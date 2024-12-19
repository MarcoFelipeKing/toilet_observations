# analysis.py
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from gpt_pro_model import EnhancedToiletModelWithValidation
import numpy as np
import networkx as nx
import os
import math

# Ensure output directories exist
os.makedirs("scenario_transition_matrices", exist_ok=True)

model = EnhancedToiletModelWithValidation("../data/clean_contact_data.csv")

activities = ["Urination", "Defecation", "MHM"]
toilet_types = ["Men", "Women", "Gender neutral"]

all_sequences = []
all_metadata = []
all_contaminations = []

participant_id = 0  # We'll assign a unique ID to each generated participant (sequence)

for tt in toilet_types:
    # If men, exclude MHM from possible activities
    if tt == "Men":
        possible_activities = ["Urination", "Defecation"]
    else:
        possible_activities = activities
    
    for act in possible_activities:
        for i in range(30):
            participant_id += 1
            seq, hand_pattern, meta = model.generate_sequence(act, tt)
            contamination = model.simulate_contamination(seq)
            # Store results
            all_sequences.append(seq)
            meta["ParticipantID"] = participant_id
            all_metadata.append(meta)
            all_contaminations.append((act, tt, contamination, participant_id, seq))

# Validation
validation_results = model.validate_sequences(n_samples=100)
print("Validation Results:")
print(validation_results)

# Compute descriptive stats for lengths
sequences = model._extract_sequences()
observed_lengths = [len(s) for _, s, _, _ in sequences]

generated_lengths = []
for i in range(1000):
    chosen_tt = np.random.choice(toilet_types)
    if chosen_tt == "Men":
        chosen_act = np.random.choice(["Urination", "Defecation"])
    else:
        chosen_act = np.random.choice(activities)
    seq, _, _ = model.generate_sequence(chosen_act, chosen_tt)
    generated_lengths.append(len(seq))

obs_mean = np.mean(observed_lengths)
obs_median = np.median(observed_lengths)
obs_std = np.std(observed_lengths)

gen_mean = np.mean(generated_lengths)
gen_median = np.median(generated_lengths)
gen_std = np.std(generated_lengths)

print("Observed Length Statistics:")
print(f"Mean: {obs_mean:.2f}, Median: {obs_median:.2f}, Std: {obs_std:.2f}")

print("Generated Length Statistics:")
print(f"Mean: {gen_mean:.2f}, Median: {gen_median:.2f}, Std: {gen_std:.2f}")

length_diff_mean = gen_mean - obs_mean
print(f"Difference in Mean Length (Generated - Observed): {length_diff_mean:.2f}")

# ---- Save scenario-based transition matrices to CSV ----
for ttype in toilet_types:
    for act in activities:
        scenario_key = (ttype, act)
        if scenario_key not in model.markov_chains:
            continue
        
        scenario_chain = model.markov_chains[scenario_key]
        # Extract states
        unique_states = set()
        for prev in scenario_chain:
            for nxt in scenario_chain[prev]:
                unique_states.add(nxt)
            unique_states.update(prev)
        
        unique_states = list(unique_states)
        state_index = {s: i for i, s in enumerate(unique_states)}
        
        # Build matrix
        matrix = np.zeros((len(unique_states), len(unique_states)))
        
        counts = {}
        for (prev_states), transitions in scenario_chain.items():
            for nxt, p in transitions.items():
                current_state = prev_states[-1]
                counts[(current_state, nxt)] = counts.get((current_state, nxt), 0) + p
        
        # Normalize rows
        row_sums = {}
        for (c, n), val in counts.items():
            row_sums[c] = row_sums.get(c, 0) + val
        
        for (c, n), val in counts.items():
            if row_sums[c] > 0:
                matrix[state_index[c], state_index[n]] = val/row_sums[c]
        
        scenario_name = f"{ttype}_{act}".replace(" ", "_")
        df_mat = pd.DataFrame(matrix, index=unique_states, columns=unique_states)
        df_mat.to_csv(f"scenario_transition_matrices/{scenario_name}_transition_matrix.csv")

# ---- Create a CSV recording all contamination at each contact for each participant ----
# Structure: ParticipantID, Activity, ToiletType, ContactIndex, LeftHandConc, RightHandConc, SurfaceContacted, SurfaceConc
contamination_records = []
for (act, tt, cont, pid, seq) in all_contaminations:
    hand_series = cont["hand_time_series"]  # [(LH, RH), ...]
    surface_series = cont["surface_time_series"]  # [ {surface: conc, ...}, ...]
    # Each index i corresponds to the i-th contact event in seq
    # seq[i] is the surface contacted at step i
    # hand_series[i], surface_series[i] correspond to state after i-th contact.
    
    for idx, (lh, rh) in enumerate(hand_series):
        contacted_surface = seq[idx]
        # Check if contacted_surface is in surface_series[idx]
        # If not (like "Exit"), put NaN
        if contacted_surface in surface_series[idx]:
            surface_conc = surface_series[idx][contacted_surface]
        else:
            surface_conc = math.nan
        
        contamination_records.append({
            "ParticipantID": pid,
            "Activity": act,
            "ToiletType": tt,
            "ContactIndex": idx,
            "LeftHandConc": lh,
            "RightHandConc": rh,
            "SurfaceContacted": contacted_surface,
            "SurfaceConc": surface_conc
        })

df_contamination = pd.DataFrame(contamination_records)
df_contamination.to_csv("hand_contamination_per_participant.csv", index=False)

# ---- 3x3 Grid of Contamination vs Contact Step (First 9 Participants) ----
n_examples = 9
example_data = all_contaminations[:n_examples]

fig, axes = plt.subplots(3, 3, figsize=(15, 12))
axes = axes.flatten()

