import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
from typing import List, Dict
import seaborn as sns

class ContactNetworkAnalyzer:
    def __init__(self, data_file: str):
        self.data = pd.read_csv(data_file)
        self.location_colors = {
            'Entry': '#1f77b4',    # blue
            'Cubicle': '#ff7f0e',  # orange
            'Hygiene': '#2ca02c',  # green
            'Personal': '#d62728',   # red
            'Exit': '#5f77b4'
        }
        
    def get_surface_location(self, surface: str) -> str:
        """Map surface to location category"""
        entry_surfaces = {'Door handle outside'}
        exit_surfaces = { 'Door handle inside'}
        cubicle_surfaces = {
            'Toilet paper', 'Toilet surface', 'Flush button',
            'Cubicle door handle inside', 'Door lock',
            'Sanitary bin', 'Toilet brush handle'
        }
        hygiene_surfaces = {
            'Tap', 'Soap dispenser', 'Hand dryer', 
            'Paper towel', 'Bin outside the cubicle'
        }
        
        if surface in entry_surfaces:
            return 'Entry'
        elif surface in cubicle_surfaces:
            return 'Cubicle'
        elif surface in hygiene_surfaces:
            return 'Hygiene'
        elif surface in exit_surfaces:
            return 'Exit'
        else:
            return 'Personal'
    
    
    def create_contact_network(self, activity: str, toilet_type: str, exp_id: str) -> nx.DiGraph:
        """Create directed graph for a specific experiment sequence"""
        # Filter data for specific experiment, activity and toilet type
        sequence = self.data[
            (self.data['ExperimentID'] == exp_id) & 
            (self.data['Activity'] == activity) &
            (self.data['Toilet_type'] == toilet_type)
        ]
        
        if sequence.empty:
            return None
        
        # Create directed graph
        G = nx.DiGraph()
        
        # Add edges based on surface contacts with sequence numbers
        surfaces = list(sequence['Surface'])
        for i in range(len(surfaces) - 1):
            source = surfaces[i]
            target = surfaces[i + 1]
            
            # Add nodes with location information if they don't exist
            if not G.has_node(source):
                G.add_node(source, location=self.get_surface_location(source))
            if not G.has_node(target):
                G.add_node(target, location=self.get_surface_location(target))
            
            # Add edge with sequence number
            if G.has_edge(source, target):
                # If edge exists, append new sequence number
                G[source][target]['sequence_nums'].append(i+1)
            else:
                # Create new edge with first sequence number
                G.add_edge(source, target, sequence_nums=[i+1])
                
        return G
    
    def plot_network(self, G: nx.DiGraph, title: str):
        if G is None or len(G.nodes()) == 0:
            print(f"No data to plot for {title}")
            return None
            
        plt.figure(figsize=(15, 10))
        
        # Use spring layout with more space between nodes
        pos = nx.spring_layout(G, k=2, iterations=50)
        
        # Draw nodes colored by location
        node_colors = [self.location_colors[G.nodes[node]['location']] 
                      for node in G.nodes()]
        nx.draw_networkx_nodes(G, pos, node_color=node_colors,
                             node_size=2000, alpha=0.6)
        
        # Draw edges with sequence numbers
        nx.draw_networkx_edges(G, pos, edge_color='gray',
                             width=2, arrowsize=20)
        
        # Add node labels with smaller font and word wrapping
        labels = {node: '\n'.join(node.split()) for node in G.nodes()}
        nx.draw_networkx_labels(G, pos, labels, font_size=8)
        
        # Add sequence numbers as edge labels
        edge_labels = {(u, v): ','.join(map(str, d['sequence_nums'])) 
                      for u, v, d in G.edges(data=True)}
        nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=8)
        
        # Add legend for locations
        legend_elements = [plt.Line2D([0], [0], marker='o', color='w', 
                                    markerfacecolor=color, label=loc, markersize=15)
                         for loc, color in self.location_colors.items()]
        plt.legend(handles=legend_elements, loc='upper left', title='Locations')
        
        plt.title(title, wrap=True)
        plt.axis('off')
        return plt.gcf()
    
    def analyze_patterns(self) -> pd.DataFrame:
        """Analyze common patterns in sequences"""
        patterns = []
        
        for (activity, toilet_type), group in self.data.groupby(['Activity', 'Toilet_type']):
            experiment_patterns = []
            
            for exp_id in group['ExperimentID'].unique():
                exp_data = group[group['ExperimentID'] == exp_id]
                sequence = list(exp_data['Surface'])
                locations = [self.get_surface_location(s) for s in sequence]
                
                # Analyze location transitions
                location_transitions = []
                current_loc = locations[0]
                for loc in locations[1:]:
                    if loc != current_loc:
                        location_transitions.append(f"{current_loc}->{loc}")
                        current_loc = loc
                
                experiment_patterns.append({
                    'Activity': activity,
                    'Toilet_type': toilet_type,
                    'ExperimentID': exp_id,
                    'Sequence_length': len(sequence),
                    'Location_transitions': ' -> '.join(location_transitions),
                    'Unique_surfaces': len(set(sequence)),
                    'Has_handwashing': any(s in sequence for s in ['Tap', 'Soap dispenser']),
                    'Personal_items_touched': sum(1 for s in sequence 
                                               if self.get_surface_location(s) == 'Personal')
                })
            
            patterns.extend(experiment_patterns)
            
        return pd.DataFrame(patterns)

if __name__ == "__main__":
    # Initialize analyzer
    analyzer = ContactNetworkAnalyzer("../data/clean_contact_data.csv")
    
    # Plot example networks
    activities = analyzer.data['Activity'].unique()
    toilet_types = analyzer.data['Toilet_type'].unique()
    
    # Create networks for each combination
    for activity in activities:
        for toilet_type in toilet_types:
            # Get first 5 unique experiment IDs for this combination
            exp_ids = analyzer.data[
                (analyzer.data['Activity'] == activity) & 
                (analyzer.data['Toilet_type'] == toilet_type)
            ]['ExperimentID'].unique()[:5]
            
            # Create and save network for each experiment
            for exp_id in exp_ids:
                G = analyzer.create_contact_network(activity, toilet_type, exp_id)
                if G is not None:
                    title = f"{activity} in {toilet_type} toilet\nExperiment {exp_id}"
                    fig = analyzer.plot_network(G, title)
                    if fig is not None:
                        fig.savefig(
                            f"network_{activity}_{toilet_type}_{exp_id}.png",
                            bbox_inches='tight',
                            dpi=300
                        )
                        plt.close()
                    else:
                        print(f"Could not create plot for {title}")
                else:
                    print(f"No network created for {activity} - {toilet_type} - {exp_id}")
                    
    # Analyze patterns
    patterns_df = analyzer.analyze_patterns()
    patterns_df.to_csv("sequence_patterns.csv", index=False)
    
    # Print summary statistics
    print("\nPattern Analysis Summary:")
    print("\nMean sequence length by activity:")
    print(patterns_df.groupby('Activity')['Sequence_length'].mean())
    
    print("\nHandwashing compliance:")
    print(patterns_df.groupby('Activity')['Has_handwashing'].mean())
    
    print("\nMost common location transition patterns:")
    print(patterns_df['Location_transitions'].value_counts().head())