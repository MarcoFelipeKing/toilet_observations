import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import Embedding, LSTM, Dense, Input, LayerNormalization, Dropout, MultiHeadAttention
from tensorflow.keras.optimizers import Adam
from collections import Counter, defaultdict
import matplotlib.pyplot as plt
import seaborn as sns

# Assume we already have `model` as an instance of EnhancedToiletModelWithValidation:
from gpt_pro_model import EnhancedToiletModelWithValidation
model = EnhancedToiletModelWithValidation("../data/clean_contact_data.csv")

scenario_chains = model.markov_chains  # {(toilet_type, activity): { (prev_s1, prev_s2): {next_s: prob, ...}, ... }}

# Parameters
N_SEQUENCES_PER_SCENARIO = 500  # number of sequences per scenario for training
MAX_LENGTH = 50

available_scenarios = list(scenario_chains.keys())
print("Available scenarios:", available_scenarios)

all_states = model.surface_categories
state_to_idx = {s: i for i, s in enumerate(all_states)}
idx_to_state = {i: s for s, i in state_to_idx.items()}
vocab_size = len(all_states)

def generate_sequences_from_chain(chain, n_sequences=100, max_length=50):
    sequences = []
    initial_pairs = [pair for pair in chain.keys() if pair[0] == "Entry"]
    if not initial_pairs:
        initial_pairs = list(chain.keys())
    for _ in range(n_sequences):
        prev_states = list(initial_pairs[np.random.randint(len(initial_pairs))])
        seq = prev_states[:]
        while len(seq) < max_length:
            pair = (seq[-2], seq[-1])
            if pair not in chain:
                seq.append("Exit")
                break
            next_states_prob = chain[pair]
            next_states = list(next_states_prob.keys())
            probs = list(next_states_prob.values())
            next_state = np.random.choice(next_states, p=probs)
            seq.append(next_state)
            if next_state == "Exit":
                break
        if seq[-1] != "Exit":
            seq.append("Exit")
        sequences.append(seq)
    return sequences

all_generated_sequences = []
for (tt, act) in available_scenarios:
    print(f"Generating sequences for scenario: {(tt, act)}")
    ch = scenario_chains[(tt, act)]
    seqs = generate_sequences_from_chain(ch, n_sequences=N_SEQUENCES_PER_SCENARIO, max_length=MAX_LENGTH)
    for seq in seqs:
        all_generated_sequences.append((tt, act, seq))

encoded_sequences = []
for (tt, act, seq) in all_generated_sequences:
    encoded = [state_to_idx[s] for s in seq if s in state_to_idx]
    encoded_sequences.append(encoded)

# Prepare training data: given last 2 states, predict next state
X_train = []
Y_train = []
for enc_seq in encoded_sequences:
    for i in range(2, len(enc_seq)):
        X_train.append([enc_seq[i-2], enc_seq[i-1]])
        Y_train.append(enc_seq[i])

X_train = np.array(X_train, dtype='int32')
Y_train = np.array(Y_train, dtype='int32')

print("Training data shape:", X_train.shape, Y_train.shape)

########################################
# Original LSTM-based Model
########################################
embedding_dim = 16
hidden_dim = 32

lstm_model = Sequential()
lstm_model.add(Embedding(input_dim=vocab_size, output_dim=embedding_dim, input_length=2))
lstm_model.add(LSTM(hidden_dim))
lstm_model.add(Dense(vocab_size, activation='softmax'))

lstm_model.compile(loss='sparse_categorical_crossentropy', optimizer=Adam(0.001), metrics=['accuracy'])
lstm_model.summary()

lstm_model.fit(X_train, Y_train, epochs=5, batch_size=64, validation_split=0.1)

