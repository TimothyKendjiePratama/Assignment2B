# gui.py
"""
Tkinter GUI for TBRGS
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from config import WINDOW_WIDTH, WINDOW_HEIGHT, LEFT_PANEL_WIDTH, DEFAULT_K_ROUTES


class TBRGSGUI:
    """Main GUI application for TBRGS"""
    
    def __init__(self, root, map_viewer, pathfinder):
        self.root = root
        self.map_viewer = map_viewer
        self.pathfinder = pathfinder
        
        # GUI variables
        self.current_model = tk.StringVar(value='lstm')
        self.origin_var = tk.StringVar()
        self.dest_var = tk.StringVar()
        self.time_var = tk.StringVar(value="12:00")
        self.k_value = tk.IntVar(value=DEFAULT_K_ROUTES)
        
        # Map widgets reference
        self.map_widget = None
        self.results_text = None
        self.status_var = None
        
        # Setup window
        self._setup_window()
        self._build_gui()
        
        # Initialize map
        if self.map_viewer.is_map_available():
            self._init_map()
        else:
            self._show_map_unavailable()
    
    def _setup_window(self):
        self.root.title("TBRGS - Traffic-Based Route Guidance System")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.configure(bg='#f0f0f0')
    
    def _build_gui(self):
        # Left panel
        left_panel = tk.Frame(self.root, bg='#f0f0f0', width=LEFT_PANEL_WIDTH)
        left_panel.pack(side='left', fill='both', expand=False, padx=(10, 5), pady=10)
        left_panel.pack_propagate(False)
        
        # Right panel for map
        self.right_panel = tk.Frame(self.root, bg='#ffffff', bd=2, relief='sunken')
        self.right_panel.pack(side='right', fill='both', expand=True, padx=(5, 10), pady=10)
        
        # Title
        tk.Label(left_panel, text="TRAFFIC-BASED ROUTE GUIDANCE", 
                font=('Arial', 14, 'bold'), bg='#f0f0f0', fg='#1a237e').pack(pady=(0, 15))
        
        # Input frame
        self._build_input_frame(left_panel)
        
        # Model frame
        self._build_model_frame(left_panel)
        
        # Button frame
        self._build_button_frame(left_panel)
        
        # Results frame
        self._build_results_frame(left_panel)
        
        # Status bar
        self._build_status_bar()
    
    def _build_input_frame(self, parent):
        input_frame = tk.LabelFrame(parent, text="Trip Information", 
                                     font=('Arial', 11, 'bold'), 
                                     bg='#f0f0f0', padx=10, pady=10)
        input_frame.pack(fill='x', pady=(0, 10))
        
        # Origin
        tk.Label(input_frame, text="Origin SCATS:", font=('Arial', 10), 
                bg='#f0f0f0').grid(row=0, column=0, sticky='w', pady=5)
        self.origin_combo = ttk.Combobox(input_frame, textvariable=self.origin_var, width=20)
        self.origin_combo.grid(row=0, column=1, pady=5, padx=(10, 0))
        tk.Button(input_frame, text="📍", command=self._locate_origin,
                 font=('Arial', 10), width=3).grid(row=0, column=2, padx=5)
        
        # Destination
        tk.Label(input_frame, text="Destination SCATS:", font=('Arial', 10), 
                bg='#f0f0f0').grid(row=1, column=0, sticky='w', pady=5)
        self.dest_combo = ttk.Combobox(input_frame, textvariable=self.dest_var, width=20)
        self.dest_combo.grid(row=1, column=1, pady=5, padx=(10, 0))
        tk.Button(input_frame, text="📍", command=self._locate_destination,
                 font=('Arial', 10), width=3).grid(row=1, column=2, padx=5)
        
        # Time
        tk.Label(input_frame, text="Departure Time:", font=('Arial', 10), 
                bg='#f0f0f0').grid(row=2, column=0, sticky='w', pady=5)
        tk.Entry(input_frame, textvariable=self.time_var, width=10, 
                font=('Arial', 10)).grid(row=2, column=1, sticky='w', pady=5, padx=(10, 0))
        tk.Label(input_frame, text="(HH:MM, 24hr)", font=('Arial', 8), 
                bg='#f0f0f0').grid(row=2, column=1, sticky='e', padx=(0, 10))
    
    def _build_model_frame(self, parent):
        model_frame = tk.LabelFrame(parent, text="Model Selection (REAL ML Models)", 
                                     font=('Arial', 11, 'bold'), 
                                     bg='#f0f0f0', padx=10, pady=10)
        model_frame.pack(fill='x', pady=(0, 10))
        
        models = [('LSTM (Long Short-Term Memory)', 'lstm'),
                  ('GRU (Gated Recurrent Unit)', 'gru'),
                  ('XGBoost (Gradient Boosting)', 'xgboost')]
        
        for i, (text, value) in enumerate(models):
            tk.Radiobutton(model_frame, text=text, variable=self.current_model,
                          value=value, font=('Arial', 10), bg='#f0f0f0').grid(
                          row=i, column=0, padx=20, pady=5, sticky='w')
        
        tk.Label(model_frame, text="Number of routes (K):", font=('Arial', 10), 
                bg='#f0f0f0').grid(row=3, column=0, sticky='w', pady=5)
        tk.Spinbox(model_frame, from_=1, to=10, textvariable=self.k_value, 
                  width=5).grid(row=3, column=1, sticky='w', pady=5, padx=(10, 0))
    
    def _build_button_frame(self, parent):
        button_frame = tk.Frame(parent, bg='#f0f0f0')
        button_frame.pack(fill='x', pady=(0, 10))
        
        self.find_button = tk.Button(button_frame, text="FIND ROUTES", 
                                     command=self.find_routes,
                                     bg='#2e7d32', fg='white', 
                                     font=('Arial', 11, 'bold'), 
                                     padx=20, pady=5)
        self.find_button.pack(side='left', padx=5)
        
        self.clear_button = tk.Button(button_frame, text="CLEAR MAP", 
                                      command=self.clear_route,
                                      bg='#ef6c00', fg='white', 
                                      font=('Arial', 10), 
                                      padx=15, pady=5)
        self.clear_button.pack(side='left', padx=5)
    
    def _build_results_frame(self, parent):
        results_frame = tk.LabelFrame(parent, text="Route Results", 
                                       font=('Arial', 11, 'bold'), 
                                       bg='#f0f0f0', padx=10, pady=10)
        results_frame.pack(fill='both', expand=True)
        
        self.results_text = scrolledtext.ScrolledText(results_frame, height=12, 
                                                       width=50, font=('Courier', 9))
        self.results_text.pack(fill='both', expand=True)
    
    def _build_status_bar(self):
        self.status_var = tk.StringVar(value="Ready. Select origin and destination to find routes.")
        status_bar = tk.Label(self.root, textvariable=self.status_var, 
                              bd=1, relief='sunken', anchor='w')
        status_bar.pack(side='bottom', fill='x')
    
    def _init_map(self):
        """Initialize map using map_viewer"""
        self.map_widget = self.map_viewer.create_map(self.right_panel)
        self.map_viewer.draw_network()
        
        # Update site dropdowns
        self._update_site_lists()
    
    def _show_map_unavailable(self):
        tk.Label(self.right_panel, 
                text="Map visualization unavailable.\n\nPlease install tkintermapview:\npip install tkintermapview",
                font=('Arial', 12), bg='#ffffff', fg='#ff0000').pack(expand=True)
    
    def _update_site_lists(self):
        """Populate site dropdowns from available sites"""
        sites = self.map_viewer.get_available_sites()
        self.origin_combo['values'] = sites
        self.dest_combo['values'] = sites
        if len(sites) >= 2:
            self.origin_combo.set(str(sites[0]))
            self.dest_combo.set(str(sites[1]))
    
    def _locate_origin(self):
        site = self.origin_var.get()
        if site:
            self.map_viewer.locate_site(site)
            self.status_var.set(f"Located SCATS {site}")
    
    def _locate_destination(self):
        site = self.dest_var.get()
        if site:
            self.map_viewer.locate_site(site)
            self.status_var.set(f"Located SCATS {site}")
    
    def clear_route(self):
        """Clear route from map and results"""
        self.map_viewer.clear_route()
        self.results_text.delete(1.0, tk.END)
        self.status_var.set("Route cleared from map.")
    
    def get_user_input(self):
        """Get validated user input"""
        origin_str = self.origin_var.get()
        dest_str = self.dest_var.get()
        
        if not origin_str or not dest_str:
            messagebox.showwarning("Input Error", "Select origin and destination")
            return None, None, None
        
        try:
            origin = int(origin_str)
            dest = int(dest_str)
        except ValueError:
            messagebox.showwarning("Input Error", "Invalid site selection")
            return None, None, None
        
        if origin == dest:
            messagebox.showwarning("Input Error", "Origin and destination must be different")
            return None, None, None
        
        # Parse time
        try:
            time_str = self.time_var.get()
            hour = int(time_str.split(':')[0]) if ':' in time_str else int(time_str)
            hour = max(0, min(23, hour))
        except:
            hour = 12
        
        return origin, dest, hour
    
    # def find_routes(self):
    #     """Find and display routes"""
    #     origin, dest, hour = self.get_user_input()
    #     if origin is None:
    #         return
        
    #     model_name = self.current_model.get()
    #     k = self.k_value.get()
        
    #     # Update status
    #     self.status_var.set(f"Calculating routes from {origin} to {dest} "
    #                        f"using {model_name.upper()} at {hour}:00...")
    #     self.root.update()
        
    #     # Clear previous results
    #     self.results_text.delete(1.0, tk.END)
    #     self.map_viewer.clear_route()
        
    #     # Set model and find paths
    #     self.pathfinder.set_model(model_name)
    #     paths = self.pathfinder.find_top_k_paths(origin, dest, k, hour)
        
    #     # Display results
    #     self._display_results(origin, dest, hour, model_name, paths, k)
        
    #     if paths:
    #         self.map_viewer.draw_route(paths[0][0])
    #         self.status_var.set(f"✓ Found {len(paths)} routes. Best: {paths[0][1]:.1f} minutes")
    #     else:
    #         self.status_var.set("No routes found. Try different origin/destination.")
    
def find_routes(self):
    """Find and display top-K routes with algorithm selection info"""
    origin, dest, hour = self.get_user_input()
    if origin is None:
        return
    
    model_name = self.current_model.get()
    k = self.k_value.get()
    
    self.status_var.set(f"Finding top-{k} routes from {origin} to {dest}...")
    self.root.update()
    
    self.results_text.delete(1.0, tk.END)
    self.map_viewer.clear_route()
    
    # AUTO-SELECT BEST ALGORITHM
    # You can enable this or let user choose manually
    auto_select = True  # Set to True to auto-select, False for manual
    
    selection_reason = None
    if auto_select:
        # Get graph stats for recommendation
        graph_stats = self.pathfinder.get_graph_info()
        graph_size = graph_stats['total_nodes']
        
        # Simple auto-selection logic
        if graph_size > 50:
            recommended = 'bidirectional'
            selection_reason = f"Large graph ({graph_size} nodes) → Bidirectional A* is fastest"
        elif k > 3:
            recommended = 'astar'
            selection_reason = f"Need {k} routes → A* provides optimal paths"
        else:
            recommended = 'astar'
            selection_reason = "Default optimal algorithm"
        
        self.pathfinder.set_algorithm(recommended)
        algorithm = recommended
    else:
        algorithm = self.algorithm_var.get()  # User selected
    
    self.pathfinder.set_model(model_name)
    paths = self.pathfinder.find_top_k_paths(origin, dest, k, hour)
    
    # Draw the best route on map
    if paths:
        self.map_viewer.draw_route(paths[0][0])
        self.status_var.set(f"✓ Found {len(paths)} routes. Best: {paths[0][1]:.1f} minutes using {algorithm.upper()}")
    else:
        self.status_var.set("No routes found. Try different origin/destination.")
    
    # Display results with algorithm info
    self._display_results(origin, dest, hour, model_name, algorithm, paths, k, selection_reason)
    
    # def _display_results(self, origin, dest, hour, model_name, paths, k):
    #     """Display formatted results in text area"""
    #     self.results_text.insert(tk.END, "=" * 55 + "\n")
    #     self.results_text.insert(tk.END, "TBRGS ROUTE RESULTS\n")
    #     self.results_text.insert(tk.END, "=" * 55 + "\n\n")
    #     self.results_text.insert(tk.END, f"Origin:      SCATS {origin}\n")
    #     self.results_text.insert(tk.END, f"Destination: SCATS {dest}\n")
    #     self.results_text.insert(tk.END, f"Departure:   {self.time_var.get()} (Hour {hour}:00)\n")
    #     self.results_text.insert(tk.END, f"Model:       {model_name.upper()}\n")
    #     self.results_text.insert(tk.END, f"K requested: {k}\n")
    #     self.results_text.insert(tk.END, "=" * 55 + "\n\n")
        
    #     if not paths:
    #         self.results_text.insert(tk.END, "❌ No routes found!\n\n")
    #         self.results_text.insert(tk.END, "Possible reasons:\n")
    #         self.results_text.insert(tk.END, "  - No road connection between these SCATS sites\n")
    #         self.results_text.insert(tk.END, "  - Graph may not be fully connected\n")
    #         return
        
    #     for i, (path, total_time) in enumerate(paths, 1):
    #         self.results_text.insert(tk.END, f"\n{'─' * 50}\n")
    #         self.results_text.insert(tk.END, f"ROUTE {i} │ {total_time:.1f} minutes ({total_time/60:.1f} hours)\n")
    #         self.results_text.insert(tk.END, f"{'─' * 50}\n")
    #         path_str = " → ".join(str(n) for n in path)
    #         self.results_text.insert(tk.END, f"  {path_str}\n")
            
    #         # Show segment breakdown
    #         if len(path) > 2:
    #             segments = len(path) - 1
    #             avg_segment_time = total_time / segments
    #             self.results_text.insert(tk.END, f"\n  Average per segment: {avg_segment_time:.1f} minutes\n")
        
    #     self.results_text.insert(tk.END, f"\n{'=' * 55}\n")
    
def _display_results(self, origin, dest, hour, model_name, algorithm, paths, k, selection_reason=None):
    """Display formatted results including top-K routes and algorithm selection info"""
    self.results_text.insert(tk.END, "=" * 65 + "\n")
    self.results_text.insert(tk.END, "TBRGS ROUTE RESULTS\n")
    self.results_text.insert(tk.END, "=" * 65 + "\n\n")
    
    # Trip information
    self.results_text.insert(tk.END, f"Origin:      SCATS {origin}\n")
    self.results_text.insert(tk.END, f"Destination: SCATS {dest}\n")
    self.results_text.insert(tk.END, f"Departure:   {self.time_var.get()} (Hour {hour}:00)\n")
    self.results_text.insert(tk.END, f"ML Model:    {model_name.upper()}\n")
    self.results_text.insert(tk.END, "-" * 65 + "\n")
    
    # Algorithm selection info
    self.results_text.insert(tk.END, f"Selected Algorithm: {algorithm.upper()}\n")
    if selection_reason:
        self.results_text.insert(tk.END, f"Selection Reason:   {selection_reason}\n")
    
    # Algorithm metadata
    algo_info = self.pathfinder.get_algorithm_info().get(algorithm, {})
    if algo_info:
        optimal = "✓ Yes" if algo_info.get('optimal') else "✗ No (heuristic only)"
        self.results_text.insert(tk.END, f"Optimal Guarantee:  {optimal}\n")
    
    self.results_text.insert(tk.END, "=" * 65 + "\n\n")
    
    # Show top-K routes
    if not paths:
        self.results_text.insert(tk.END, "❌ No routes found!\n\n")
        return
    
    self.results_text.insert(tk.END, f"Found {len(paths)} routes (requested: {k}):\n\n")
    
    for i, (path, total_time) in enumerate(paths, 1):
        self.results_text.insert(tk.END, f"{'─' * 60}\n")
        self.results_text.insert(tk.END, f"ROUTE {i} │ {total_time:.1f} minutes ({total_time/60:.1f} hours)\n")
        self.results_text.insert(tk.END, f"{'─' * 60}\n")
        
        # Show path with arrows
        path_str = " → ".join(str(n) for n in path)
        # Wrap long paths
        if len(path_str) > 70:
            # Break into multiple lines
            nodes = [str(n) for n in path]
            lines = []
            current_line = []
            current_length = 0
            for node in nodes:
                if current_length + len(node) + 3 > 70:
                    lines.append(" → ".join(current_line))
                    current_line = [node]
                    current_length = len(node)
                else:
                    current_line.append(node)
                    current_length += len(node) + 3
            if current_line:
                lines.append(" → ".join(current_line))
            for line in lines:
                self.results_text.insert(tk.END, f"  {line}\n")
        else:
            self.results_text.insert(tk.END, f"  {path_str}\n")
        
        # Show segment breakdown
        if len(path) > 2:
            self.results_text.insert(tk.END, f"\n  Segment times:\n")
            for j in range(len(path) - 1):
                from_node = path[j]
                to_node = path[j+1]
                # Find distance for this edge
                dist = None
                for neighbor, d in self.pathfinder.graph.get(str(from_node), []):
                    if neighbor == str(to_node):
                        dist = d
                        break
                if dist:
                    self.results_text.insert(tk.END, f"    {from_node} → {to_node}: {dist:.2f} km\n")
        
        self.results_text.insert(tk.END, f"\n  Total: {total_time:.1f} minutes\n")
    
    self.results_text.insert(tk.END, f"\n{'=' * 65}\n")
    
    # Show algorithm comparison if multiple routes found
    if len(paths) > 1:
        self.results_text.insert(tk.END, "\n📊 Route Comparison:\n")
        self.results_text.insert(tk.END, "-" * 40 + "\n")
        for i, (_, time) in enumerate(paths, 1):
            best_time = paths[0][1]
            diff = time - best_time
            if i == 1:
                self.results_text.insert(tk.END, f"  Route {i}: {time:.1f} min (BEST)\n")
            else:
                self.results_text.insert(tk.END, f"  Route {i}: {time:.1f} min (+{diff:.1f} min longer)\n")

def _build_algorithm_frame(self, parent):
    """Algorithm selection frame"""
    algo_frame = tk.LabelFrame(parent, text="Search Algorithm Selection", 
                                font=('Arial', 11, 'bold'), 
                                bg='#f0f0f0', padx=10, pady=10)
    algo_frame.pack(fill='x', pady=(0, 10))
    
    # Algorithm dropdown
    tk.Label(algo_frame, text="Search Algorithm:", font=('Arial', 10), 
            bg='#f0f0f0').grid(row=0, column=0, sticky='w', pady=5)
    
    self.algorithm_var = tk.StringVar(value='astar')
    algorithms = [
        ('A* (Optimal, Recommended)', 'astar'),
        ('Bidirectional A* (Fast for large graphs)', 'bidirectional'),
        ("Dijkstra (Optimal, no heuristic)", 'dijkstra'),
        ('Greedy Best-First (Fast, not optimal)', 'greedy'),
        ('BFS (Fewest hops, ignores weights)', 'bfs'),
        ('DFS (Memory efficient)', 'dfs')
    ]
    
    self.algo_combo = ttk.Combobox(algo_frame, textvariable=self.algorithm_var, 
                                    values=[a[1] for a in algorithms], width=30)
    self.algo_combo.grid(row=0, column=1, pady=5, padx=(10, 0))
    
    # Auto-select button
    tk.Button(algo_frame, text="🤖 Auto-Select Best", command=self.auto_select_algorithm,
             bg='#2196f3', fg='white', font=('Arial', 9), padx=10, pady=2).grid(
             row=1, column=0, columnspan=2, pady=5)
    
    # Algorithm info label
    self.algo_info_label = tk.Label(algo_frame, text="", font=('Arial', 8), 
                                     bg='#f0f0f0', fg='#666')
    self.algo_info_label.grid(row=2, column=0, columnspan=2, pady=5)

def auto_select_algorithm(self):
    """Auto-select best algorithm based on graph and user request"""
    graph_stats = self.pathfinder.get_graph_info()
    k = self.k_value.get()
    graph_size = graph_stats['total_nodes']
    
    if graph_size > 50:
        recommended = 'bidirectional'
        reason = f"Large graph ({graph_size} nodes) → Bidirectional A* is fastest"
    elif k > 3:
        recommended = 'astar'
        reason = f"Need {k} routes → A* provides optimal paths with heuristic"
    else:
        recommended = 'astar'
        reason = "Default optimal algorithm for general use"
    
    self.algorithm_var.set(recommended)
    self.pathfinder.set_algorithm(recommended)
    self.algo_info_label.config(text=f"✓ Recommended: {recommended.upper()} - {reason}")
    self.status_var.set(f"Auto-selected {recommended.upper()} algorithm: {reason}")