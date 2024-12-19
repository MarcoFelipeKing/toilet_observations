# gpt_pro_model.py
import pandas as pd
import numpy as np
import random
from collections import defaultdict, Counter
from scipy.stats import beta, lognorm, bernoulli, ks_2samp, chi2_contingency, gamma, norm
import networkx as nx
import matplotlib.pyplot as plt
import seaborn as sns

class EnhancedToiletModelWithValidation:
    def __init__(self, data_file):
        """
        Initialize model with observed data.
        """
        self.data_file = data_file
        self.data = pd.read_csv(data_file, sep=",")

        self._check_data_integrity()
        
        # Define states: Add "Urinal" for men's toilets
        self.surface_categories = ["Entry", "CubicleIN", "Cubicle", "Unlock", "CubicleOUT", 
                                   "Hygiene", "Personal", "MHM", "Exit", "Urinal"]
        
        self.activities = ["Urination", "Defecation", "MHM"]
        self.toilet_types = ["Men", "Women", "Gender neutral"]
        
        # Build scenario-specific Markov chains:
        self.markov_chains = self._build_scenario_markov_chains(order=2)
        
        # Parameters
        self.hand_hygiene_compliance_prob = 0.45 #From literature (men 31%, women up to 60%)
        
        # Transfer efficiency Beta parameters
        self.alpha_lambda = 2.0
        self.beta_lambda = 5.0
        
        # Gamma distribution for contact area
        self.k_area = 2.0
        self.theta_area = 2.0
        
        # Fraction available for transfer
        #self.theta = 0.1
        
        # Pathogen decay rate
        self.default_pathogen_decay_rate = 0.0116 # if you assume a half-life of ~1 hour and each step ~1 min, the per-step decay would be about ~1- (0.5^(1/60)) ≈ 0.0116
        
        # Hands start clean
        self.initial_left_hand_contamination = 0.0
        self.initial_right_hand_contamination = 0.0
        
        # Amoah paper surface contamination distributions:
        self.surface_contamination_params = {
            "Cubicle": ("Toilet seat", 132.9, 39.8),
            "Hygiene": ("Tap", 30.0, 5.0),
            "CubicleIN": ("Cubicle door lock", 60.1, 14.5),
            "CubicleOUT": ("Cubicle door lock", 60.1, 14.5),
            "Unlock": ("Cubicle door lock", 60.1, 14.5),
            "Entry": ("Low contamination", 1.0, 0.5),
            "Personal": ("Low contamination", 1.0, 0.5),
            "MHM": ("Low contamination", 1.0, 0.5),
            "Exit": ("Low contamination", 1.0, 0.5),
            # Urinal: If present in data, assume similar low contamination or estimate if data available
            "Urinal": ("Low contamination", 5.0, 2.0)
        }

    def _check_data_integrity(self):
        # Optionally check if each experiment starts at Entry and ends at Exit
        pass
        
    def _extract_sequences(self):
        sequences = []
        for exp_id, group in self.data.groupby("ExperimentID"):
            seq = group.sort_values(by="ID")
            surfaces = seq["SurfaceCategories"].tolist()
            activity = seq["Activity"].iloc[0]
            toilet_type = seq["Toilet_type"].iloc[0]
            # Only count until Exit if needed:
            # If your data always has Exit at end, good. If not, ensure:
            if "Exit" in surfaces:
                # Truncate sequence at first Exit occurrence
                exit_idx = surfaces.index("Exit")
                surfaces = surfaces[:exit_idx] 
            sequences.append((exp_id, surfaces, activity, toilet_type))
        return sequences

    def _build_scenario_markov_chains(self, order=2):
        """
        Build a separate Markov chain for each (toilet_type, activity) scenario.
        """
        sequences = self._extract_sequences()
        
        # Dictionary: (toilet_type, activity) -> transition_probs
        scenario_chains = {}
        
        # Loop over each scenario
        for ttype in self.toilet_types:
            for act in self.activities:
                # Filter sequences for this scenario
                scenario_seqs = [s for (_, s, a, t) in sequences if a == act and t == ttype]
                
                # If no sequences for this scenario, skip
                if len(scenario_seqs) == 0:
                    continue
                
                # Build chain for these sequences
                transition_counts = defaultdict(Counter)
                for surf_seq in scenario_seqs:
                    padded_seq = ["Entry"] + surf_seq + ["Exit"]
                    for i in range(len(padded_seq) - order):
                        prev_states = tuple(padded_seq[i:i+order])
                        next_state = padded_seq[i+order]
                        transition_counts[prev_states][next_state] += 1
                
                transition_probs = {}
                for prev, counts in transition_counts.items():
                    total = sum(counts.values())
                    transition_probs[prev] = {k: v/total for k, v in counts.items()}
                
                scenario_chains[(ttype, act)] = transition_probs
        
        return scenario_chains

    def generate_sequence(self, activity, toilet_type, max_length=50):
        """
        Generate a synthetic sequence with scenario-specific chain:
        - If Men and MHM, switch activity since Men shouldn't do MHM.
        - If no chain for a scenario, return a minimal sequence (Entry->Exit).
        - Use scenario-specific chain to pick transitions.
        - Cubicle logic and personal interruptions remain.
        """
        
        if toilet_type == "Men" and activity == "MHM":
            activity = np.random.choice(["Urination", "Defecation"])
        
        chain = self.markov_chains.get((toilet_type, activity), None)
        if chain is None:
            # No data for this scenario, return a simple minimal sequence
            sequence = ["Entry", "Exit"]
            hand_pattern = np.random.choice(["Left", "Right", "Both"], size=len(sequence))
            metadata = {
                "activity": activity,
                "toilet_type": toilet_type,
                "hand_hygiene_compliant": bool(bernoulli.rvs(self.hand_hygiene_compliance_prob))
            }
            return sequence, hand_pattern, metadata
        
        sequence = ["Entry"]
        
        while len(sequence) < max_length:
            if sequence[-1] == "Exit":
                break
            
            prev_states = tuple(sequence[-2:]) if len(sequence) > 1 else ("Entry", sequence[-1])
            if prev_states not in chain:
                # No known transitions from here, append Exit
                sequence.append("Exit")
                break
            next_states_prob = chain[prev_states]
            next_state = np.random.choice(list(next_states_prob.keys()), p=list(next_states_prob.values()))
            
            # Insert personal interruptions (if not about to exit)
            #if next_state != "Exit" and np.random.rand() < 0.41:
            #    sequence.append("Personal")
            #    if len(sequence) >= max_length:
            #        sequence.append("Exit")
            #        break
            
            # Cubicle logic
            if sequence[-1] == "Cubicle" and next_state in ["CubicleOUT", "Exit"]:
                sequence.append("Unlock")
                if next_state == "Exit":
                    sequence.append("CubicleOUT")
                    sequence.append("Exit")
                    break
                else:
                    sequence.append("CubicleOUT")
            else:
                sequence.append(next_state)
            
            if sequence[-1] == "Exit":
                break
        
        if sequence[-1] != "Exit":
            sequence.append("Exit")
        
        hand_pattern = np.random.choice(["Left", "Right", "Both"], size=len(sequence),p=[0.319, 0.445, 0.236]) #Here we can infer from data
        '''
         hand      n     prop
        <chr> <int>    <dbl>
        1 Both    543 0.235   
        2 Left    738 0.319   
        3 Right  1027 0.445   '''
        metadata = {
            "activity": activity,
            "toilet_type": toilet_type,
            "hand_hygiene_compliant": bool(bernoulli.rvs(self.hand_hygiene_compliance_prob))
        }
        
        return sequence, hand_pattern, metadata

    def _initialize_surfaces(self):
        surfaces = {}
        for s in self.surface_categories:
            if s == "Exit":
                continue
            surf_name, mean_val, std_val = self.surface_contamination_params[s]
            val = np.random.normal(loc=mean_val, scale=std_val)
            val = max(val, 0.0)
            surfaces[s] = val
        return surfaces
    
    def simulate_contamination(self, sequence, pathogen_decay_rate=None):
        if pathogen_decay_rate is None:
            pathogen_decay_rate = self.default_pathogen_decay_rate
        
        surfaces = self._initialize_surfaces()
        
        left_hand_contamination = self.initial_left_hand_contamination
        right_hand_contamination = self.initial_right_hand_contamination
        
        hand_contamination_over_time = []
        surface_contamination_over_time = []
        
        for idx, surf in enumerate(sequence):
            # Decay pathogen on surfaces
            for k in surfaces:
                surfaces[k] *= (1 - pathogen_decay_rate)
            
            chosen_hand = np.random.choice(["Left", "Right", "Both"])
            
            if surf in surfaces:
                C_s = surfaces[surf]

                TOTAL_HAND_AREA = 150.0
                lam = beta.rvs(self.alpha_lambda, self.beta_lambda)  # transfer efficiency
                A = gamma.rvs(self.k_area, scale=self.theta_area)    # contact area

                Delta_PFU = 0.0

                if chosen_hand == "Left":
                    Delta_PFU = (C_s - left_hand_contamination) * A * lam
                    new_left = (left_hand_contamination * TOTAL_HAND_AREA + Delta_PFU) / TOTAL_HAND_AREA
                    left_hand_contamination = max(new_left, 0.0)

                elif chosen_hand == "Right":
                    Delta_PFU = (C_s - right_hand_contamination) * A * lam
                    new_right = (right_hand_contamination * TOTAL_HAND_AREA + Delta_PFU) / TOTAL_HAND_AREA
                    right_hand_contamination = max(new_right, 0.0)

                else:
                    # Both hands scenario:
                    Delta_PFU_left = (C_s - left_hand_contamination) * (A/2) * lam
                    new_left = (left_hand_contamination * TOTAL_HAND_AREA + Delta_PFU_left) / TOTAL_HAND_AREA
                    left_hand_contamination = max(new_left, 0.0)

                    Delta_PFU_right = (C_s - right_hand_contamination) * (A/2) * lam
                    new_right = (right_hand_contamination * TOTAL_HAND_AREA + Delta_PFU_right) / TOTAL_HAND_AREA
                    right_hand_contamination = max(new_right, 0.0)

                    Delta_PFU = Delta_PFU_left + Delta_PFU_right

                surfaces[surf] = max(C_s - (Delta_PFU / A), 0.0)
            else:
                # If surf is not in surfaces, do nothing
                pass

            # Hand hygiene
            if surf == "Hygiene":
                if bernoulli.rvs(self.hand_hygiene_compliance_prob):
                    reduction_factor = lognorm(s=0.5, scale=np.exp(-1)).rvs()
                    left_hand_contamination *= reduction_factor
                    right_hand_contamination *= reduction_factor
            
            hand_contamination_over_time.append((left_hand_contamination, right_hand_contamination))
            surface_contamination_over_time.append(surfaces.copy())
        
        return {
            "final_hands": (left_hand_contamination, right_hand_contamination),
            "hand_time_series": hand_contamination_over_time,
            "surface_time_series": surface_contamination_over_time
        }
    
    def validate_sequences(self, n_samples=1000):
        # Validation now relies on scenario-based generation
        sequences = self._extract_sequences()
        observed_lengths = [len(s) for _, s, _, _ in sequences]
        
        generated_lengths = []
        for i in range(n_samples):
            chosen_tt = np.random.choice(self.toilet_types)
            if chosen_tt == "Men":
                chosen_act = np.random.choice(["Urination", "Defecation"])
            else:
                chosen_act = np.random.choice(self.activities)
            seq, _, _ = self.generate_sequence(chosen_act, chosen_tt)
            generated_lengths.append(len(seq))
        
        ks_stat, ks_p = ks_2samp(observed_lengths, generated_lengths)
        
        def get_transitions(seq):
            return [tuple(seq[i:i+2]) for i in range(len(seq)-1)]
        
        observed_transitions = []
        for _, s, a, t in sequences:
            observed_transitions.extend(get_transitions(["Entry"]+s+["Exit"]))
        
        generated_transitions = []
        for i in range(n_samples):
            chosen_tt = np.random.choice(self.toilet_types)
            if chosen_tt == "Men":
                chosen_act = np.random.choice(["Urination", "Defecation"])
            else:
                chosen_act = np.random.choice(self.activities)
            seq, _, _ = self.generate_sequence(chosen_act, chosen_tt)
            generated_transitions.extend(get_transitions(seq))
        
        obs_counts = Counter(observed_transitions)
        gen_counts = Counter(generated_transitions)
        
        all_trans = set(obs_counts.keys()).union(set(gen_counts.keys()))
        obs_array = np.array([obs_counts[t] for t in all_trans])
        gen_array = np.array([gen_counts[t] for t in all_trans])
        
        chi2_stat, chi2_p, _, _ = chi2_contingency(np.vstack([obs_array, gen_array]))
        
        return {
            "length_ks_stat": ks_stat,
            "length_ks_p": ks_p,
            "transition_chi2_stat": chi2_stat,
            "transition_chi2_p": chi2_p
        }
    
    def visualize_transition_matrix(self):
        """
        Visualize the Markov chain transition probabilities as a heatmap.
        Note: This visualizes the global transitions aggregated from all scenarios combined if needed.
        You may want to visualize scenario-specific matrices separately.
        """
        # For demonstration, choose one scenario (e.g., Women, Urination) if available:
        # If you'd like to visualize a specific scenario, pick one here:
        chosen_scenario = ("Women", "Urination")
        if chosen_scenario not in self.markov_chains:
            print(f"No chain for scenario {chosen_scenario}")
            return
        
        scenario_chain = self.markov_chains[chosen_scenario]
        
        unique_states = set()
        for prev in scenario_chain:
            for nxt in scenario_chain[prev]:
                unique_states.add(nxt)
            unique_states.update(prev)
        
        unique_states = list(unique_states)
        state_index = {s: i for i, s in enumerate(unique_states)}
        
        matrix = np.zeros((len(unique_states), len(unique_states)))
        
        counts = defaultdict(float)
        for (prev_states), transitions in scenario_chain.items():
            for nxt, p in transitions.items():
                current_state = prev_states[-1]
                counts[(current_state, nxt)] += p
        
        row_sums = defaultdict(float)
        for (c, n), val in counts.items():
            row_sums[c] += val
        
        for (c, n), val in counts.items():
            if row_sums[c] > 0:
                matrix[state_index[c], state_index[n]] = val / row_sums[c]
        
        plt.figure(figsize=(10,8))
        sns.heatmap(matrix, xticklabels=unique_states, yticklabels=unique_states, annot=False, cmap="viridis")
        plt.title(f"Markov Chain Transition Matrix for {chosen_scenario}")
        plt.xlabel("Next State")
        plt.ylabel("Current State")
        plt.tight_layout()
        plt.show()
