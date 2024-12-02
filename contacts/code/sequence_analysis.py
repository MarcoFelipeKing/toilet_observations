import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Tuple, Dict
from toilet_model import ToiletModel

class SequenceAnalyzer:
    def __init__(self, model: ToiletModel, n_simulations: int = 1000):
        self.model = model
        self.n_simulations = n_simulations
        
    def get_sequence_lengths(self, data: pd.DataFrame) -> Dict[Tuple[str, str], List[int]]:
        lengths = {}
        for (toilet_type, activity), group in data.groupby(['Toilet_type', 'Activity']):
            lengths[(toilet_type, activity)] = [
                len(seq) for _, seq in group.groupby(['ExperimentID']) #, 'ParticipantID'
            ]
        return lengths
        
    def simulate_sequences(self, toilet_type: str, activity: str) -> List[int]:
        lengths = []
        for _ in range(self.n_simulations):
            seq = self.model.generate_sequence(toilet_type, activity)
            lengths.append(len(seq))
        return lengths
    
    def plot_length_comparison(self, observed_lengths: Dict[Tuple[str, str], List[int]]):
        n_combos = len(observed_lengths)
        fig, axes = plt.subplots(n_combos, 1, figsize=(10, 5*n_combos))
        if n_combos == 1:
            axes = [axes]
            
        colors = {'Observed': '#ff7f0e', 'Simulated': '#1f77b4'}
            
        for idx, ((toilet_type, activity), obs_lens) in enumerate(observed_lengths.items()):
            ax = axes[idx]
            sim_lens = self.simulate_sequences(toilet_type, activity)
            
            # Create violin plot
            plot_data = pd.DataFrame({
                'Length': obs_lens + sim_lens,
                'Type': ['Observed']*len(obs_lens) + ['Simulated']*len(sim_lens)
            })
            
            sns.violinplot(data=plot_data, x='Type', y='Length', ax=ax, 
                         palette=colors, inner='box')
            
            ax.set_title(f'{toilet_type} - {activity}')
            ax.set_ylabel('Sequence Length')
            
        plt.tight_layout()
        return fig

    def simulate_contamination(self, toilet_type: str, activity: str,
                             initial_surface_contamination: float = 100,
                             initial_hand_contamination: float = 0,
                             transfer_efficiency: float = 0.1,
                             surface_contact_fraction: float = 0.1,
                             n_people: int = 100) -> pd.DataFrame:
        results = []
        
        for person in range(n_people):
            sequence = self.model.generate_sequence(toilet_type, activity)
            hand_contam = initial_hand_contamination
            surface_contams = {surface: initial_surface_contamination for surface in set(sequence)}
            
            for step, surface in enumerate(sequence):
                # Calculate effective surface area for transfer
                effective_surface_contam = surface_contams[surface] * surface_contact_fraction
                
                # Calculate transfer based on concentration gradient
                if hand_contam > effective_surface_contam:
                    # Transfer from hand to surface
                    transfer = (hand_contam - effective_surface_contam) * transfer_efficiency
                    hand_contam -= transfer
                    surface_contams[surface] += transfer / surface_contact_fraction
                else:
                    # Transfer from surface to hand
                    transfer = (effective_surface_contam - hand_contam) * transfer_efficiency
                    hand_contam += transfer
                    surface_contams[surface] -= transfer / surface_contact_fraction
                
                results.append({
                    'Person': person,
                    'Step': step,
                    'Surface': surface,
                    'HandContamination': hand_contam,
                    'SurfaceContamination': surface_contams[surface]
                })
                
        return pd.DataFrame(results)
                
    
    def plot_contamination_profiles(self, contamination_data: pd.DataFrame):
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        for person in contamination_data['Person'].unique()[:10]:
            person_data = contamination_data[contamination_data['Person'] == person]
            ax1.step(person_data['Step'], person_data['HandContamination'], 
                    where='post', alpha=0.5, label=f'Person {person}')
            
        ax1.set_title('Hand Contamination Over Sequence')
        ax1.set_xlabel('Contact Step')
        ax1.set_ylabel('Contamination Level')
        
        surfaces = contamination_data['Surface'].unique()
        for surface in surfaces[:5]:
            surface_data = contamination_data[contamination_data['Surface'] == surface]
            ax2.step(surface_data['Step'], surface_data['SurfaceContamination'],
                    where='post', alpha=0.5, label=surface)
            
        ax2.set_title('Surface Contamination Over Time')
        ax2.set_xlabel('Contact Step')
        ax2.set_ylabel('Contamination Level')
        ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        plt.tight_layout()
        return fig

if __name__ == "__main__":
    # Initialize models
    model = ToiletModel("../data/clean_contact_data.csv")
    analyzer = SequenceAnalyzer(model)
    
    # Compare sequence lengths
    observed_lengths = analyzer.get_sequence_lengths(model.data)
    length_fig = analyzer.plot_length_comparison(observed_lengths)
    length_fig.savefig("sequence_length_comparison.png")
    
    # Analyze contamination patterns
    contam_data = analyzer.simulate_contamination("Women", "Urination")
    contam_fig = analyzer.plot_contamination_profiles(contam_data)
    contam_fig.savefig("contamination_profiles.png")