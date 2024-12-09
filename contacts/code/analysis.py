import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from gpt_pro_model import EnhancedToiletModelWithValidation
import numpy as np
import networkx as nx

# Initialize model with provided data
model = EnhancedToiletModelWithValidation("../data/clean_contact_data.csv")

# Generate synthetic data: 
# 30 sequences per activity/toilet combination
activities = ["Urination", "Defecation", "MHM"]
toilet_types = ["Men", "Women", "Gender neutral"]

all_sequences = []
all_metadata = []
all_contaminations = []

for act in activities:
    for tt in toilet_types:
        for i in range(30):
            seq, hand_pattern, meta = model.generate_sequence(act, tt)
            contamination = model.simulate_contamination(
                seq,
                initial_surface_contamination=100,
                transfer_efficiency=0.1,
                surface_contact_fraction=0.1
            )
            all_sequences.append(seq)
            all_metadata.append(meta)
            all_contaminations.append((act, tt, contamination))

# Validation
validation_results = model.validate_sequences(n_samples=100)
print("Validation Results:")
print(validation_results)

# Extract final hand contamination across sequences for visualization
final_contam_data = []
for (act, tt, cont) in all_contaminations:
    lh, rh = cont["final_hands"]
    final_load = (lh+rh)/2.0
    final_contam_data.append({"Activity": act, "ToiletType": tt, "FinalHandContamination": final_load})

final_df = pd.DataFrame(final_contam_data)

# Violin Plot comparing final hand contamination across toilet types and activities
plt.figure(figsize=(12,6))
sns.violinplot(data=final_df, x="ToiletType", y="FinalHandContamination", hue="Activity")
plt.title("Final Hand Contamination by Toilet Type and Activity")
plt.ylabel("Final Hand Contamination (arbitrary units)")
plt.xlabel("Toilet Type")
plt.legend(title="Activity")
plt.tight_layout()
plt.show()

# Network visualization of contact patterns (example)
# Build a graph of transitions from one sequence
example_seq = all_sequences[0]
G = nx.DiGraph()
for i in range(len(example_seq)-1):
    G.add_edge(example_seq[i], example_seq[i+1])
pos = nx.spring_layout(G)
plt.figure(figsize=(8,6))
nx.draw_networkx(G, pos, with_labels=True, node_color='lightblue', arrows=True, arrowstyle='->', arrowsize=12)
plt.title("Example Contact Pattern Network")
plt.show()