def generate_nn_sequences(model_nn, state_to_idx, idx_to_state, start_state="Entry", n_sequences=100, max_length=50):
    if start_state not in state_to_idx:
        raise ValueError(f"Start state {start_state} not in state_to_idx.")
    initial_pair = ("Entry", "Entry")
    nn_sequences = []
    for _ in range(n_sequences):
        seq = list(initial_pair)
        while len(seq) < max_length:
            prev_s1_idx = state_to_idx[seq[-2]]
            prev_s2_idx = state_to_idx[seq[-1]]
            x_input = np.array([[prev_s1_idx, prev_s2_idx]])
            preds = model_nn.predict(x_input, verbose=0)[0]
            next_idx = np.random.choice(range(vocab_size), p=preds)
            next_state = idx_to_state[next_idx]
            seq.append(next_state)
            if next_state == "Exit":
                break
        if seq[-1] != "Exit":
            seq.append("Exit")
        nn_sequences.append(seq)
    return nn_sequences

lstm_sequences = generate_nn_sequences(lstm_model, state_to_idx, idx_to_state, start_state="Entry", n_sequences=100, max_length=50)

# Extract only sequences from Markov data
markov_only_seqs = [seq for (tt, act, seq) in all_generated_sequences]

########################################
# Improved Transformer-based Model
########################################

# We'll define a small Transformer encoder for next-state prediction:
class PositionalEmbedding(tf.keras.layers.Layer):
    def __init__(self, max_len, embed_dim):
        super().__init__()
        position = tf.range(max_len)[:, tf.newaxis]
        div_term = tf.exp(tf.cast(tf.range(0, embed_dim, 2), tf.float32) * (-tf.math.log(10000.0) / float(embed_dim)))
        sine = tf.sin(tf.cast(position, tf.float32) * div_term)
        cos = tf.cos(tf.cast(position, tf.float32) * div_term)
        sine_cos = tf.reshape(tf.stack([sine, cos], axis=2), [max_len, embed_dim])
        self.pos_encoding = sine_cos[tf.newaxis, ...]
    
    def call(self, x):
        seq_len = tf.shape(x)[1]
        return self.pos_encoding[:, :seq_len, :]

def transformer_encoder(inputs, embed_dim, num_heads, ff_dim, dropout_rate=0.1):
    attn_output = MultiHeadAttention(num_heads=num_heads, key_dim=embed_dim)(inputs, inputs)
    attn_output = Dropout(dropout_rate)(attn_output)
    out1 = LayerNormalization(epsilon=1e-6)(inputs + attn_output)
    ffn = tf.keras.Sequential([
        tf.keras.layers.Dense(ff_dim, activation='relu'),
        tf.keras.layers.Dense(embed_dim),
    ])
    ffn_output = ffn(out1)
    ffn_output = Dropout(dropout_rate)(ffn_output)
    out2 = LayerNormalization(epsilon=1e-6)(out1 + ffn_output)
    return out2

# We'll try a longer input context. For simplicity, still use length=2 for direct comparison.
# But ideally, you'd increase input_length to a larger context window.
input_length = 2
transformer_embed_dim = 64
transformer_heads = 4
transformer_ff_dim = 128
num_transformer_layers = 2
max_seq_length = 50 # same as MAX_LENGTH used above

input_seq = tf.keras.Input(shape=(input_length,), dtype="int32")
x = Embedding(vocab_size, transformer_embed_dim)(input_seq)
x += PositionalEmbedding(max_seq_length, transformer_embed_dim)(input_seq)

for _ in range(num_transformer_layers):
    x = transformer_encoder(x, transformer_embed_dim, transformer_heads, transformer_ff_dim, dropout_rate=0.1)

x = tf.keras.layers.Dense(vocab_size, activation='softmax')(x[:, -1, :]) # predict next state from last position
transformer_model = tf.keras.Model(input_seq, x)
transformer_model.compile(loss='sparse_categorical_crossentropy', optimizer=Adam(1e-3), metrics=['accuracy'])
transformer_model.summary()

transformer_model.fit(X_train, Y_train, epochs=5, batch_size=64, validation_split=0.1)

