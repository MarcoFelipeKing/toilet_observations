import pandas as pd
import numpy as np
from typing import List, Dict, Set, Optional, Tuple
from scipy.stats import ks_2samp, chi2_contingency
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class CubicleState:
    """State tracking for cubicle-specific constraints"""
    is_locked: bool = False
    is_inside: bool = False
    activity_completed: bool = False
    
    def can_access_surface(self, surface: str) -> bool:
        """Check if surface can be accessed in current state"""
        cubicle_only_surfaces = {
            'Toilet paper', 'Toilet surface', 'Flush button',
            'Sanitary bin', 'Toilet brush handle'
        }
        outside_surfaces = {
            'Tap', 'Soap dispenser', 'Hand dryer', 
            'Door handle outside', 'Door handle inside'
        }
        
        if self.is_inside and self.is_locked:
            return surface not in outside_surfaces
        elif self.is_inside and not self.is_locked:
            return surface not in outside_surfaces
        else:
            return surface not in cubicle_only_surfaces

class EnhancedToiletModelWithValidation(EnhancedToiletModel):
    def __init__(self, data_file: str, order: int = 2):
        super().__init__(data_file, order)
        self.activity_patterns = self._analyze_activity_patterns()
        
    def _analyze_activity_patterns(self) -> Dict:
        """Analyze patterns specific to each activity"""
        patterns = {}
        
        for activity in self.data['Activity'].unique():
            activity_data = self.data[self.data['Activity'] == activity]
            
            patterns[activity] = {
                'mean_length': activity_data['Sequence'].apply(len).mean(),
                'std_length': activity_data['Sequence'].apply(len).std(),
                'toilet_paper_freq': self._calculate_surface_frequency(activity_data, 'Toilet paper'),
                'common_transitions': self._get_common_transitions(activity_data)
            }
        
        return patterns
    
    def _calculate_surface_frequency(self, data: pd.DataFrame, surface: str) -> float:
        """Calculate frequency of a surface in sequences"""
        total_touches = sum(len(seq) for seq in data['Sequence'])
        surface_touches = sum(seq.count(surface) for seq in data['Sequence'])
        return surface_touches / total_touches if total_touches > 0 else 0
    
    def _get_common_transitions(self, data: pd.DataFrame) -> Dict[Tuple[str, str], float]:
        """Get transition probabilities from observed data"""
        transitions = defaultdict(int)
        total_transitions = 0
        
        for sequence in data['Sequence']:
            for i in range(len(sequence) - 1):
                transitions[(sequence[i], sequence[i+1])] += 1
                total_transitions += 1
        
        return {k: v/total_transitions for k, v in transitions.items()}
    
    def validate_sequences(self, n_samples: int = 1000) -> Dict:
        """Validate generated sequences against observed patterns"""
        validation_results = {}
        
        for activity in self.activity_patterns:
            # Generate test sequences
            generated_sequences = [
                self.generate_sequence(activity, "Gender neutral")[0]
                for _ in range(n_samples)
            ]
            
            # Get observed sequences
            observed_sequences = list(
                self.data[self.data['Activity'] == activity]['Sequence']
            )
            
            # Length distribution comparison
            gen_lengths = [len(seq) for seq in generated_sequences]
            obs_lengths = [len(seq) for seq in observed_sequences]
            
            # Kolmogorov-Smirnov test for length distributions
            ks_stat, ks_pvalue = ks_2samp(gen_lengths, obs_lengths)
            
            # Transition pattern comparison
            gen_transitions = self._get_common_transitions(pd.DataFrame({'Sequence': generated_sequences}))
            obs_transitions = self.activity_patterns[activity]['common_transitions']
            
            # Chi-square test for transition patterns
            transition_chi2 = self._compare_transition_patterns(
                gen_transitions, obs_transitions
            )
            
            validation_results[activity] = {
                'length_ks_stat': ks_stat,
                'length_ks_pvalue': ks_pvalue,
                'transition_chi2': transition_chi2,
                'mean_length_diff': np.mean(gen_lengths) - self.activity_patterns[activity]['mean_length'],
                'std_length_diff': np.std(gen_lengths) - self.activity_patterns[activity]['std_length']
            }
            
        return validation_results
    
    def _compare_transition_patterns(self, gen_trans: Dict, obs_trans: Dict) -> float:
        """Compare transition patterns using chi-square test"""
        all_transitions = set(gen_trans.keys()) | set(obs_trans.keys())
        
        # Create contingency table
        table = []
        for trans in all_transitions:
            gen_count = gen_trans.get(trans, 0)
            obs_count = obs_trans.get(trans, 0)
            table.append([gen_count, obs_count])
            
        # Perform chi-square test
        chi2, _ = chi2_contingency(np.array(table))
        return chi2
    
    def generate_sequence(self, activity: str, toilet_type: str) -> Tuple[List[str], Dict]:
        """Generate sequence with enhanced spatial constraints"""
        sequence = []
        metadata = {
            'handwashing': False,
            'handwashing_effectiveness': 0.0,
            'interrupts': 0,
            'phases': [],
            'cubicle_state': CubicleState()
        }
        
        # Initialize state
        history = ['START'] * (self.order - 1)
        phase = 'initial'
        consecutive_interrupts = 0
        
        while True:
            state_key = (tuple(history), phase)
            
            # Apply cubicle constraints
            if metadata['cubicle_state'].is_inside:
                valid_surfaces = self._get_valid_surfaces(metadata['cubicle_state'])
            else:
                valid_surfaces = None
                
            # Generate next surface with constraints
            next_surface = self._generate_next_surface(
                state_key, valid_surfaces, activity, phase
            )
            
            if next_surface is None:
                break
                
            # Update cubicle state
            self._update_cubicle_state(metadata['cubicle_state'], next_surface)
            
            sequence.append(next_surface)
            metadata['phases'].append(phase)
            
            # Update state
            history = (history + [next_surface])[1:]
            phase = self._update_phase(sequence, phase)
            
            # Check for sequence completion
            if self._is_sequence_complete(sequence, metadata):
                break
        
        return sequence, metadata
    
    def _get_valid_surfaces(self, cubicle_state: CubicleState) -> Set[str]:
        """Get valid surfaces based on cubicle state"""
        valid_surfaces = set()
        
        if cubicle_state.is_inside and cubicle_state.is_locked:
            valid_surfaces.update([
                'Toilet paper', 'Toilet surface', 'Flush button',
                'Sanitary bin', 'Toilet brush handle', 'Personal item'
            ])
        elif cubicle_state.is_inside and not cubicle_state.is_locked:
            valid_surfaces.update([
                'Cubicle door handle inside', 'Door lock',
                'Personal item'
            ])
        else:
            valid_surfaces.update([
                'Door handle outside', 'Door handle inside',
                'Tap', 'Soap dispenser', 'Hand dryer',
                'Personal item'
            ])
            
        return valid_surfaces
    
    def _update_cubicle_state(self, state: CubicleState, surface: str):
        """Update cubicle state based on surface interaction"""
        if surface == 'Door lock':
            state.is_locked = not state.is_locked
        elif surface == 'Cubicle door handle inside':
            state.is_inside = True
        elif surface in {'Toilet surface', 'Flush button'}:
            state.activity_completed = True
            
    def _is_sequence_complete(self, sequence: List[str], metadata: Dict) -> bool:
        """Check if sequence is complete"""
        if len(sequence) < 5:
            return False
            
        # Must exit through door
        if sequence[-1] != 'Door handle inside':
            return False
            
        # Must complete activity
        if not metadata['cubicle_state'].activity_completed:
            return False
            
        return True

if __name__ == "__main__":
    # Example usage with validation
    model = EnhancedToiletModelWithValidation("../data/clean_contact_data.csv")
    
    # Generate and validate sequences
    validation_results = model.validate_sequences(n_samples=1000)
    
    print("\nValidation Results:")
    for activity, results in validation_results.items():
        print(f"\n{activity}:")
        print(f"Length KS test p-value: {results['length_ks_pvalue']:.4f}")
        print(f"Mean length difference: {results['mean_length_diff']:.2f}")
        print(f"Transition pattern chi2: {results['transition_chi2']:.2f}")
    
    # Generate example sequence
    sequence, metadata = model.generate_sequence("Urination", "Gender neutral")
    print("\nExample Generated Sequence:")
    print(" -> ".join(sequence))
    print(f"Length: {len(sequence)}")
    print(f"Handwashing: {metadata['handwashing']}")