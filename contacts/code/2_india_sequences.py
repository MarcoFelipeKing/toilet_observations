#!/usr/bin/env python
# coding: utf-8

# This notebook demonstrates how to simulate hand contamination for a different toilet setting scenario
# (e.g., a public toilet setting in India), where we only have a rough order of contacts
# rather than observed data. We will:
# - Define a set of base sequences for each scenario (Urination/Defecation in Women’s toilet,
#   Defecation in Men’s toilet, Urinations in Men’s toilet, and Menstrual hygiene management).
# - Add some noise and variability to the sequences (e.g., randomly inserting a "Personal" contact,
#   or slightly rearranging one or two steps).
# - Use the existing model's `simulate_contamination` method to compute contamination.
# - Save the output in a similar format as before, so we can compare results against the original predictions.

import pandas as pd
import numpy as np
import random
import math
import os

from gpt_pro_model import EnhancedToiletModelWithValidation

# Ensure output directory
os.makedirs("india_scenario_outputs", exist_ok=True)

##############################################
# Define base sequences for the Indian scenario
##############################################

# We have different activities and toilet types scenarios. According to the user:
# For Urinations & Defecation in Women's toilet AND Defecation in Men's toilet, the sequence is:
base_sequence_women_ur_def_men_def = [
    "Personal",#"Lota",
    "CubicleIN",#"External cubicle door surface",
    "Unlock",#"Internal cubicle door surface",
    "Unlock",#"Door lock",
    "Personal",#"Clothing",
    "Personal",#"Phone",
    "Personal",#"Lota",
    "Personal",#"Clothing",
    "Personal",#"Phone",
    "Personal",#"Lota",
    "Hygiene",
    "Personal",#"Clothing",
    "Personal",#"Phone",
    "Personal",#"Lota",
    "Unlock",#"Door lock",
    "CubicleOUT",
    "Exit"#"Internal cubicle door surface"
]

# For Urinations in men's toilet:
base_sequence_men_ur = [
    "Unlock",#"External cubicle door surface",
    "CubicleIN",#"Internal cubicle door surface",
    "CubicleIN",
    "Personal",#"Clothing",
    "Personal",#"Phone",
    "Personal",#"Clothing",
    "Unlock",#"Door lock",
    "CubicleOUT",
    "Exit"#"Internal cubicle door surface"
]

# For Menstrual hygiene management:
base_sequence_mhm = [
    "Personal",#"Lota",
    "CubicleIN",#"External cubicle door surface",
    "Unlock",
    "Unlock",
    "Personal",#"Clothing",
    "MHM",
    "Personal",#"Phone",
    "Personal",#"Lota",
    "MHM",
    "Personal",#"Clothing",
    "Personal",#"Phone",
    "Personal",#"Lota",
    "Hygiene",
    "MHM",
    "Personal",#"Clothing",
    "Personal",#"Phone",
    "Personal",#"Lota",
    "Door lock",
    "Hygiene",
    "Exit",#"Internal cubicle door surface"
]

# We assume the following mapping:
# - "Women", "Urination" -> use the women_ur_def_men_def sequence (since mentioned: Urinations & Defecation in Women's)
# - "Women", "Defecation" -> same as above
# - "Men", "Defecation" -> same as above (since it said defecation in men's toilet uses the same long sequence)
# - "Men", "Urination" -> men_ur sequence (urinations in men's toilet)
# - "Women", "MHM" -> mhm sequence
# - "Men", "MHM" -> Not possible scenario according to original instructions, skip
# - "Gender neutral" -> Not mentioned explicitly, let's skip this scenario or assume no scenario?

# Let's define a scenario dictionary:
scenario_sequences = {
    ("Women", "Urination"): base_sequence_women_ur_def_men_def,
    ("Women", "Defecation"): base_sequence_women_ur_def_men_def,
    ("Men", "Defecation"): base_sequence_women_ur_def_men_def,
    ("Men", "Urination"): base_sequence_men_ur,
    ("Women", "MHM"): base_sequence_mhm
}

# We won't generate for "Gender neutral" or Men MHM as not specified.

# Add noise and variability:
# Let's define a function that takes a base sequence and with some probability
# inserts a "Personal" contact or slightly rearranges one contact.
def add_noise_to_sequence(base_seq):
    seq = base_seq[:]
    # With a small probability, insert a "Personal" contact randomly in the sequence
    if random.random() < 0.3:  # 30% chance to insert a personal interruption
        insert_pos = random.randint(0, len(seq))
        seq.insert(insert_pos, "Personal")
    # With a small probability, swap two adjacent steps (not involving HANDWASHING)
    if len(seq) > 2 and random.random() < 0.2:
        idx = random.randint(0, len(seq)-2)
        # Avoid swapping HANDWASHING step
        if "HANDWASHING" not in (seq[idx], seq[idx+1]):
            seq[idx], seq[idx+1] = seq[idx+1], seq[idx]

    return seq

# We'll generate about 30 sequences for each scenario and simulate contamination
model = EnhancedToiletModelWithValidation("data/clean_contact_data.csv")

activities_india = ["Urination", "Defecation", "MHM"]
toilet_types_india = ["Men", "Women"]  # We'll skip "Gender neutral" for now since scenario not described

all_sequences_india = []
all_metadata_india = []
all_contaminations_india = []

participant_id = 0

for tt in toilet_types_india:
    # Determine activities
    if tt == "Men":
        possible_activities = ["Urination", "Defecation"] # from given scenario instructions
    else:
        possible_activities = ["Urination", "Defecation", "MHM"]  # from scenario instructions
    
    for act in possible_activities:
        if (tt, act) not in scenario_sequences:
            continue
        base_seq = scenario_sequences[(tt, act)]
        for i in range(30):
            participant_id += 1
            noisy_seq = add_noise_to_sequence(base_seq)
            # We don't have a Markov chain for these, we directly simulate contamination
            # We'll define a mock metadata
            meta = {
                "activity": act,
                "toilet_type": tt,
                "hand_hygiene_compliant": True, # assume always true for now
                "ParticipantID": participant_id
            }
            contamination = model.simulate_contamination(noisy_seq)
            all_sequences_india.append(noisy_seq)
            all_metadata_india.append(meta)
            all_contaminations_india.append((act, tt, contamination, participant_id, noisy_seq))

# Create a similar CSV with contamination records as before
contamination_records_india = []
for (act, tt, cont, pid, seq) in all_contaminations_india:
    hand_series = cont["hand_time_series"]  # [(LH, RH), ...]
    surface_series = cont["surface_time_series"]  # [ {surface: conc, ...}, ...]
    # Each index i corresponds to the i-th contact event in seq
    for idx, (lh, rh) in enumerate(hand_series):
        contacted_surface = seq[idx]
        if contacted_surface in surface_series[idx]:
            surface_conc = surface_series[idx][contacted_surface]
        else:
            surface_conc = math.nan
        
        contamination_records_india.append({
            "ParticipantID": pid,
            "Activity": act,
            "ToiletType": tt,
            "ContactIndex": idx,
            "LeftHandConc": lh,
            "RightHandConc": rh,
            "SurfaceContacted": contacted_surface,
            "SurfaceConc": surface_conc
        })

df_contamination_india = pd.DataFrame(contamination_records_india)

# Save this DataFrame
df_contamination_india.to_csv("india_scenario_outputs/hand_contamination_per_participant_india.csv", index=False)

# (Optionally produce some summary stats or plots here as well)
print("Generated and saved India scenario hand contamination data in 'india_scenario_outputs/hand_contamination_per_participant_india.csv'.")