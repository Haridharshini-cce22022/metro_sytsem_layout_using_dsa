from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QPalette, QColor
import folium
from opencage.geocoder import OpenCageGeocode
import geopy.distance as geodesic
import networkx as nx

class LocationPlotterGUI(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Location Plotter")
        self.setGeometry(100, 100, 400, 600)

        layout = QVBoxLayout()

        self.city_label = QLabel("Enter the name of the city:")
        layout.addWidget(self.city_label)

        self.city_entry = QLineEdit()
        layout.addWidget(self.city_entry)

        self.location_label = QLabel("Enter locations to pin on the map. Type 'done' when finished:")
        layout.addWidget(self.location_label)

        self.location_entry = QLineEdit()
        layout.addWidget(self.location_entry)

        self.add_location_button = QPushButton("Add Location", clicked=self.add_location)
        layout.addWidget(self.add_location_button)

        self.plot_map_button = QPushButton("Plot Map", clicked=self.plot_map)
        layout.addWidget(self.plot_map_button)

        self.remove_edge_button = QPushButton("Remove Edge", clicked=self.remove_edge_gui)
        layout.addWidget(self.remove_edge_button)
        
        self.edge_remove_entry = QLineEdit()
        layout.addWidget(self.edge_remove_entry)

        # Labels to display distances and costs for both plans
        self.plan_a_label = QLabel("Plan A - Christofides' Algorithm:")
        layout.addWidget(self.plan_a_label)
        
        self.plan_a_distance_label = QLabel("Total Distance: ")
        layout.addWidget(self.plan_a_distance_label)
        
        self.plan_a_cost_label = QLabel("Total Cost: ")
        layout.addWidget(self.plan_a_cost_label)
        
        self.plan_b_label = QLabel("Plan B - Prim's Algorithm:")
        layout.addWidget(self.plan_b_label)
        
        self.plan_b_distance_label = QLabel("Total Distance: ")
        layout.addWidget(self.plan_b_distance_label)
        
        self.plan_b_cost_label = QLabel("Total Cost: ")
        layout.addWidget(self.plan_b_cost_label)

        self.setLayout(layout)

        self.locations = []
        self.graph = nx.Graph()

        self.apply_styles()

    def apply_styles(self):
        palette = QPalette()

        palette.setColor(QPalette.Window, QColor(140, 140, 140))

        palette.setColor(QPalette.WindowText, QColor(70, 70, 70))

        palette.setColor(QPalette.Button, QColor(100, 160, 220))
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))

        self.setPalette(palette)

        self.setStyleSheet(
            "QLineEdit { background-color: white; border: 1px solid gray; border-radius: 5px; }"
            "QPushButton { background-color: #649CDB; color: white; border: 1px solid #649CDB; border-radius: 5px; }"
            "QPushButton:hover { background-color: #3A77B9; }"
        )

    def get_coordinates(self, location):
        key = '758df8d8a1574a7ba3380ce407e2e308'  
        geocoder = OpenCageGeocode(key)

        results = geocoder.geocode(location)
        if results and len(results):
            first_result = results[0]
            return first_result['geometry']['lat'], first_result['geometry']['lng']
        else:
            print(f"Could not find coordinates for {location}")
            return None

    def calculate_distance(self, coord1, coord2):
        return geodesic.distance(coord1, coord2).kilometers

    def add_location(self):
        location = self.location_entry.text()
        if location.lower() != 'done':
            self.locations.append(location)
            self.location_entry.clear()

    def plot_map(self):
        city_name = self.city_entry.text()
        locations = self.locations

        city_coordinates = self.get_coordinates(city_name)
        if city_coordinates is None:
            print("Unable to get coordinates for the city.")
            return None

        self.graph.clear()

        map_object = folium.Map(location=city_coordinates, zoom_start=12)

        if len(locations) == 0:
            folium.Marker(location=city_coordinates, popup=city_name).add_to(map_object)

        elif len(locations) == 1:
            location = locations[0]
            location_coordinates = self.get_coordinates(location)
            if location_coordinates:
                folium.Marker(location=location_coordinates, popup=location).add_to(map_object)
            else:
                print(f"Unable to get coordinates for {location}.")
                return None

        else:
            for i, location1 in enumerate(locations):
                coordinates1 = self.get_coordinates(location1)
                if coordinates1 is None:
                    continue

                for j, location2 in enumerate(locations):
                    if i != j:
                        coordinates2 = self.get_coordinates(location2)
                        if coordinates2 is not None:
                            distance = self.calculate_distance(coordinates1, coordinates2)
                            self.graph.add_edge(location1, location2, weight=distance)

            christofides_edges = self.christofides_algorithm(self.graph)
            
            total_length1 = 0
            for edge in christofides_edges:
                coordinates1 = self.get_coordinates(edge[0])
                coordinates2 = self.get_coordinates(edge[1])
                if coordinates1 is not None and coordinates2 is not None:
                    folium.Marker(location=coordinates1, popup=edge[0]).add_to(map_object)
                    folium.Marker(location=coordinates2, popup=edge[1]).add_to(map_object)
                    folium.PolyLine([coordinates1, coordinates2], color="blue", weight=2.5).add_to(map_object)

                    if edge[0] in self.graph and edge[1] in self.graph[edge[0]]:
                        total_length1 += self.graph[edge[0]][edge[1]]['weight']

            map_file_christofides = f"{city_name}_map_with_christofides_algorithm.html"
            map_object.save(map_file_christofides)
            print(f"\nCity map with Christofides' Algorithm saved as '{map_file_christofides}'")
            print(f"\nTotal length of edges in Plan A: {total_length1:.2f} kilometers")
            cost_a_u, cost_a_e = self.cost_of_costruction(total_length1)

            # Update Plan A labels
            self.plan_a_distance_label.setText(f"Total Distance: {total_length1:.2f} kilometers")
            self.plan_a_cost_label.setText(f"Total Cost: Underground: {cost_a_u:.2f} crores, Elevated: {cost_a_e:.2f} crores")
            
            map_object = folium.Map(location=city_coordinates, zoom_start=12)

            min_spanning_tree_edges = self.prim_algorithm(self.graph)

            for edge in min_spanning_tree_edges:
                coordinates1 = self.get_coordinates(edge[0])
                coordinates2 = self.get_coordinates(edge[1])
                if coordinates1 is not None and coordinates2 is not None:
                    folium.Marker(location=coordinates1, popup=edge[0]).add_to(map_object)
                    folium.Marker(location=coordinates2, popup=edge[1]).add_to(map_object)
                    folium.PolyLine([coordinates1, coordinates2], color="red", weight=2.5).add_to(map_object)

            total_length2 = 0
            for edge in min_spanning_tree_edges:
                coordinates1 = self.get_coordinates(edge[0])
                coordinates2 = self.get_coordinates(edge[1])
                if coordinates1 is not None and coordinates2 is not None:
                    total_length2 += self.graph[edge[0]][edge[1]]['weight']

            map_file_prims = f"{city_name}_map_with_mst_prims.html"
            map_object.save(map_file_prims)
            print(f"City map with Minimum Spanning Tree (Prim's algorithm) saved as '{map_file_prims}'")
            print(f"\nTotal length of edges in Plan B: {total_length2:.2f} kilometers")
            cost_b_u, cost_b_e = self.cost_of_costruction(total_length2)

            # Update Plan B labels
            self.plan_b_distance_label.setText(f"Total Distance: {total_length2:.2f} kilometers")
            self.plan_b_cost_label.setText(f"Total Cost: Underground: {cost_b_u:.2f} crores, Elevated: {cost_b_e:.2f} crores")

        map_file = f"{city_name}_map.html"
        map_object.save(map_file)
        print(f"Map saved as '{map_file}'")
       
    def cost_of_costruction(self, tot_dis):
        nodes = len(self.locations)
        
        track_cost_u = tot_dis * 125
        station_cost_u = nodes * 5
        total_cost_u = track_cost_u + station_cost_u
            
        track_cost_e = tot_dis * 37
        station_cost_e = nodes * 8
        total_cost_e = track_cost_e + station_cost_e

        return total_cost_u, total_cost_e
        
    def christofides_algorithm(self, graph):
        min_spanning_tree_edges = self.prim_algorithm(graph)

        multigraph = nx.MultiGraph()
        multigraph.add_edges_from(min_spanning_tree_edges)

        odd_degree_nodes = [node for node in multigraph.nodes if multigraph.degree(node) % 2 == 1]

        subgraph = graph.subgraph(odd_degree_nodes)
        min_weight_perfect_matching_edges = nx.algorithms.matching.max_weight_matching(subgraph, maxcardinality=True)

        combined_edges = self.combine_edges(min_spanning_tree_edges, min_weight_perfect_matching_edges)

        eulerian_multigraph = nx.MultiGraph()
        eulerian_multigraph.add_edges_from(combined_edges)

        eulerian_circuit = list(nx.eulerian_circuit(eulerian_multigraph))

        unique_edges = []
        visited = set()

        for edge in eulerian_circuit:
            if edge not in visited and (edge[1], edge[0]) not in visited:
                unique_edges.append(edge)
                visited.add(edge)

        return unique_edges

    def prim_algorithm(self, graph):
        visited = set()
        start_node = list(graph.nodes)[0]
        visited.add(start_node)

        min_spanning_tree_edges = []

        while len(visited) < len(graph.nodes):
            min_edge = None
            min_edge_weight = float('inf')

            for node in visited:
                for neighbor, data in graph[node].items():
                    if neighbor not in visited and data['weight'] < min_edge_weight:
                        min_edge = (node, neighbor)
                        min_edge_weight = data['weight']

            min_spanning_tree_edges.append(min_edge)
            visited.add(min_edge[1])

        return min_spanning_tree_edges

    def combine_edges(self, edges1, edges2):
        combined_edges = edges1[:]
        for edge in edges2:
            combined_edges.append(edge)
        return combined_edges

    def remove_edge_gui(self):
        edge_to_remove = self.edge_remove_entry.text().split()
        
        if len(edge_to_remove) != 2:
            print("Invalid input. Please enter two locations separated by a space.")
            return

        location1, location2 = edge_to_remove
        if (location1, location2) in self.graph.edges or (location2, location1) in self.graph.edges:
            
            self.graph.remove_edge(location1, location2)
            print(f"Edge ({location1}, {location2}) removed.")
        else:
            print(f"Edge ({location1}, {location2}) not found in the graph.")

        self.plot_map_without_edge(location1, location2)
        
    def plot_map_without_edge(self,point1, point2):
        city_name = self.city_entry.text()
        locations = self.locations

        city_coordinates = self.get_coordinates(city_name)
        if city_coordinates is None:
            print("Unable to get coordinates for the city.")
            return None

        self.graph.clear()

        map_object = folium.Map(location=city_coordinates, zoom_start=12)

        for i, location1 in enumerate(locations):
            coordinates1 = self.get_coordinates(location1)
            if coordinates1 is None:
                continue

            for j, location2 in enumerate(locations):
                if i != j:
                    coordinates2 = self.get_coordinates(location2)
                    if coordinates2 is not None:
                        if location1!=point1 and location2!=point2:
                            distance = self.calculate_distance(coordinates1, coordinates2)
                            self.graph.add_edge(location1, location2, weight=distance)

        christofides_edges = self.christofides_algorithm(self.graph)
        
        total_length1 = 0
        for edge in christofides_edges:
            coordinates1 = self.get_coordinates(edge[0])
            coordinates2 = self.get_coordinates(edge[1])
            if coordinates1 is not None and coordinates2 is not None:
                folium.Marker(location=coordinates1, popup=edge[0]).add_to(map_object)
                folium.Marker(location=coordinates2, popup=edge[1]).add_to(map_object)
                folium.PolyLine([coordinates1, coordinates2], color="blue", weight=2.5).add_to(map_object)

                if edge[0] in self.graph and edge[1] in self.graph[edge[0]]:
                    total_length1 += self.graph[edge[0]][edge[1]]['weight']

        map_file_christofides = f"{city_name}_map_with_christofides_algorithm_new.html"
        map_object.save(map_file_christofides)
        print(f"\nCity map with Christofides' Algorithm saved as '{map_file_christofides}'")
        print(f"\nTotal length of edges in Plan A_new: {total_length1:.2f} kilometers")
        cost_a_u, cost_a_e = self.cost_of_costruction(total_length1)

        # Update Plan A labels
        self.plan_a_distance_label.setText(f"Total Distance: {total_length1:.2f} kilometers")
        self.plan_a_cost_label.setText(f"Total Cost: Underground: {cost_a_u:.2f} crores, Elevated: {cost_a_e:.2f} crores")
        
        map_object = folium.Map(location=city_coordinates, zoom_start=12)

        min_spanning_tree_edges = self.prim_algorithm(self.graph)

        for edge in min_spanning_tree_edges:
            coordinates1 = self.get_coordinates(edge[0])
            coordinates2 = self.get_coordinates(edge[1])
            if coordinates1 is not None and coordinates2 is not None:
                folium.Marker(location=coordinates1, popup=edge[0]).add_to(map_object)
                folium.Marker(location=coordinates2, popup=edge[1]).add_to(map_object)
                folium.PolyLine([coordinates1, coordinates2], color="red", weight=2.5).add_to(map_object)

        total_length2 = 0
        for edge in min_spanning_tree_edges:
            coordinates1 = self.get_coordinates(edge[0])
            coordinates2 = self.get_coordinates(edge[1])
            if coordinates1 is not None and coordinates2 is not None:
                total_length2 += self.graph[edge[0]][edge[1]]['weight']

        map_file_prims = f"{city_name}_map_with_mst_prims_new.html"
        map_object.save(map_file_prims)
        print(f"City map with Minimum Spanning Tree (Prim's algorithm) saved as '{map_file_prims}'")
        print(f"\nTotal length of edges in Plan B_new: {total_length2:.2f} kilometers")
        cost_b_u, cost_b_e = self.cost_of_costruction(total_length2)

        # Update Plan B labels
        self.plan_b_distance_label.setText(f"Total Distance: {total_length2:.2f} kilometers")
        self.plan_b_cost_label.setText(f"Total Cost: Underground: {cost_b_u:.2f} crores, Elevated: {cost_b_e:.2f} crores")

app = QApplication([])
window = LocationPlotterGUI()
window.show()
app.exec_()
