# # pathfinder.py
# """
# Pathfinding with 6 Search Algorithms (Reused from Assignment 2A)
# Algorithms: BFS, DFS, Greedy, A*, Dijkstra, Bidirectional A*
# Supports automatic algorithm selection based on graph characteristics

# Author: COS30019 Assignment 2B
# """

# from heapq import heappush, heappop
# import math
# from config import DEFAULT_K_ROUTES, MAX_VISITS_PER_NODE


# class PathFinder:
#     """
#     Unified pathfinding class supporting 6 different search algorithms.
#     Dynamically calculates edge costs using traffic predictions.
#     """
    
#     def __init__(self, graph, travel_time_calculator, traffic_predictor, coords=None):
#         """
#         Args:
#             graph: Dictionary of {node: [(neighbor, distance_km)]}
#             travel_time_calculator: TravelTimeCalculator instance
#             traffic_predictor: TrafficPredictor instance
#             coords: Dictionary of {node: (lat, lon)} for heuristics
#         """
#         self.graph = graph
#         self.tt_calc = travel_time_calculator
#         self.traffic_predictor = traffic_predictor
#         self.coords = coords or {}
#         self.current_model = 'lstm'
#         self.current_algorithm = 'astar'  # Default algorithm
        
#         # Algorithm metadata for display
#         self.algorithm_metadata = {
#             'bfs': {
#                 'name': 'Breadth-First Search (BFS)',
#                 'optimal': False,
#                 'complete': True,
#                 'time': 'O(V+E)',
#                 'space': 'O(V)',
#                 'best_for': 'Unweighted graphs, fewest hops'
#             },
#             'dfs': {
#                 'name': 'Depth-First Search (DFS)',
#                 'optimal': False,
#                 'complete': False,
#                 'time': 'O(V+E)',
#                 'space': 'O(depth)',
#                 'best_for': 'Memory-constrained environments'
#             },
#             'greedy': {
#                 'name': 'Greedy Best-First Search',
#                 'optimal': False,
#                 'complete': False,
#                 'time': 'O(V log V)',
#                 'space': 'O(V)',
#                 'best_for': 'Fast approximate routes'
#             },
#             'astar': {
#                 'name': 'A* Search',
#                 'optimal': True,
#                 'complete': True,
#                 'time': 'O(E log V)',
#                 'space': 'O(V)',
#                 'best_for': 'Best all-purpose, optimal paths'
#             },
#             'dijkstra': {
#                 'name': "Dijkstra's Algorithm",
#                 'optimal': True,
#                 'complete': True,
#                 'time': 'O(E log V)',
#                 'space': 'O(V)',
#                 'best_for': 'Weighted graphs, guaranteed optimal'
#             },
#             'bidirectional': {
#                 'name': 'Bidirectional A* Search',
#                 'optimal': True,
#                 'complete': True,
#                 'time': 'O(b^(d/2))',
#                 'space': 'O(b^(d/2))',
#                 'best_for': 'Large graphs, long distances'
#             }
#         }

#     # ============================================================
#     # SETTER METHODS
#     # ============================================================
    
#     def set_model(self, model_name):
#         """Set the active traffic prediction model (lstm/gru/xgboost)"""
#         self.current_model = model_name

#     def set_algorithm(self, algorithm_name):
#         """Set the active search algorithm"""
#         if algorithm_name in self.algorithm_metadata:
#             self.current_algorithm = algorithm_name
#             return True
#         return False
    
#     def set_coordinates(self, coords):
#         """Set coordinates for heuristic-based algorithms"""
#         self.coords = coords

#     # ============================================================
#     # CORE EDGE COST CALCULATION
#     # ============================================================
    
#     def _get_edge_cost(self, from_node, to_node, distance, hour):
#         """
#         Calculate dynamic edge cost based on predicted traffic.
#         This is the core function that uses ML predictions.
#         """
#         predicted_flow = self.traffic_predictor.predict(
#             self.current_model, None, hour
#         )
#         return self.tt_calc.calculate_travel_time(distance, predicted_flow)
    
#     def _calculate_path_time(self, path, hour):
#         """Calculate total travel time for a complete path"""
#         if len(path) < 2:
#             return 0
        
#         total_time = 0
#         for i in range(len(path) - 1):
#             from_node = str(path[i])
#             to_node = str(path[i+1])
            
#             # Find distance between these nodes
#             for neighbor, dist in self.graph.get(from_node, []):
#                 if neighbor == to_node:
#                     total_time += self._get_edge_cost(from_node, to_node, dist, hour)
#                     break
        
#         return round(total_time, 2)
    