transformer_sequences = generate_nn_sequences(transformer_model, state_to_idx, idx_to_state, start_state="Entry", n_sequences=100, max_length=50)

########################################
# Visualization and Comparison
########################################

def get_transitions(sequences):
    transitions = []
    for seq in sequences:
        for i in range(len(seq)-1):
            transitions.append((seq[i], seq[i+1]))
    return transitions

# Length Distributions
markov_lengths = [len(seq) for seq in markov_only_seqs]
lstm_lengths = [len(seq) for seq in lstm_sequences]
transformer_lengths = [len(seq) for seq in transformer_sequences]

plt.figure(figsize=(10,6))
sns.kdeplot(markov_lengths, label="Markov Chain", shade=True)
sns.kdeplot(lstm_lengths, label="LSTM NN", shade=True)
sns.kdeplot(transformer_lengths, label="Transformer NN", shade=True)
plt.title("Sequence Length Distribution")
plt.xlabel("Sequence Length")
plt.ylabel("Density")
plt.legend()
plt.tight_layout()
plt.show()

# State Frequency
markov_state_counts = Counter(s for seq in markov_only_seqs for s in seq)
lstm_state_counts = Counter(s for seq in lstm_sequences for s in seq)
transformer_state_counts = Counter(s for seq in transformer_sequences for s in seq)

all_states_union = list(set(markov_state_counts.keys()).union(lstm_state_counts.keys(), transformer_state_counts.keys()))
markov_freq = [markov_state_counts.get(s,0) for s in all_states_union]
lstm_freq = [lstm_state_counts.get(s,0) for s in all_states_union]
transformer_freq = [transformer_state_counts.get(s,0) for s in all_states_union]

markov_total = sum(markov_freq)
lstm_total = sum(lstm_freq)
transformer_total = sum(transformer_freq)

markov_norm = [c/markov_total for c in markov_freq]
lstm_norm = [c/lstm_total for c in lstm_freq]
transformer_norm = [c/transformer_total for c in transformer_freq]

x = np.arange(len(all_states_union))
width = 0.25

plt.figure(figsize=(12,6))
plt.bar(x - width, markov_norm, width=width, label="Markov Chain")
plt.bar(x, lstm_norm, width=width, label="LSTM NN")
plt.bar(x + width, transformer_norm, width=width, label="Transformer NN")
plt.xticks(x, all_states_union, rotation=45, ha='right')
plt.ylabel("Frequency")
plt.title("State Frequency Comparison")
plt.legend()
plt.tight_layout()
plt.show()

# Transition Patterns
markov_transitions = get_transitions(markov_only_seqs)
lstm_transitions = get_transitions(lstm_sequences)
transformer_transitions = get_transitions(transformer_sequences)

markov_trans_counts = Counter(markov_transitions)
lstm_trans_counts = Counter(lstm_transitions)
transformer_trans_counts = Counter(transformer_transitions)

all_pairs = list(set(markov_trans_counts.keys()).union(lstm_trans_counts.keys(), transformer_trans_counts.keys()))
states_set = list(set(s for s1,s2 in all_pairs for s in (s1,s2)))
states_set = sorted(states_set)
state_index = {s:i for i,s in enumerate(states_set)}

def build_matrix(trans_counts):
    total_trans = sum(trans_counts.values())
    mat = np.zeros((len(states_set), len(states_set)))
    for (s1, s2), c in trans_counts.items():
        mat[state_index[s1], state_index[s2]] = c / total_trans
    return mat

markov_matrix = build_matrix(markov_trans_counts)
lstm_matrix = build_matrix(lstm_trans_counts)
transformer_matrix = build_matrix(transformer_trans_counts)

fig, axes = plt.subplots(1,3, figsize=(24,6))
sns.heatmap(markov_matrix, xticklabels=states_set, yticklabels=states_set, ax=axes[0], cmap="Blues")
axes[0].set_title("Markov Chain Transitions")
axes[0].set_xlabel("Next State")
axes[0].set_ylabel("Previous State")

