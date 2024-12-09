import pandas as pd
import numpy as np
import random
from collections import defaultdict, Counter
from scipy.stats import beta, lognorm, bernoulli, ks_2samp, chi2_contingency
import networkx as nx

class EnhancedToiletModelWithValidation:
    def __init__(self, data_file):
        """
        Initialize model with observed data.
        :param data_file: Path to clean_contact_data.csv
        """
        self.data_file = data_file
        self.data = pd.read_csv(data_file, sep=",")
        
        # Ensure data integrity: every ExperimentID has Entry and Exit at least
        # Filtering logic may be needed if data incomplete
        self._check_data_integrity()
        
        # Define states (surface categories), activities, toilet types
        self.surface_categories = ["Entry", "CubicleIN", "Cubicle", "CubicleOUT", "Hygiene", "Personal", "Exit", "MHM"]
        # Note: MHM surfaces can be considered a subtype of Cubicle or their own category
        # depending on modeling choice. For simplicity, treat "Menstrual product" etc. as "MHM" state category.
        
        self.activities = ["Urination", "Defecation", "MHM"]
        self.toilet_types = ["Men", "Women", "Gender neutral"]
        
        # Preprocess data to build higher-order Markov chain transition probabilities
        self.markov_chain = self._build_higher_order_markov_chain(order=2)
        
        # Hand hygiene compliance probability (assumed global or activity-specific)
        self.hand_hygiene_compliance_prob = 0.7  # example value
        
        # Surface to hand and hand to surface parameters
        self.default_transfer_efficiency = 0.1
        self.default_surface_contact_fraction = 0.1
        self.default_initial_contamination = 100.0
        self.default_pathogen_decay_rate = 0.05  # arbitrary daily decay or per-minute decay factor
        
    def _check_data_integrity(self):
        # Simple check: Ensure each ExperimentID starts with Entry and ends with Exit
        # Note: This may require domain logic. For now, just a placeholder.
        pass
        
    def _extract_sequences(self):
        """
        Extract sequences of surfaces from observed data grouped by ExperimentID.
        """
        sequences = []
        for exp_id, group in self.data.groupby("ExperimentID"):
            # Sort by order of occurrence if needed
            seq = group.sort_values(by="ID")  # If ID represents chronological order
            surfaces = seq["SurfaceCategories"].tolist()
            # Additional info can be stored as metadata
            activity = seq["Activity"].iloc[0]
            toilet_type = seq["Toilet_type"].iloc[0]
            sequences.append((exp_id, surfaces, activity, toilet_type))
        return sequences
    
    def _build_higher_order_markov_chain(self, order=2):
        """
        Build a higher-order Markov chain from observed sequences.
        Using order=2 for demonstration.
        """
        sequences = self._extract_sequences()
        # Dictionary keyed by (prev_state1, prev_state2) to counts of next_state
        transition_counts = defaultdict(Counter)
        
        for _, surf_seq, activity, ttype in sequences:
            # Add pseudo-start states if needed
            padded_seq = ["Entry"] + surf_seq + ["Exit"]
            for i in range(len(padded_seq) - order):
                prev_states = tuple(padded_seq[i:i+order])
                next_state = padded_seq[i+order]
                transition_counts[(prev_states)][next_state] += 1
        
        # Convert counts to probabilities
        transition_probs = {}
        for prev, counts in transition_counts.items():
            total = sum(counts.values())
            transition_probs[prev] = {k: v/total for k, v in counts.items()}
        
        return transition_probs
    
    def generate_sequence(self, activity, toilet_type, max_length=50):
        """
        Generate a synthetic sequence of surface contacts given activity and toilet type.
        Incorporate logic and constraints:
        - Start at "Entry"
        - Must progress logically: Entry -> CubicleIN (if using cubicle) -> Cubicle -> ...
        - Can have Personal interruptions (e.g. phone, clothing)
        - End at "Exit"
        """
        # For simplicity, start with "Entry"
        # We'll randomly pick transitions from self.markov_chain
        sequence = ["Entry"]
        
        # Attempt a generative process using the Markov chain:
        # We'll try to maintain a last 2 states context
        while len(sequence) < max_length and sequence[-1] != "Exit":
            prev_states = tuple(sequence[-2:]) if len(sequence) > 1 else ("Entry", sequence[-1])
            if prev_states not in self.markov_chain:
                # If no known transitions, break
                break
            next_states_prob = self.markov_chain[prev_states]
            next_state = np.random.choice(list(next_states_prob.keys()), p=list(next_states_prob.values()))
            
            # Apply constraints (e.g. if activity=Urination and toilet_type=Men, prefer Urinal surfaces)
            # For demonstration, we won't deeply implement all constraints here, but in a real model you would:
            # - If activity=Urination (men) -> includes "Urinal" states
            # - If inside cubicle, restrict transitions to surfaces inside cubicle + personal items
            # etc.
            
            # Add random personal interruptions:
            # With some probability, insert a "Personal" item touch
            if np.random.rand() < 0.2 and sequence[-1] != "Exit":
                sequence.append("Personal")
            
            sequence.append(next_state)
        
        # Ensure there's an Exit
        if sequence[-1] != "Exit":
            sequence.append("Exit")
        
        # Assign random hand usage (Left/Right/Both) pattern
        hand_pattern = np.random.choice(["Left", "Right", "Both"], size=len(sequence))
        
        metadata = {
            "activity": activity,
            "toilet_type": toilet_type,
            "hand_hygiene_compliant": bool(bernoulli.rvs(self.hand_hygiene_compliance_prob))
        }
        
        return sequence, hand_pattern, metadata
    
    def simulate_contamination(self, sequence, initial_surface_contamination=None,
                               transfer_efficiency=None, surface_contact_fraction=None,
                               pathogen_decay_rate=None):
        """
        Simulate pathogen contamination over the generated sequence.
        
        Each surface has a contamination level. Each hand has a contamination level.
        On touching a surface:
        - Transfer occurs bidirectionally based on concentration gradient.
        - After contact, update hand and surface contamination.
        
        Then apply hand hygiene if performed.
        """
        if initial_surface_contamination is None:
            initial_surface_contamination = self.default_initial_contamination
        if transfer_efficiency is None:
            transfer_efficiency = self.default_transfer_efficiency
        if surface_contact_fraction is None:
            surface_contact_fraction = self.default_surface_contact_fraction
        if pathogen_decay_rate is None:
            pathogen_decay_rate = self.default_pathogen_decay_rate
        
        # Initialize surfaces with some contamination (for simplicity, uniform)
        # In reality, different surfaces would have different initial levels
        surfaces = {s: initial_surface_contamination for s in self.surface_categories if s != "Exit"}
        # Hands start clean or with low contamination
        left_hand_contamination = 10.0
        right_hand_contamination = 10.0
        
        hand_contamination_over_time = []
        surface_contamination_over_time = []
        
        # Assume each step is a contact event
        for idx, surf in enumerate(sequence):
            # Decay pathogen on surfaces over time (simple multiplicative decay)
            for k in surfaces:
                surfaces[k] *= (1 - pathogen_decay_rate)
            
            # Determine which hand(s) used
            # For simplicity, assume we have a stored hand pattern
            # If you passed hand_pattern from generate_sequence, you would use it.
            # Here, just randomly choose:
            chosen_hand = np.random.choice(["Left", "Right", "Both"])
            
            # Hand contamination before contact
            h_before = (left_hand_contamination + right_hand_contamination)/2
            
            if surf in surfaces:
                # Contact event:
                surface_load = surfaces[surf]
                hand_load = (left_hand_contamination + right_hand_contamination)/2.0
                
                # Transfer proportion based on gradient
                # delta = transfer_efficiency * contact fraction * (difference in contamination)
                delta = transfer_efficiency * surface_contact_fraction * (surface_load - hand_load)
                
                # Update both
                if chosen_hand == "Left":
                    left_hand_contamination += delta
                elif chosen_hand == "Right":
                    right_hand_contamination += delta
                else:
                    # Both hands share transfer
                    left_hand_contamination += delta/2
                    right_hand_contamination += delta/2
                
                # Surface loses or gains from the hand correspondingly
                surfaces[surf] -= delta
            
            # Possibly apply hand hygiene if at a Hygiene state and user is compliant
            # Handwashing reduces contamination by a lognormal distributed factor
            if surf == "Hygiene":
                # Check compliance
                if bernoulli.rvs(self.hand_hygiene_compliance_prob):
                    # Draw from lognormal to get reduction factor
                    reduction_factor = lognorm(s=0.5, scale=np.exp(-1)).rvs()  # example: ~e^-1 on average
                    left_hand_contamination *= reduction_factor
                    right_hand_contamination *= reduction_factor
            
            hand_contamination_over_time.append((left_hand_contamination, right_hand_contamination))
            surface_contamination_over_time.append(surfaces.copy())
        
        # Return final contamination levels and full timeline
        return {
            "final_hands": (left_hand_contamination, right_hand_contamination),
            "hand_time_series": hand_contamination_over_time,
            "surface_time_series": surface_contamination_over_time
        }
    
    def validate_sequences(self, n_samples=1000):
        """
        Validate generated sequences against observed data.
        
        Metrics:
        - Length distribution: KS test between observed and generated
        - Transition patterns: Chi-square test on transition counts
        """
        sequences = self._extract_sequences()
        observed_lengths = [len(s) for _, s, _, _ in sequences]
        
        generated_lengths = []
        for i in range(n_samples):
            seq, _, _ = self.generate_sequence(
                activity=np.random.choice(self.activities),
                toilet_type=np.random.choice(self.toilet_types)
            )
            generated_lengths.append(len(seq))
        
        # KS test for length distributions
        ks_stat, ks_p = ks_2samp(observed_lengths, generated_lengths)
        
        # For transition patterns: create a contingency table of observed vs generated transitions
        def get_transitions(seq):
            return [tuple(seq[i:i+2]) for i in range(len(seq)-1)]
        
        observed_transitions = []
        for _, s, _, _ in sequences:
            observed_transitions.extend(get_transitions(["Entry"]+s+["Exit"]))
        
        generated_transitions = []
        for i in range(n_samples):
            seq, _, _ = self.generate_sequence(
                activity=np.random.choice(self.activities),
                toilet_type=np.random.choice(self.toilet_types)
            )
            generated_transitions.extend(get_transitions(seq))
        
        # Count transitions
        obs_counts = Counter(observed_transitions)
        gen_counts = Counter(generated_transitions)
        
        # Create a common set
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