#     def _heuristic(self, node, goal):
#         """
#         Euclidean distance heuristic for A* and Greedy.
#         Estimates remaining travel time assuming free-flow speed (60 km/h).
#         """
#         if not self.coords or node not in self.coords or goal not in self.coords:
#             return 0
        
#         lat1, lon1 = self.coords[node]
#         lat2, lon2 = self.coords[goal]
        
#         # Haversine distance
#         R = 6371
#         lat1_r, lon1_r = math.radians(lat1), math.radians(lon1)
#         lat2_r, lon2_r = math.radians(lat2), math.radians(lon2)
#         dlat = lat2_r - lat1_r
#         dlon = lon2_r - lon1_r
#         a = math.sin(dlat/2)**2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon/2)**2
#         c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
#         distance_km = R * c
        
#         # Convert to minutes at free-flow speed (60 km/h)
#         return (distance_km / 60) * 60

#     # ============================================================
#     # ALGORITHM 1: BFS (Breadth-First Search)
#     # ============================================================
    
#     def bfs(self, start, goal, hour=12):
#         """
#         Breadth-First Search
#         - Finds path with fewest edges
#         - Ignores edge weights during search
#         - Optimal for unweighted graphs
#         """
#         start_str = str(start)
#         goal_str = str(goal)
        
#         if start_str not in self.graph or goal_str not in self.graph:
#             return None, float('inf'), 0
        
#         from collections import deque
#         queue = deque([(start_str, [start_str])])
#         visited = {start_str}
#         nodes_explored = 0
        
#         while queue:
#             current, path = queue.popleft()
#             nodes_explored += 1
            
#             if current == goal_str:
#                 total_time = self._calculate_path_time([int(n) for n in path], hour)
#                 return [int(n) for n in path], total_time, nodes_explored
            
#             for neighbor, _ in self.graph.get(current, []):
#                 if neighbor not in visited:
#                     visited.add(neighbor)
#                     queue.append((neighbor, path + [neighbor]))
        
#         return None, float('inf'), nodes_explored

#     # ============================================================
#     # ALGORITHM 2: DFS (Depth-First Search)
#     # ============================================================
    
#     def dfs(self, start, goal, hour=12, max_depth=50):
#         """
#         Depth-First Search
#         - Memory efficient
#         - May not find shortest path
#         - Good for deep graphs with memory constraints
#         """
#         start_str = str(start)
#         goal_str = str(goal)
        
#         if start_str not in self.graph or goal_str not in self.graph:
#             return None, float('inf'), 0
        
#         stack = [(start_str, [start_str], 0)]
#         visited = set()
#         nodes_explored = 0
#         best_path = None
#         best_cost = float('inf')
        
#         while stack:
#             current, path, depth = stack.pop()
#             nodes_explored += 1
            
#             if depth > max_depth:
#                 continue
            
#             if current == goal_str:
#                 total_time = self._calculate_path_time([int(n) for n in path], hour)
#                 if total_time < best_cost:
#                     best_cost = total_time
#                     best_path = [int(n) for n in path]
#                 continue
            
#             if current in visited:
#                 continue
#             visited.add(current)
            
#             for neighbor, _ in self.graph.get(current, []):
#                 if neighbor not in path:
#                     stack.append((neighbor, path + [neighbor], depth + 1))
        
#         return best_path, best_cost, nodes_explored

#     # ============================================================
#     # ALGORITHM 3: Greedy Best-First Search
#     # ============================================================
    
#     def greedy(self, start, goal, hour=12):
#         """
#         Greedy Best-First Search
#         - Uses heuristic only, ignores actual path cost
#         - Fast but may not find optimal path
#         - Good for time-critical applications
#         """
#         start_str = str(start)
#         goal_str = str(goal)
        
#         if start_str not in self.graph or goal_str not in self.graph:
#             return None, float('inf'), 0
        
#         pq = [(self._heuristic(start_str, goal_str), start_str, [start_str])]
#         visited = set()
#         nodes_explored = 0
        
#         while pq:
#             _, current, path = heappop(pq)
#             nodes_explored += 1
            
#             if current in visited:
#                 continue
#             visited.add(current)
            
#             if current == goal_str:
#                 total_time = self._calculate_path_time([int(n) for n in path], hour)
#                 return [int(n) for n in path], total_time, nodes_explored
            
#             for neighbor, _ in self.graph.get(current, []):
#                 if neighbor not in visited:
#                     h = self._heuristic(neighbor, goal_str)
#                     heappush(pq, (h, neighbor, path + [neighbor]))
        
#         return None, float('inf'), nodes_explored

#     # ============================================================
#     # ALGORITHM 4: A* Search (Optimal + Heuristic)
#     # ============================================================
    