for i, (act, tt, cont, pid, seq) in enumerate(example_data):
    ax = axes[i]
    hand_series = cont["hand_time_series"]
    times = np.arange(len(hand_series))
    lh_series = [h[0] for h in hand_series]
    rh_series = [h[1] for h in hand_series]
    ax.plot(times, lh_series, label="Left Hand")
    ax.plot(times, rh_series, label="Right Hand")
    ax.set_title(f"PID:{pid}, {tt}, {act}")
    ax.set_xlabel("Contact Step")
    ax.set_ylabel("Hand Contamination (PFU/cm^2)")
    if i == 0:
        ax.legend()

plt.tight_layout()
plt.savefig("contamination_3x3_grid.png")
plt.show()

# ---- 3x3 Grid of Network Plots for the same 9 participants ----
fig, axes = plt.subplots(3, 3, figsize=(15, 12))
axes = axes.flatten()

for i, (act, tt, cont, pid, seq) in enumerate(example_data):
    ax = axes[i]
    G = nx.DiGraph()
    for j in range(len(seq)-1):
        G.add_edge(seq[j], seq[j+1])
    pos = nx.spring_layout(G, seed=42)
    nx.draw_networkx(G, pos, with_labels=True, node_color='lightblue', arrows=True, 
                     arrowstyle='->', arrowsize=12, ax=ax, font_size=8)
    ax.set_title(f"PID:{pid}, {tt}, {act}")
    ax.set_axis_off()

plt.tight_layout()
plt.savefig("sequence_network_3x3_grid.png")
plt.show()

def compare_length_distributions(model, activities, toilet_types, n_generated=1000, plot_type='density'):
    """
    Compare the observed vs generated length distributions for each (activity, toilet_type) scenario.
    
    Parameters:
    - model: EnhancedToiletModelWithValidation instance
    - activities: list of activities, e.g. ["Urination", "Defecation", "MHM"]
    - toilet_types: list of toilet types, e.g. ["Men", "Women", "Gender neutral"]
    - n_generated: number of generated sequences per scenario
    - plot_type: 'hist' for histogram or 'density' for kernel density estimate plots
    
    The function:
    - Extracts observed lengths per scenario.
    - Generates lengths for new sequences per scenario.
    - Plots both distributions for comparison.
    """
    # Extract observed sequences
    sequences = model._extract_sequences()  # returns (exp_id, surfaces, activity, toilet_type)
    # Organize observed lengths by scenario
    observed_lengths_by_scenario = {}
    for _, surf_seq, act, ttype in sequences:
        scenario = (act, ttype)
        length = len(surf_seq)
        if scenario not in observed_lengths_by_scenario:
            observed_lengths_by_scenario[scenario] = []
        observed_lengths_by_scenario[scenario].append(length)
    
    # For each scenario, generate sequences and record their lengths
    fig, axes = plt.subplots(len(toilet_types), len(activities), figsize=(15, 12))
    axes = axes.flatten()
    
    i = 0
    for ttype in toilet_types:
        # Determine which activities to consider if Men
        if ttype == "Men":
            scenario_activities = ["Urination", "Defecation"]
        else:
            scenario_activities = activities
        
        for act in scenario_activities:
            scenario = (act, ttype)
            
            # Observed lengths
            obs_lengths = observed_lengths_by_scenario.get(scenario, [])
            
            # Generate sequences and lengths
            gen_lengths = []
            for _ in range(n_generated):
                seq, _, _ = model.generate_sequence(act, ttype)
                gen_lengths.append(len(seq))
            
            ax = axes[i]
            i += 1
            
            # Plotting
            if plot_type == 'hist':
                # Plot observed and generated as overlapping histograms
                ax.hist(obs_lengths, bins=20, alpha=0.5, label='Observed', density=True)
                ax.hist(gen_lengths, bins=20, alpha=0.5, label='Generated', density=True)
            else:
                # Plot density using seaborn
                sns.kdeplot(obs_lengths, label='Observed', ax=ax, shade=True)
                sns.kdeplot(gen_lengths, label='Generated', ax=ax, shade=True)
            
            ax.set_title(f"{ttype}, {act}")
            ax.set_xlabel("Sequence Length")
            ax.set_ylabel("Density")
            ax.legend()
    
    plt.tight_layout()
    plt.savefig("length_comparison.png")
    plt.show()

compare_length_distributions(model, activities, toilet_types, n_generated=1000, plot_type='density')

# Combine Activity and ToiletType into a single scenario column
df_contamination["Scenario"] = df_contamination["Activity"] + "_" + df_contamination["ToiletType"].str.replace(" ", "_")
# Calculate final hand contamination for each participant
df_contamination["FinalHandContamination"] = df_contamination.groupby("ParticipantID")["RightHandConc"].transform("last")

# Split Scenario into Activity and ToiletType again (if you don't already have them separate)
# Assuming you already have "Activity" and "ToiletType" in df_contamination

g = sns.catplot(data=df_contamination, x="ToiletType", y="FinalHandContamination", hue="ToiletType", col="Activity", kind="violin", cut=0, sharey=False)
g.set_xticklabels(rotation=45)
g.set_axis_labels("Toilet Type", "Final Hand Contamination (RNA copies/cm^2)")
g.fig.subplots_adjust(top=0.9)
g.fig.suptitle("Final Hand Contamination by Activity and Toilet Type")
plt.savefig("final_hand_contamination_violin.png")
plt.show()

# Perform a Kruskal-Wallis test across all scenarios
# This checks if at least one scenario differs significantly from the others.
from scipy.stats import kruskal

groups = [group["FinalHandContamination"].values for _, group in df_contamination.groupby("Scenario")]
stat, p = kruskal(*groups)
print("Kruskal-Wallis test across scenarios:")
print("Statistic:", stat)
print("p-value:", p)