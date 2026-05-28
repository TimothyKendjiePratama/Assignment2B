# pathfinder.py
"""
A* pathfinding algorithm (reused from Assignment 2A)
Finds top-K shortest paths between SCATS sites
"""

from heapq import heappush, heappop
from config import DEFAULT_K_ROUTES, MAX_VISITS_PER_NODE


class PathFinder:
    def __init__(self, graph, travel_time_calculator, traffic_predictor):
        self.graph = graph
        self.tt_calc = travel_time_calculator
        self.traffic_predictor = traffic_predictor
        self.current_model = 'lstm'
        
    def set_model(self, model_name):
        self.current_model = model_name
    
    def find_top_k_paths(self, start, goal, k=DEFAULT_K_ROUTES, hour=12):
        """
        Find top-K shortest paths using A* with k-shortest paths extension.
        
        Args:
            start: Origin SCATS site number
            goal: Destination SCATS site number
            k: Number of routes to find
            hour: Hour of day (0-23) for traffic prediction
        
        Returns:
            List of (path, total_time) tuples
        """
        # Priority queue: (estimated_total, counter, node, path, actual_cost)
        pq = [(0, 0, start, [start], 0)]
        found_paths = []
        visits = {}
        counter = 0
        
        while pq and len(found_paths) < k:
            est_total, _, current, path, actual_cost = heappop(pq)
            
            if current == goal:
                found_paths.append((path, round(actual_cost, 2)))
                continue
            
            # Limit revisits
            visits[current] = visits.get(current, 0) + 1
            if visits[current] > MAX_VISITS_PER_NODE:
                continue
            
            # Explore neighbors
            for neighbor, distance in self.graph.get(current, []):
                if neighbor in path:
                    continue
                
                # Predict traffic for this neighbor at given hour
                predicted_flow = self.traffic_predictor.predict(
                    self.current_model, None, hour
                )
                
                # Calculate edge travel time
                edge_time = self.tt_calc.calculate_travel_time(distance, predicted_flow)
                new_cost = actual_cost + edge_time
                
                counter += 1
                # Heuristic is 0 (uniform cost) - can be enhanced with Euclidean distance
                heappush(pq, (new_cost, counter, neighbor, path + [neighbor], new_cost))
        
        return found_paths