#     def astar(self, start, goal, hour=12):
#         """
#         A* Search Algorithm
#         - Combines actual cost + heuristic
#         - Optimal with admissible heuristic
#         - Best general-purpose algorithm
#         """
#         start_str = str(start)
#         goal_str = str(goal)
        
#         if start_str not in self.graph or goal_str not in self.graph:
#             return None, float('inf'), 0
        
#         pq = [(0, 0, start_str, [start_str], 0)]
#         visited = {}
#         nodes_explored = 0
#         counter = 0
        
#         while pq:
#             est_total, _, current, path, actual_cost = heappop(pq)
#             nodes_explored += 1
            
#             if current in visited and visited[current] <= actual_cost:
#                 continue
#             visited[current] = actual_cost
            
#             if current == goal_str:
#                 return [int(n) for n in path], round(actual_cost, 2), nodes_explored
            
#             for neighbor, distance in self.graph.get(current, []):
#                 if neighbor in path:
#                     continue
                
#                 edge_cost = self._get_edge_cost(current, neighbor, distance, hour)
#                 new_cost = actual_cost + edge_cost
#                 h = self._heuristic(neighbor, goal_str)
                
#                 counter += 1
#                 heappush(pq, (new_cost + h, counter, neighbor, path + [neighbor], new_cost))
        
#         return None, float('inf'), nodes_explored

#     # ============================================================
#     # ALGORITHM 5: Dijkstra (Uniform Cost Search)
#     # ============================================================
    
#     def dijkstra(self, start, goal, hour=12):
#         """
#         Dijkstra's Algorithm (Uniform Cost Search)
#         - Guarantees optimal path by minimizing total cost
#         - Does not use heuristic
#         - Good for weighted graphs
#         """
#         start_str = str(start)
#         goal_str = str(goal)
        
#         if start_str not in self.graph or goal_str not in self.graph:
#             return None, float('inf'), 0
        
#         pq = [(0, start_str, [start_str])]
#         visited = {}
#         nodes_explored = 0
        
#         while pq:
#             cost, current, path = heappop(pq)
#             nodes_explored += 1
            
#             if current in visited and visited[current] <= cost:
#                 continue
#             visited[current] = cost
            
#             if current == goal_str:
#                 return [int(n) for n in path], round(cost, 2), nodes_explored
            
#             for neighbor, distance in self.graph.get(current, []):
#                 if neighbor in path:
#                     continue
                
#                 edge_cost = self._get_edge_cost(current, neighbor, distance, hour)
#                 new_cost = cost + edge_cost
#                 heappush(pq, (new_cost, neighbor, path + [neighbor]))
        
#         return None, float('inf'), nodes_explored

#     # ============================================================
#     # ALGORITHM 6: Bidirectional A* Search
#     # ============================================================
    
#     def bidirectional_astar(self, start, goal, hour=12):
#         """
#         Bidirectional A* Search
#         - Searches from both start and goal simultaneously
#         - Much faster than standard A* for large graphs
#         - Optimal when heuristics are consistent
#         """
#         start_str = str(start)
#         goal_str = str(goal)
        
#         if start_str not in self.graph or goal_str not in self.graph:
#             return None, float('inf'), 0
        
#         # Forward search from start
#         forward_pq = [(self._heuristic(start_str, goal_str), 0, start_str, [start_str], 0)]
#         forward_visited = {start_str: (0, [start_str])}
        
#         # Backward search from goal
#         backward_pq = [(self._heuristic(goal_str, start_str), 0, goal_str, [goal_str], 0)]
#         backward_visited = {goal_str: (0, [goal_str])}
        
#         nodes_explored = 0
#         best_path = None
#         best_cost = float('inf')
#         counter = 0
        
#         while forward_pq and backward_pq:
#             # Expand forward
#             if forward_pq:
#                 _, _, current, path, cost = heappop(forward_pq)
#                 nodes_explored += 1
                
#                 # Check if meeting point found
#                 if current in backward_visited:
#                     back_cost, back_path = backward_visited[current]
#                     total_cost = cost + back_cost
#                     if total_cost < best_cost:
#                         best_cost = total_cost
#                         # Combine paths (remove duplicate meeting node)
#                         combined = path[:-1] + back_path[::-1]
#                         best_path = [int(n) for n in combined]
                
#                 if current in forward_visited and forward_visited[current][0] <= cost:
#                     continue
#                 forward_visited[current] = (cost, path)
                
#                 for neighbor, distance in self.graph.get(current, []):
#                     if neighbor in path:
#                         continue
#                     edge_cost = self._get_edge_cost(current, neighbor, distance, hour)
#                     new_cost = cost + edge_cost
#                     h = self._heuristic(neighbor, goal_str)
#                     counter += 1
#                     heappush(forward_pq, (new_cost + h, counter, neighbor, path + [neighbor], new_cost))
            
