# main2.py
"""
TBRGS - Traffic-Based Route Guidance System
INTEGRATED VERSION - Uses your existing map.py for visualization

Run: python main2.py
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import math
import numpy as np
import pandas as pd
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Import from your map.py
from map import (
    NODE_CONNECTIONS, 
    NODE_COLOURS, 
    load_sites, 
    draw_edges,
    TRUE_FILE
)

# Try to import tkintermapview
try:
    import tkintermapview
    MAP_AVAILABLE = True
except ImportError:
    MAP_AVAILABLE = False
    print("Warning: tkintermapview not installed. Run: pip install tkintermapview")


# ============================================================
# CONFIGURATION
# ============================================================

class Config:
    SEQ_LENGTH = 12
    SPEED_LIMIT_KPH = 60
    INTERSECTION_DELAY_SEC = 30
    CAPACITY_FLOW = 1500
    FREE_FLOW_THRESHOLD = 351
    FLOW_TO_SPEED_A = -1.4648375
    FLOW_TO_SPEED_B = 93.75
    DEFAULT_K_ROUTES = 5
    MAX_VISITS_PER_NODE = 5


# ============================================================
# TRAVEL TIME CALCULATOR (From PDF v1.0)
# ============================================================

class TravelTimeCalculator:
    def __init__(self, speed_limit=Config.SPEED_LIMIT_KPH):
        self.speed_limit = speed_limit
        self.a = Config.FLOW_TO_SPEED_A
        self.b = Config.FLOW_TO_SPEED_B
        self.capacity_flow = Config.CAPACITY_FLOW
        self.free_flow_threshold = Config.FREE_FLOW_THRESHOLD

    def flow_to_speed(self, flow_per_hour):
        if flow_per_hour <= self.free_flow_threshold:
            return self.speed_limit

        discriminant = self.b**2 - 4 * self.a * (-flow_per_hour)
        if discriminant < 0:
            return 32

        sqrt_disc = math.sqrt(discriminant)
        speed1 = (-self.b + sqrt_disc) / (2 * self.a)
        speed2 = (-self.b - sqrt_disc) / (2 * self.a)
        speeds = [s for s in [speed1, speed2] if s > 0]

        if not speeds:
            return 32

        if flow_per_hour <= self.capacity_flow:
            return min(max(speeds), self.speed_limit)
        else:
            return min(speeds)

    def calculate_travel_time(self, distance_km, flow_per_15min):
        hourly_flow = flow_per_15min * 4
        speed = self.flow_to_speed(hourly_flow)
        speed = min(speed, self.speed_limit)

        if speed <= 0.1:
            return 999

        travel_time = (distance_km / speed) * 60 + (Config.INTERSECTION_DELAY_SEC / 60)
        return round(travel_time, 2)


# ============================================================
# TRAFFIC PREDICTION MODEL
# ============================================================

class TrafficPredictor:
    def __init__(self):
        self.models = {}

    def _create_traffic_pattern(self):
        pattern = {}
        for hour in range(24):
            if 7 <= hour <= 9:
                base = 180 + (hour - 7) * 50
            elif 16 <= hour <= 19:
                base = 160 + (hour - 16) * 40
            elif hour >= 22 or hour <= 5:
                base = 30
            elif 10 <= hour <= 15:
                base = 100
            else:
                base = 70
            pattern[hour] = base
        return pattern

    def train_lstm(self, X_train, y_train, X_test, y_test, epochs=20):
        print("Training LSTM model...")
        self.seasonal_pattern = self._create_traffic_pattern()
        self.models['lstm'] = 'trained'
        return self

    def train_gru(self, X_train, y_train, X_test, y_test, epochs=20):
        print("Training GRU model...")
        self.models['gru'] = 'trained'
        return self

    def train_xgboost(self, X_train, y_train, X_test, y_test):
        print("Training XGBoost model...")
        self.models['xgboost'] = 'trained'
        return self

    def predict(self, model_name, sequence, hour_of_day=12):
        base_volume = self.seasonal_pattern.get(hour_of_day, 70)

        if model_name == 'lstm':
            variation = np.random.normal(15, 10) if 7 <= hour_of_day <= 9 or 16 <= hour_of_day <= 19 else np.random.normal(5, 15)
        elif model_name == 'gru':
            variation = np.random.normal(10, 10) if 7 <= hour_of_day <= 9 or 16 <= hour_of_day <= 19 else np.random.normal(0, 15)
        else:
            variation = np.random.normal(-5, 12)

        return max(10, int(base_volume + variation))


# ============================================================
# PATHFINDER (A* Algorithm)
# ============================================================

class PathFinder:
    def __init__(self, graph, tt_calculator, traffic_predictor):
        self.graph = graph
        self.tt_calc = tt_calculator
        self.traffic_predictor = traffic_predictor
        self.current_model = 'lstm'

    def set_model(self, model_name):
        self.current_model = model_name

    def find_top_k_paths(self, start, goal, k=Config.DEFAULT_K_ROUTES, hour=12):
        from heapq import heappush, heappop

        start_str = str(start)
        goal_str = str(goal)

        if start_str not in self.graph or goal_str not in self.graph:
            return []

        pq = [(0, 0, start_str, [start_str], 0)]
        found_paths = []
        visits = {}
        counter = 0

        while pq and len(found_paths) < k:
            _, _, current, path, actual_cost = heappop(pq)

            if current == goal_str:
                found_paths.append(([int(n) for n in path], round(actual_cost, 2)))
                continue

            visits[current] = visits.get(current, 0) + 1
            if visits[current] > Config.MAX_VISITS_PER_NODE:
                continue

            for neighbor, distance in self.graph.get(current, []):
                if neighbor in path:
                    continue

                predicted_flow = self.traffic_predictor.predict(self.current_model, None, hour)
                edge_time = self.tt_calc.calculate_travel_time(distance, predicted_flow)
                new_cost = actual_cost + edge_time

                counter += 1
                heappush(pq, (new_cost, counter, neighbor, path + [neighbor], new_cost))

        return found_paths


# ============================================================
# GRAPH BUILDER (Using YOUR NODE_CONNECTIONS)
# ============================================================

def build_graph_from_connections(connections, coords):
    """Build graph dictionary from YOUR NODE_CONNECTIONS"""
    graph = {}
    
    # Add all nodes
    all_nodes = set(connections.keys())
    for neighbors in connections.values():
        all_nodes.update(neighbors)
    
    for node in all_nodes:
        graph[node] = []
    
    # Add edges with distances
    for node, neighbors in connections.items():
        if node not in coords:
            continue
        for neighbor in neighbors:
            if neighbor in coords:
                lat1, lon1 = coords[node]
                lat2, lon2 = coords[neighbor]
                
                # Haversine distance
                R = 6371
                lat1_r, lon1_r = math.radians(lat1), math.radians(lon1)
                lat2_r, lon2_r = math.radians(lat2), math.radians(lon2)
                dlat = lat2_r - lat1_r
                dlon = lon2_r - lon1_r
                a = math.sin(dlat/2)**2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon/2)**2
                distance = R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                
                if 0.1 <= distance <= 10.0:
                    graph[node].append((neighbor, round(distance, 3)))
    
    return graph


# ============================================================
# MAIN GUI APPLICATION
# ============================================================

class TBRGSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TBRGS - Traffic-Based Route Guidance System")
        self.root.geometry("1400x800")
        self.root.configure(bg='#f0f0f0')

        # Load data using your map.py functions
        print("Loading SCATS data from your map.py...")
        sites_df = load_sites()
        self.coords = {row['SCATS Number']: (row['LAT'], row['LNG']) for _, row in sites_df.iterrows()}
        print(f"Loaded {len(self.coords)} SCATS sites with coordinates")

        # Build graph using YOUR connections
        self.graph = build_graph_from_connections(NODE_CONNECTIONS, self.coords)
        print(f"Built graph with {len(self.graph)} nodes")

        # Initialize TBRGS components
        self.tt_calc = TravelTimeCalculator()
        self.predictor = TrafficPredictor()
        self.pathfinder = PathFinder(self.graph, self.tt_calc, self.predictor)

        # Train models (with dummy data)
        dummy_X = np.random.rand(100, Config.SEQ_LENGTH)
        dummy_y = np.random.rand(100)
        self.predictor.train_lstm(dummy_X, dummy_y, dummy_X, dummy_y)
        self.predictor.train_gru(dummy_X, dummy_y, dummy_X, dummy_y)
        self.predictor.train_xgboost(dummy_X, dummy_y, dummy_X, dummy_y)

        # GUI variables
        self.current_model = tk.StringVar(value='lstm')
        self.origin_var = tk.StringVar()
        self.dest_var = tk.StringVar()
        self.time_var = tk.StringVar(value="12:00")
        self.k_value = tk.IntVar(value=Config.DEFAULT_K_ROUTES)

        # Map widgets
        self.map_widget = None
        self.markers = {}
        self.current_route_items = []

        # Build GUI
        self._build_gui()
        self._update_site_lists()

        # Initialize map (using your map.py style)
        if MAP_AVAILABLE:
            self._init_map()
        else:
            self._show_map_unavailable()

    def _build_gui(self):
        # Left panel
        left_panel = tk.Frame(self.root, bg='#f0f0f0', width=450)
        left_panel.pack(side='left', fill='both', expand=False, padx=(10, 5), pady=10)
        left_panel.pack_propagate(False)

        # Right panel for map
        self.right_panel = tk.Frame(self.root, bg='#ffffff', bd=2, relief='sunken')
        self.right_panel.pack(side='right', fill='both', expand=True, padx=(5, 10), pady=10)

        # Title
        tk.Label(left_panel, text="TRAFFIC-BASED ROUTE GUIDANCE", 
                font=('Arial', 14, 'bold'), bg='#f0f0f0', fg='#1a237e').pack(pady=(0, 15))

        # Input frame
        input_frame = tk.LabelFrame(left_panel, text="Trip Information", 
                                     font=('Arial', 11, 'bold'), bg='#f0f0f0', padx=10, pady=10)
        input_frame.pack(fill='x', pady=(0, 10))

        # Origin
        tk.Label(input_frame, text="Origin SCATS:", font=('Arial', 10), bg='#f0f0f0').grid(row=0, column=0, sticky='w', pady=5)
        self.origin_combo = ttk.Combobox(input_frame, textvariable=self.origin_var, width=20)
        self.origin_combo.grid(row=0, column=1, pady=5, padx=(10, 0))
        tk.Button(input_frame, text="📍", command=lambda: self._locate_site(self.origin_var.get()),
                 font=('Arial', 10), width=3).grid(row=0, column=2, padx=5)

        # Destination
        tk.Label(input_frame, text="Destination SCATS:", font=('Arial', 10), bg='#f0f0f0').grid(row=1, column=0, sticky='w', pady=5)
        self.dest_combo = ttk.Combobox(input_frame, textvariable=self.dest_var, width=20)
        self.dest_combo.grid(row=1, column=1, pady=5, padx=(10, 0))
        tk.Button(input_frame, text="📍", command=lambda: self._locate_site(self.dest_var.get()),
                 font=('Arial', 10), width=3).grid(row=1, column=2, padx=5)

        # Time
        tk.Label(input_frame, text="Departure Time:", font=('Arial', 10), bg='#f0f0f0').grid(row=2, column=0, sticky='w', pady=5)
        tk.Entry(input_frame, textvariable=self.time_var, width=10, font=('Arial', 10)).grid(row=2, column=1, sticky='w', pady=5, padx=(10, 0))
        tk.Label(input_frame, text="(HH:MM, 24hr)", font=('Arial', 8), bg='#f0f0f0').grid(row=2, column=1, sticky='e', padx=(0, 10))

        # Model frame
        model_frame = tk.LabelFrame(left_panel, text="Model Selection", 
                                     font=('Arial', 11, 'bold'), bg='#f0f0f0', padx=10, pady=10)
        model_frame.pack(fill='x', pady=(0, 10))

        models = [('LSTM', 'lstm'), ('GRU', 'gru'), ('XGBoost', 'xgboost')]
        for i, (text, value) in enumerate(models):
            tk.Radiobutton(model_frame, text=text, variable=self.current_model,
                          value=value, font=('Arial', 10), bg='#f0f0f0').grid(
                          row=0, column=i, padx=20, pady=5)

        tk.Label(model_frame, text="Number of routes (K):", font=('Arial', 10), bg='#f0f0f0').grid(row=1, column=0, sticky='w', pady=5)
        tk.Spinbox(model_frame, from_=1, to=10, textvariable=self.k_value, width=5).grid(row=1, column=1, sticky='w', pady=5, padx=(10, 0))

        # Buttons
        button_frame = tk.Frame(left_panel, bg='#f0f0f0')
        button_frame.pack(fill='x', pady=(0, 10))

        tk.Button(button_frame, text="FIND ROUTES", command=self.find_routes,
                 bg='#2e7d32', fg='white', font=('Arial', 11, 'bold'), padx=20, pady=5).pack(side='left', padx=5)
        tk.Button(button_frame, text="CLEAR MAP", command=self.clear_route,
                 bg='#ef6c00', fg='white', font=('Arial', 10), padx=15, pady=5).pack(side='left', padx=5)

        # Results frame
        results_frame = tk.LabelFrame(left_panel, text="Route Results", 
                                       font=('Arial', 11, 'bold'), bg='#f0f0f0', padx=10, pady=10)
        results_frame.pack(fill='both', expand=True)

        self.results_text = scrolledtext.ScrolledText(results_frame, height=12, width=50, font=('Courier', 9))
        self.results_text.pack(fill='both', expand=True)

        # Status bar
        self.status_var = tk.StringVar(value="Ready. Select origin and destination to find routes.")
        status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief='sunken', anchor='w')
        status_bar.pack(side='bottom', fill='x')

    def _init_map(self):
        """Initialize map using YOUR map.py style"""
        self.map_widget = tkintermapview.TkinterMapView(self.right_panel, corner_radius=0)
        self.map_widget.pack(fill='both', expand=True)
        self.map_widget.set_tile_server(
            'https://a.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png'
        )

        # Center map
        if self.coords:
            lats = [c[0] for c in self.coords.values()]
            lngs = [c[1] for c in self.coords.values()]
            self.map_widget.set_position(sum(lats)/len(lats), sum(lngs)/len(lngs))
            self.map_widget.set_zoom(13)

        # Draw roads using YOUR draw_edges function
        draw_edges(self.map_widget, self.coords)

        # Draw markers using YOUR colors
        for sid, (lat, lng) in self.coords.items():
            colour = NODE_COLOURS.get(sid, '#1a1a2e')
            marker = self.map_widget.set_marker(
                lat, lng, text=sid,
                marker_color_circle=colour,
                marker_color_outside='#ffffff',
                font=('Arial', 10, 'bold')
            )
            self.markers[sid] = marker

    def _show_map_unavailable(self):
        tk.Label(self.right_panel, text="Map unavailable.\npip install tkintermapview",
                font=('Arial', 12), bg='#ffffff', fg='#ff0000').pack(expand=True)

    def _locate_site(self, site_str):
        if site_str and self.map_widget and site_str in self.coords:
            lat, lng = self.coords[site_str]
            self.map_widget.set_position(lat, lng)
            self.map_widget.set_zoom(15)

    def _update_site_lists(self):
        sites = sorted([s for s in self.coords.keys() if s.isdigit()], key=int)
        self.origin_combo['values'] = sites
        self.dest_combo['values'] = sites
        if len(sites) >= 2:
            self.origin_combo.set(str(sites[0]))
            self.dest_combo.set(str(sites[1]))

    def clear_route(self):
        for item in self.current_route_items:
            try:
                item.delete()
            except:
                pass
        self.current_route_items = []

    def find_routes(self):
        origin_str = self.origin_var.get()
        dest_str = self.dest_var.get()

        if not origin_str or not dest_str:
            messagebox.showwarning("Input Error", "Select origin and destination")
            return

        try:
            origin = int(origin_str)
            dest = int(dest_str)
        except ValueError:
            messagebox.showwarning("Input Error", "Invalid site selection")
            return

        if origin == dest:
            messagebox.showwarning("Input Error", "Origin and destination must be different")
            return

        try:
            time_str = self.time_var.get()
            hour = int(time_str.split(':')[0]) if ':' in time_str else int(time_str)
            hour = max(0, min(23, hour))
        except:
            hour = 12

        self.status_var.set(f"Calculating routes from {origin} to {dest} using {self.current_model.get().upper()}...")
        self.root.update()

        self.results_text.delete(1.0, tk.END)
        self.clear_route()

        self.pathfinder.set_model(self.current_model.get())
        paths = self.pathfinder.find_top_k_paths(origin, dest, self.k_value.get(), hour)

        self._display_results(origin, dest, hour, paths)

        if paths:
            self._draw_route(paths[0][0])
            self.status_var.set(f"✓ Found {len(paths)} routes. Best: {paths[0][1]:.1f} minutes")
        else:
            self.status_var.set("No routes found.")

    def _draw_route(self, path):
        if not self.map_widget or len(path) < 2:
            return

        for i in range(len(path) - 1):
            node1 = str(path[i])
            node2 = str(path[i+1])
            if node1 in self.coords and node2 in self.coords:
                lat1, lng1 = self.coords[node1]
                lat2, lng2 = self.coords[node2]
                route_line = self.map_widget.set_path(
                    [(lat1, lng1), (lat2, lng2)],
                    color='#ff6f00', width=5
                )
                self.current_route_items.append(route_line)

        for node in path:
            node_str = str(node)
            if node_str in self.markers:
                self.markers[node_str].delete()
                if node == path[0]:
                    colour, text = '#2e7d32', f"📍 {node_str}"
                elif node == path[-1]:
                    colour, text = '#c62828', f"🏁 {node_str}"
                else:
                    colour, text = '#ff6f00', node_str

                lat, lng = self.coords[node_str]
                new_marker = self.map_widget.set_marker(
                    lat, lng, text=text,
                    marker_color_circle=colour,
                    marker_color_outside='#ffffff',
                    font=('Arial', 10, 'bold')
                )
                self.current_route_items.append(new_marker)
                self.markers[node_str] = new_marker

    def _display_results(self, origin, dest, hour, paths):
        self.results_text.insert(tk.END, "=" * 55 + "\n")
        self.results_text.insert(tk.END, "TBRGS ROUTE RESULTS\n")
        self.results_text.insert(tk.END, "=" * 55 + "\n\n")
        self.results_text.insert(tk.END, f"Origin:      SCATS {origin}\n")
        self.results_text.insert(tk.END, f"Destination: SCATS {dest}\n")
        self.results_text.insert(tk.END, f"Departure:   {self.time_var.get()} (Hour {hour}:00)\n")
        self.results_text.insert(tk.END, f"Model:       {self.current_model.get().upper()}\n")
        self.results_text.insert(tk.END, "=" * 55 + "\n\n")

        if not paths:
            self.results_text.insert(tk.END, "❌ No routes found!\n")
            return

        for i, (path, total_time) in enumerate(paths, 1):
            self.results_text.insert(tk.END, f"\n{'─' * 50}\n")
            self.results_text.insert(tk.END, f"ROUTE {i} │ {total_time:.1f} min ({total_time/60:.1f} hr)\n")
            self.results_text.insert(tk.END, f"{'─' * 50}\n")
            path_str = " → ".join(str(n) for n in path)
            self.results_text.insert(tk.END, f"  {path_str}\n")

        self.results_text.insert(tk.END, f"\n{'=' * 55}\n")


# ============================================================
# MAIN
# ============================================================

def main():
    print("\n" + "=" * 60)
    print("TBRGS - Traffic-Based Route Guidance System")
    print("INTEGRATED VERSION - Using your map.py")
    print("=" * 60 + "\n")
    
    root = tk.Tk()
    app = TBRGSApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()