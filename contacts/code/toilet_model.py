import pandas as pd
import numpy as np
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class LocationState:
    location: str
    valid_surfaces: Set[str]
    required_next_surfaces: Optional[Set[str]]

@dataclass
class MarkovChain:
    transitions: Dict[str, Dict[str, float]]
    initial_distribution: Dict[str, float]

class ToiletModel:
    def _preprocess_sequences(self, data: pd.DataFrame) -> pd.DataFrame:
        """Ensure sequences are complete with entry/exit"""
        processed = data.copy()
        
        # Group by experiment
        sequences = []
        for _, group in processed.groupby('ExperimentID'):
            sequence = list(group['Surface'])
            
            # Add entry if missing
            if 'Door handle outside' not in sequence[:2]:
                sequence.insert(0, 'Door handle outside')
                
            # Add exit if missing
            if 'Door handle inside' not in sequence[-2:]:
                sequence.append('Door handle inside')
            
            sequences.append({
                'ExperimentID': group['ExperimentID'].iloc[0],
                'Activity': group['Activity'].iloc[0],
                'Toilet_type': group['Toilet_type'].iloc[0],
                'Sequence': sequence
            })
            
        return pd.DataFrame(sequences)

    def __init__(self, data_file: str):
        """Initialize model with preprocessed data"""
        raw_data = pd.read_csv(data_file)
        self.data = self._preprocess_sequences(raw_data)
        self.locations = self._initialize_locations()
        self.models = self._build_all_models()
        
    def _initialize_locations(self) -> Dict[str, LocationState]:
        """Define valid locations and their properties"""
        return {
            'Entry': LocationState(
                location='Entry',
                valid_surfaces={'Door handle outside', 'Door handle inside'},
                required_next_surfaces=None
            ),
            'Cubicle': LocationState(
                location='Cubicle',
                valid_surfaces={
                    'Toilet paper', 'Toilet surface', 'Flush button',
                    'Cubicle door handle inside', 'Door lock',
                    'Sanitary bin', 'Toilet brush handle'
                },
                required_next_surfaces={'Flush button'}
            ),
            'Hygiene': LocationState(
                location='Hygiene',
                valid_surfaces={
                    'Tap', 'Soap dispenser', 'Hand dryer', 
                    'Paper towel', 'Bin outside the cubicle'
                },
                required_next_surfaces=None
            )
        }
        
    def _get_location(self, surface: str) -> str:
        """Determine location based on surface"""
        for loc_name, loc_state in self.locations.items():
            if surface in loc_state.valid_surfaces:
                return loc_name
        return 'Personal'  # For surfaces like phone, clothing, etc.
        
    def _calculate_transitions(self, sequences: List[List[str]]) -> Dict[str, Dict[str, float]]:
        """Calculate transition probabilities between surfaces"""
        counts = defaultdict(lambda: defaultdict(int))
        for seq in sequences:
            for i in range(len(seq) - 1):
                current, next_state = seq[i], seq[i + 1]
                counts[current][next_state] += 1
        
        transitions = {}
        for current in counts:
            total = sum(counts[current].values())
            transitions[current] = {
                next_state: count/total 
                for next_state, count in counts[current].items()
            }
            
        return transitions
    
    def _calculate_initial_distribution(self, sequences: List[List[str]]) -> Dict[str, float]:
        """Calculate probability distribution of initial surfaces"""
        initial_counts = defaultdict(int)
        for seq in sequences:
            if seq:
                initial_counts[seq[0]] += 1
                
        total = sum(initial_counts.values())
        return {state: count/total for state, count in initial_counts.items()}
        
    def _build_all_models(self) -> Dict[Tuple[str, str], Dict[str, MarkovChain]]:
        """Build Markov chains for each toilet type and activity combination"""
        models = {}
        
        for (toilet_type, activity), group in self.data.groupby(['Toilet_type', 'Activity']):
            location_models = {}
            
            # Group sequences
            for _, row in group.iterrows():
                sequence = row['Sequence']  # Now using the preprocessed sequence
                locations = [self._get_location(s) for s in sequence]
                
                # Split sequence by location
                current_location = locations[0]
                current_sequence = []
                
                for surface, location in zip(sequence, locations):
                    if location != current_location:
                        if current_sequence:
                            if current_location not in location_models:
                                location_models[current_location] = []
                            location_models[current_location].append(current_sequence)
                            
                        current_location = location
                        current_sequence = [surface]
                    else:
                        current_sequence.append(surface)
                
                # Add last sequence
                if current_sequence:
                    if current_location not in location_models:
                        location_models[current_location] = []
                    location_models[current_location].append(current_sequence)
            
            # Build Markov chain for each location
            models[(toilet_type, activity)] = {
                location: MarkovChain(
                    transitions=self._calculate_transitions(sequences),
                    initial_distribution=self._calculate_initial_distribution(sequences)
                )
                for location, sequences in location_models.items()
                if sequences  # Only create models for locations with data
            }
            
        return models
    
    def validate_sequences(self) -> pd.DataFrame:
        """Check sequence completeness and validity"""
        validation = []
        
        for _, row in self.data.iterrows():
            sequence = row['Sequence']
            validation.append({
                'ExperimentID': row['ExperimentID'],
                'Activity': row['Activity'],
                'Toilet_type': row['Toilet_type'],
                'Length': len(sequence),
                'Has_Entry': 'Door handle outside' in sequence[:2],
                'Has_Exit': 'Door handle inside' in sequence[-2:],
                'Has_Handwashing': any(s in sequence for s in ['Tap', 'Soap dispenser']),
                'Sequence': ' -> '.join(sequence)
            })
            
        return pd.DataFrame(validation)
        
    def analyze_transition_probabilities(self) -> Dict:
        """Analyze transition probabilities for debugging"""
        analysis = {}
        
        for (toilet_type, activity), location_models in self.models.items():
            analysis[(toilet_type, activity)] = {}
            
            for location, chain in location_models.items():
                # Analyze transition diversity
                transition_counts = {
                    state: len(transitions) 
                    for state, transitions in chain.transitions.items()
                }
                
                # Check for dead ends (states with no outgoing transitions)
                dead_ends = [
                    state for state in chain.initial_distribution.keys()
                    if state not in chain.transitions
                ]
                
                analysis[(toilet_type, activity)][location] = {
                    'transition_counts': transition_counts,
                    'dead_ends': dead_ends,
                    'initial_states': list(chain.initial_distribution.keys())
                }
                
        return analysis

    def generate_sequence(self, toilet_type: str, activity: str, max_length: int = 30) -> List[str]:
        """Generate a surface contact sequence"""
        model_key = (toilet_type, activity)
        if model_key not in self.models:
            raise ValueError(f"No model for {toilet_type} - {activity}")
            
        location_models = self.models[model_key]
        sequence = []
        current_location = 'Entry'
        
        while len(sequence) < max_length:
            if current_location not in location_models:
                break
                
            model = location_models[current_location]
            
            # Choose initial surface for this location
            if not sequence:
                surface = np.random.choice(
                    list(model.initial_distribution.keys()),
                    p=list(model.initial_distribution.values())
                )
            else:
                surface = sequence[-1]
            
            # Generate sequence for current location
            while len(sequence) < max_length:
                if surface not in model.transitions:
                    break
                    
                next_states = list(model.transitions[surface].keys())
                probs = list(model.transitions[surface].values())
                
                next_surface = np.random.choice(next_states, p=probs)
                sequence.append(next_surface)
                
                # Check if we've moved to a new location
                new_location = self._get_location(next_surface)
                if new_location != current_location:
                    current_location = new_location
                    break
                
                surface = next_surface
                
        return sequence