#             # Expand backward
#             if backward_pq:
#                 _, _, current, path, cost = heappop(backward_pq)
#                 nodes_explored += 1
                
#                 if current in forward_visited:
#                     forward_cost, forward_path = forward_visited[current]
#                     total_cost = forward_cost + cost
#                     if total_cost < best_cost:
#                         best_cost = total_cost
#                         combined = forward_path[:-1] + path[::-1]
#                         best_path = [int(n) for n in combined]
                
#                 if current in backward_visited and backward_visited[current][0] <= cost:
#                     continue
#                 backward_visited[current] = (cost, path)
                
#                 for neighbor, distance in self.graph.get(current, []):
#                     if neighbor in path:
#                         continue
#                     edge_cost = self._get_edge_cost(current, neighbor, distance, hour)
#                     new_cost = cost + edge_cost
#                     h = self._heuristic(neighbor, start_str)
#                     counter += 1
#                     heappush(backward_pq, (new_cost + h, counter, neighbor, path + [neighbor], new_cost))
            
#             # Early termination if best path found and cannot be improved
#             if best_path and forward_pq and backward_pq:
#                 forward_best = forward_pq[0][0]
#                 backward_best = backward_pq[0][0]
#                 if forward_best + backward_best >= best_cost:
#                     break
        
#         if best_path:
#             total_time = self._calculate_path_time(best_path, hour)
#             return best_path, total_time, nodes_explored
        
#         return None, float('inf'), nodes_explored

#     # ============================================================
#     # UNIFIED PATH FINDING INTERFACE
#     # ============================================================
    
#     def find_path(self, start, goal, hour=12):
#         """
#         Find a single path using the currently selected algorithm.
        
#         Returns:
#             (path, cost, nodes_explored) tuple
#         """
#         algorithm_map = {
#             'bfs': self.bfs,
#             'dfs': self.dfs,
#             'greedy': self.greedy,
#             'astar': self.astar,
#             'dijkstra': self.dijkstra,
#             'bidirectional': self.bidirectional_astar
#         }
        
#         algorithm_func = algorithm_map.get(self.current_algorithm, self.astar)
#         return algorithm_func(start, goal, hour)

#     def find_top_k_paths(self, start, goal, k=DEFAULT_K_ROUTES, hour=12):
#         """
#         Find top-K paths using the selected algorithm.
#         For K=1, returns the best path.
#         For K>1, finds best path then uses alternative algorithms for variety.
        
#         Returns:
#             List of (path, total_time) tuples
#         """
#         # Get the best path first
#         best_path, best_cost, nodes = self.find_path(start, goal, hour)
        
#         if not best_path:
#             return []
        
#         paths = [(best_path, best_cost)]
        
#         # If more paths requested, try alternative algorithms
#         if k > 1:
#             alternative_algorithms = []
#             for algo in ['dijkstra', 'greedy', 'bfs']:
#                 if algo != self.current_algorithm:
#                     alternative_algorithms.append(algo)
            
#             for alt_algo in alternative_algorithms[:k-1]:
#                 # Temporarily switch algorithm
#                 original_algo = self.current_algorithm
#                 self.set_algorithm(alt_algo)
#                 alt_path, alt_cost, _ = self.find_path(start, goal, hour)
#                 self.set_algorithm(original_algo)
                
#                 # Add if valid and not duplicate
#                 if alt_path and alt_path not in [p for p, _ in paths]:
#                     paths.append((alt_path, alt_cost))
            
#             # Sort by cost
#             paths.sort(key=lambda x: x[1])
        
#         return paths[:k]

#     # ============================================================
#     # AUTO-SELECTION FEATURE
#     # ============================================================
    
#     def auto_select_algorithm(self, start=None, goal=None, time_pressure='medium', preference=None):
#         """
#         Automatically select the best algorithm based on graph characteristics.
        
#         Args:
#             start: Origin (optional, for distance estimation)
#             goal: Destination (optional)
#             time_pressure: 'low', 'medium', 'high'
#             preference: 'fast', 'optimal', 'memory_efficient'
        
#         Returns:
#             (selected_algorithm, reason, stats)
#         """
#         graph_stats = self.get_graph_info()
#         graph_size = graph_stats['total_nodes']
#         avg_degree = graph_stats['total_edges'] * 2 / max(graph_size, 1)
        
#         # Decision tree for algorithm selection
#         recommendations = []
        
#         # Rule 1: Very large graph (> 100 nodes)
#         if graph_size > 100:
#             recommendations.append(('bidirectional', f'Large graph ({graph_size} nodes) → Bidirectional A* is fastest'))
        