sns.heatmap(lstm_matrix, xticklabels=states_set, yticklabels=states_set, ax=axes[1], cmap="Greens")
axes[1].set_title("LSTM NN Transitions")
axes[1].set_xlabel("Next State")

sns.heatmap(transformer_matrix, xticklabels=states_set, yticklabels=states_set, ax=axes[2], cmap="Reds")
axes[2].set_title("Transformer NN Transitions")
axes[2].set_xlabel("Next State")

plt.tight_layout()
plt.show()

#####
# Metrics
#####

def markov_log_likelihood(chain, encoded_seq):
    """
    Compute the log-likelihood of an integer-encoded sequence under a second-order Markov chain.
    chain : dict of dict
      chain[(s_{k-2}, s_{k-1})][s_k] = probability
    encoded_seq : list of integers representing states
    """
    log_lik = 0.0
    # For convenience, ensure we have at least two states
    if len(encoded_seq) < 2:
        return 0.0  # trivial or handle differently
    
    for i in range(2, len(encoded_seq)):
        prev_pair = (encoded_seq[i-2], encoded_seq[i-1])
        next_s = encoded_seq[i]
        # Check if chain has prob
        if prev_pair in chain and next_s in chain[prev_pair]:
            prob = chain[prev_pair][next_s]
        else:
            # If not found, assign small probability
            prob = 1e-12
        log_lik += np.log(prob)
    return log_lik

def compute_markov_perplexity(chain, test_sequences):
    """
    Given a set of test sequences (encoded), compute average perplexity.
    """
    total_log_lik = 0.0
    total_length = 0
    for seq in test_sequences:
        ll = markov_log_likelihood(chain, seq)
        total_log_lik += ll
        total_length += len(seq) - 2  # or len(seq), but typically we skip first two
    # average negative log-likelihood
    avg_nll = - total_log_lik / max(1, total_length)
    perplexity = np.exp(avg_nll)
    return perplexity

def nn_log_likelihood(model_nn, encoded_seq, vocab_size):
    """
    Compute log-likelihood of a sequence under a 2-state context neural network.
    model_nn: Keras model
    encoded_seq: list of integers (states)
    vocab_size: number of states
    """
    log_lik = 0.0
    if len(encoded_seq) < 2:
        return 0.0
    
    for i in range(2, len(encoded_seq)):
        prev_s1 = encoded_seq[i-2]
        prev_s2 = encoded_seq[i-1]
        x_input = np.array([[prev_s1, prev_s2]])  # shape (1,2)
        preds = model_nn.predict(x_input, verbose=0)[0]  # shape (vocab_size,)
        
        prob_next = preds[encoded_seq[i]]
        if prob_next < 1e-12:
            prob_next = 1e-12
        log_lik += np.log(prob_next)
    return log_lik

def compute_nn_perplexity(model_nn, test_sequences, vocab_size):
    total_log_lik = 0.0
    total_length = 0
    for seq in test_sequences:
        ll = nn_log_likelihood(model_nn, seq, vocab_size)
        total_log_lik += ll
        total_length += len(seq) - 2
    avg_nll = - total_log_lik / max(1, total_length)
    return np.exp(avg_nll)

# Suppose we have test_sequences_markov (real data) integer-encoded
markov_perp = compute_markov_perplexity(scenario_chains[(tt, act)], all_generated_sequences)
nn_LSTM_perp = compute_nn_perplexity(lstm_model, lstm_sequences, vocab_size)
nn_T_perp = compute_nn_perplexity(transformer_model, transformer_sequences, vocab_size)
print("Markov Perplexity:", markov_perp)
print("LSTM Perplexity:", nn_LSTM_perp )
print("Transformer Perplexity:", nn_LSTM_perp )