#         # Rule 2: High time pressure
#         if time_pressure == 'high':
#             recommendations.append(('greedy', 'High time pressure → Greedy for fastest response'))
        
#         # Rule 3: User preference for fast
#         if preference == 'fast':
#             recommendations.append(('greedy', 'User requested fastest → Greedy Best-First'))
        
#         # Rule 4: User preference for optimal
#         if preference == 'optimal':
#             recommendations.append(('astar', 'User requested optimal → A*'))
        
#         # Rule 5: User preference for memory efficient
#         if preference == 'memory_efficient':
#             recommendations.append(('dfs', 'Memory efficient → DFS'))
        
#         # Rule 6: Small graph with high connectivity
#         if graph_size < 50 and avg_degree > 3:
#             recommendations.append(('dijkstra', 'Small, well-connected graph → Dijkstra works well'))
        
#         # Rule 7: Default
#         if not recommendations:
#             recommendations.append(('astar', 'Default recommendation → A* is balanced'))
        
#         # Get best recommendation
#         algorithm, reason = recommendations[0]
        
#         # Set the algorithm
#         self.set_algorithm(algorithm)
        
#         return algorithm, reason, graph_stats
    
#     def get_algorithm_ranking(self, start=None, goal=None):
#         """
#         Rank all algorithms by estimated performance.
#         Returns list of (algorithm_name, score, reason)
#         """
#         graph_stats = self.get_graph_info()
#         graph_size = graph_stats['total_nodes']
#         avg_degree = graph_stats['total_edges'] * 2 / max(graph_size, 1)
        
#         rankings = []
        
#         # Bidirectional A*
#         score = 100
#         if graph_size > 100:
#             score += 20
#         rankings.append(('bidirectional', score, 'Excellent for large graphs'))
        
#         # A*
#         score = 95
#         rankings.append(('astar', score, 'Best all-purpose, optimal paths'))
        
#         # Dijkstra
#         score = 85
#         if avg_degree < 4:
#             score += 10
#         rankings.append(('dijkstra', score, 'Guaranteed optimal, good for sparse graphs'))
        
#         # Greedy
#         score = 70
#         rankings.append(('greedy', score, 'Fastest, but may not find optimal path'))
        
#         # BFS
#         score = 60
#         rankings.append(('bfs', score, 'Simple, good for unweighted exploration'))
        
#         # DFS
#         score = 50
#         rankings.append(('dfs', score, 'Memory efficient, may not find shortest path'))
        
#         rankings.sort(key=lambda x: x[1], reverse=True)
#         return rankings

#     # ============================================================
#     # UTILITY METHODS
#     # ============================================================
    
#     def get_graph_info(self):
#         """Return information about the graph for debugging and auto-selection"""
#         total_nodes = len(self.graph)
#         total_edges = sum(len(neighbors) for neighbors in self.graph.values()) // 2
#         isolated_nodes = sum(1 for neighbors in self.graph.values() if not neighbors)
        
#         # Calculate average degree
#         avg_degree = (total_edges * 2) / max(total_nodes, 1)
        
#         return {
#             'total_nodes': total_nodes,
#             'total_edges': total_edges,
#             'isolated_nodes': isolated_nodes,
#             'avg_degree': round(avg_degree, 2)
#         }
    
#     def get_algorithm_list(self):
#         """Return list of available algorithm names"""
#         return list(self.algorithm_metadata.keys())
    
#     def get_algorithm_info(self, algorithm=None):
#         """Return detailed information about algorithm(s)"""
#         if algorithm:
#             return self.algorithm_metadata.get(algorithm, {})
#         return self.algorithm_metadata
    
#     def get_current_algorithm_info(self):
#         """Return info about currently selected algorithm"""
#         return self.algorithm_metadata.get(self.current_algorithm, {})
    # pathfinder.py
"""
Pathfinding with 6 Search Algorithms (Reused from Assignment 2A)
Algorithms: BFS, DFS, Greedy, A*, Dijkstra, Bidirectional A*
"""

from heapq import heappush, heappop
import math
from config import DEFAULT_K_ROUTES, MAX_VISITS_PER_NODE


class PathFinder:
    """
    Unified pathfinding class supporting 6 different search algorithms.
    """
    
    def __init__(self, graph, travel_time_calculator, traffic_predictor, coords=None):
        self.graph = graph
        self.tt_calc = travel_time_calculator
        self.traffic_predictor = traffic_predictor
        self.coords = coords or {}
        self.current_model = 'lstm'
        self.current_algorithm = 'astar'
        
        # Algorithm mapping
        self.algorithms = {
            'bfs': self._bfs,
            'dfs': self._dfs,
            'greedy': self._greedy,
            'astar': self._astar,
            'dijkstra': self._dijkstra,
            'bidirectional': self._bidirectional_astar
        }

    def set_model(self, model_name):
        self.current_model = model_name

    def set_algorithm(self, algorithm_name):
        if algorithm_name in self.algorithms:
            self.current_algorithm = algorithm_name
            return True
        return False
    
    def set_coordinates(self, coords):
        self.coords = coords

    def _get_edge_cost(self, from_node, to_node, distance, hour):
        predicted_flow = self.traffic_predictor.predict(self.current_model, None, hour)
        return self.tt_calc.calculate_travel_time(distance, predicted_flow)
    
    def _calculate_path_time(self, path, hour):
        if len(path) < 2:
            return 0
        total_time = 0
        for i in range(len(path) - 1):
            from_node = str(path[i])
            to_node = str(path[i+1])
            for neighbor, dist in self.graph.get(from_node, []):
                if neighbor == to_node:
                    total_time += self._get_edge_cost(from_node, to_node, dist, hour)
                    break
        return round(total_time, 2)
    
    def _heuristic(self, node, goal):
        if not self.coords or node not in self.coords or goal not in self.coords:
            return 0
        lat1, lon1 = self.coords[node]
        lat2, lon2 = self.coords[goal]
        R = 6371
        lat1_r, lon1_r = math.radians(lat1), math.radians(lon1)
        lat2_r, lon2_r = math.radians(lat2), math.radians(lon2)
        dlat = lat2_r - lat1_r
        dlon = lon2_r - lon1_r
        a = math.sin(dlat/2)**2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance_km = R * c
        return (distance_km / 60) * 60

    # ============================================================
    # ALGORITHM 1: BFS
    # ============================================================
    def _bfs(self, start, goal, hour=12):
        from collections import deque
        start_str, goal_str = str(start), str(goal)
        if start_str not in self.graph or goal_str not in self.graph:
            return None, float('inf'), 0
        
        queue = deque([(start_str, [start_str])])
        visited = {start_str}
        nodes_explored = 0
        
        while queue:
            current, path = queue.popleft()
            nodes_explored += 1
            if current == goal_str:
                total_time = self._calculate_path_time([int(n) for n in path], hour)
                return [int(n) for n in path], total_time, nodes_explored
            for neighbor, _ in self.graph.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        return None, float('inf'), nodes_explored

    # ============================================================
    # ALGORITHM 2: DFS
    # ============================================================
    def _dfs(self, start, goal, hour=12, max_depth=50):
        start_str, goal_str = str(start), str(goal)
        if start_str not in self.graph or goal_str not in self.graph:
            return None, float('inf'), 0
        
        stack = [(start_str, [start_str], 0)]
        visited = set()
        nodes_explored = 0
        best_path, best_cost = None, float('inf')
        
        while stack:
            current, path, depth = stack.pop()
            nodes_explored += 1
            if depth > max_depth:
                continue
            if current == goal_str:
                total_time = self._calculate_path_time([int(n) for n in path], hour)
                if total_time < best_cost:
                    best_cost, best_path = total_time, [int(n) for n in path]
                continue
            if current in visited:
                continue
            visited.add(current)
            for neighbor, _ in self.graph.get(current, []):
                if neighbor not in path:
                    stack.append((neighbor, path + [neighbor], depth + 1))
        return best_path, best_cost, nodes_explored

    # ============================================================
    # ALGORITHM 3: Greedy
    # ============================================================
    def _greedy(self, start, goal, hour=12):
        start_str, goal_str = str(start), str(goal)
        if start_str not in self.graph or goal_str not in self.graph:
            return None, float('inf'), 0
        
        pq = [(self._heuristic(start_str, goal_str), start_str, [start_str])]
        visited = set()
        nodes_explored = 0
        
        while pq:
            _, current, path = heappop(pq)
            nodes_explored += 1
            if current in visited:
                continue
            visited.add(current)
            if current == goal_str:
                total_time = self._calculate_path_time([int(n) for n in path], hour)
                return [int(n) for n in path], total_time, nodes_explored
            for neighbor, _ in self.graph.get(current, []):
                if neighbor not in visited:
                    h = self._heuristic(neighbor, goal_str)
                    heappush(pq, (h, neighbor, path + [neighbor]))
        return None, float('inf'), nodes_explored

    # ============================================================
    # ALGORITHM 4: A* Search
    # ============================================================
    def _astar(self, start, goal, hour=12):
        start_str, goal_str = str(start), str(goal)
        if start_str not in self.graph or goal_str not in self.graph:
            return None, float('inf'), 0
        
        pq = [(0, 0, start_str, [start_str], 0)]
        visited = {}
        nodes_explored = 0
        counter = 0
        
        while pq:
            est_total, _, current, path, actual_cost = heappop(pq)
            nodes_explored += 1
            if current in visited and visited[current] <= actual_cost:
                continue
            visited[current] = actual_cost
            if current == goal_str:
                return [int(n) for n in path], round(actual_cost, 2), nodes_explored
            for neighbor, distance in self.graph.get(current, []):
                if neighbor in path:
                    continue
                edge_cost = self._get_edge_cost(current, neighbor, distance, hour)
                new_cost = actual_cost + edge_cost
                h = self._heuristic(neighbor, goal_str)
                counter += 1
                heappush(pq, (new_cost + h, counter, neighbor, path + [neighbor], new_cost))
        return None, float('inf'), nodes_explored

    # ============================================================
    # ALGORITHM 5: Dijkstra
    # ============================================================
    def _dijkstra(self, start, goal, hour=12):
        start_str, goal_str = str(start), str(goal)
        if start_str not in self.graph or goal_str not in self.graph:
            return None, float('inf'), 0
        
        pq = [(0, start_str, [start_str])]
        visited = {}
        nodes_explored = 0
        
        while pq:
            cost, current, path = heappop(pq)
            nodes_explored += 1
            if current in visited and visited[current] <= cost:
                continue
            visited[current] = cost
            if current == goal_str:
                return [int(n) for n in path], round(cost, 2), nodes_explored
            for neighbor, distance in self.graph.get(current, []):
                if neighbor in path:
                    continue
                edge_cost = self._get_edge_cost(current, neighbor, distance, hour)
                new_cost = cost + edge_cost
                heappush(pq, (new_cost, neighbor, path + [neighbor]))
        return None, float('inf'), nodes_explored

    # ============================================================
    # ALGORITHM 6: Bidirectional A*
    # ============================================================
    def _bidirectional_astar(self, start, goal, hour=12):
        start_str, goal_str = str(start), str(goal)
        if start_str not in self.graph or goal_str not in self.graph:
            return None, float('inf'), 0
        
        forward_pq = [(self._heuristic(start_str, goal_str), 0, start_str, [start_str], 0)]
        forward_visited = {start_str: (0, [start_str])}
        backward_pq = [(self._heuristic(goal_str, start_str), 0, goal_str, [goal_str], 0)]
        backward_visited = {goal_str: (0, [goal_str])}
        
        nodes_explored = 0
        best_path = None
        best_cost = float('inf')
        counter = 0
        
        while forward_pq and backward_pq:
            if forward_pq:
                _, _, current, path, cost = heappop(forward_pq)
                nodes_explored += 1
                if current in backward_visited:
                    back_cost, back_path = backward_visited[current]
                    total_cost = cost + back_cost
                    if total_cost < best_cost:
                        best_cost = total_cost
                        best_path = [int(n) for n in (path[:-1] + back_path[::-1])]
                if current in forward_visited and forward_visited[current][0] <= cost:
                    continue
                forward_visited[current] = (cost, path)
                for neighbor, distance in self.graph.get(current, []):
                    if neighbor in path:
                        continue
                    edge_cost = self._get_edge_cost(current, neighbor, distance, hour)
                    new_cost = cost + edge_cost
                    h = self._heuristic(neighbor, goal_str)
                    counter += 1
                    heappush(forward_pq, (new_cost + h, counter, neighbor, path + [neighbor], new_cost))
            
            if backward_pq:
                _, _, current, path, cost = heappop(backward_pq)
                nodes_explored += 1
                if current in forward_visited:
                    forward_cost, forward_path = forward_visited[current]
                    total_cost = forward_cost + cost
                    if total_cost < best_cost:
                        best_cost = total_cost
                        best_path = [int(n) for n in (forward_path[:-1] + path[::-1])]
                if current in backward_visited and backward_visited[current][0] <= cost:
                    continue
                backward_visited[current] = (cost, path)
                for neighbor, distance in self.graph.get(current, []):
                    if neighbor in path:
                        continue
                    edge_cost = self._get_edge_cost(current, neighbor, distance, hour)
                    new_cost = cost + edge_cost
                    h = self._heuristic(neighbor, start_str)
                    counter += 1
                    heappush(backward_pq, (new_cost + h, counter, neighbor, path + [neighbor], new_cost))
            
            if best_path and forward_pq and backward_pq:
                if forward_pq[0][0] + backward_pq[0][0] >= best_cost:
                    break
        
        if best_path:
            total_time = self._calculate_path_time(best_path, hour)
            return best_path, total_time, nodes_explored
        return None, float('inf'), nodes_explored

    # ============================================================
    # PUBLIC METHODS
    # ============================================================
    
    def find_path(self, start, goal, hour=12):
        """Find a single path using the currently selected algorithm"""
        algorithm_func = self.algorithms.get(self.current_algorithm, self._astar)
        return algorithm_func(start, goal, hour)


    # pathfinder.py (replace the find_top_k_paths method)

    def find_top_k_paths(self, start, goal, k=DEFAULT_K_ROUTES, hour=12):
        """
        Find top-K paths using multiple strategies:
        1. Primary algorithm (user selected or auto-selected)
        2. Alternative algorithms for variety
        """
        all_paths = []
        
        # Get paths from primary algorithm
        primary_path, primary_cost, _ = self.find_path(start, goal, hour)
        if primary_path:
            all_paths.append((primary_path, primary_cost))
        
        # Try alternative algorithms to get up to K routes
        alternative_algorithms = ['dijkstra', 'greedy', 'bfs', 'bidirectional']
        for alt_algo in alternative_algorithms:
            if alt_algo != self.current_algorithm and len(all_paths) < k:
                # Temporarily switch algorithm
                original_algo = self.current_algorithm
                self.set_algorithm(alt_algo)
                alt_path, alt_cost, _ = self.find_path(start, goal, hour)
                self.set_algorithm(original_algo)
                
                # Add if valid and not duplicate
                if alt_path and alt_path not in [p for p, _ in all_paths]:
                    all_paths.append((alt_path, alt_cost))
        
        # If still not enough paths, try variations by avoiding intermediate nodes
        if len(all_paths) < k and primary_path:
            for i in range(1, len(primary_path) - 1):
                if len(all_paths) >= k:
                    break
                # Block a node and find alternative
                blocked_node = primary_path[i]
                original_graph = self.graph.copy()
                # Temporarily remove the node
                self.graph = {k: [n for n in v if n[0] != blocked_node] 
                            for k, v in self.graph.items()}
                alt_path, alt_cost, _ = self.find_path(start, goal, hour)
                self.graph = original_graph
                
                if alt_path and alt_path not in [p for p, _ in all_paths]:
                    all_paths.append((alt_path, alt_cost))
        
        # Sort by cost and return top K
        all_paths.sort(key=lambda x: x[1])
        return all_paths[:k]
    
    # def find_top_k_paths(self, start, goal, k=DEFAULT_K_ROUTES, hour=12):
    #     """Find top-K paths using the selected algorithm"""
    #     best_path, best_cost, _ = self.find_path(start, goal, hour)
    #     if not best_path:
    #         return []
    #     paths = [(best_path, best_cost)]
        
    #     if k > 1:
    #         alternatives = ['dijkstra', 'greedy', 'bfs']
    #         original_algo = self.current_algorithm
    #         for alt_algo in alternatives:
    #             if alt_algo != original_algo and len(paths) < k:
    #                 self.set_algorithm(alt_algo)
    #                 alt_path, alt_cost, _ = self.find_path(start, goal, hour)
    #                 if alt_path and alt_path not in [p for p, _ in paths]:
    #                     paths.append((alt_path, alt_cost))
    #         self.set_algorithm(original_algo)
    #         paths.sort(key=lambda x: x[1])
        
    #     return paths[:k]

    def get_graph_info(self):
        total_nodes = len(self.graph)
        total_edges = sum(len(neighbors) for neighbors in self.graph.values()) // 2
        return {
            'total_nodes': total_nodes,
            'total_edges': total_edges,
            'isolated_nodes': sum(1 for n in self.graph.values() if not n)
        }
    
    def get_algorithm_list(self):
        return list(self.algorithms.keys())
    
    def get_algorithm_info(self):
        return {
            'bfs': {'name': 'BFS', 'optimal': False},
            'dfs': {'name': 'DFS', 'optimal': False},
            'greedy': {'name': 'Greedy', 'optimal': False},
            'astar': {'name': 'A*', 'optimal': True},
            'dijkstra': {'name': 'Dijkstra', 'optimal': True},
            'bidirectional': {'name': 'Bidirectional A*', 'optimal': True}
        }
        
    def get_algorithm_comparison_table(self):
        """Generate a comparison table of all algorithms for display"""
        table = []
        for algo, info in self.algorithm_metadata.items():
            table.append({
                'algorithm': algo,
                'name': info['name'],
                'optimal': '✓' if info['optimal'] else '✗',
                'complete': '✓' if info['complete'] else '✗',
                'time': info['time'],
                'space': info['space'],
                'best_for': info['best_for']
            })
        return table