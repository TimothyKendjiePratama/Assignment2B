# gui.py
"""
Tkinter GUI for TBRGS with 2D visualization
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import math
from config import DEFAULT_K_ROUTES


class TBRGSApp:
    def __init__(self, root, processor, pathfinder, traffic_predictor):
        self.root = root
        self.processor = processor
        self.pathfinder = pathfinder
        self.traffic_predictor = traffic_predictor

        self.current_model = tk.StringVar(value='lstm')
        
        # For visualization
        self.canvas_width = 800
        self.canvas_height = 600
        self.node_positions = {}  # SCATS number -> (x, y) on canvas
        self.current_path = []    # Currently displayed path

        self._setup_window()
        self._build_gui()
        self._update_site_lists()
        self._draw_map()

    def _setup_window(self):
        self.root.title("TBRGS - Traffic-Based Route Guidance System")
        self.root.geometry("1400x800")
        self.root.configure(bg='#f0f0f0')

    def _build_gui(self):
        # Title bar
        title_frame = tk.Frame(self.root, bg='#1a237e', height=60)
        title_frame.pack(fill='x')
        tk.Label(title_frame, text="Traffic-Based Route Guidance System (TBRGS)",
                font=('Arial', 16, 'bold'), fg='white', bg='#1a237e').pack(pady=15)

        # Main container with two columns
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # LEFT PANEL - Controls and results
        left_panel = tk.Frame(main_frame, bg='#f0f0f0', width=500)
        left_panel.pack(side='left', fill='both', expand=False, padx=(0, 10))
        left_panel.pack_propagate(False)

        # RIGHT PANEL - Visualization
        right_panel = tk.Frame(main_frame, bg='#ffffff', bd=2, relief='sunken')
        right_panel.pack(side='right', fill='both', expand=True)

        # === LEFT PANEL CONTROLS ===
        # Input section
        input_frame = tk.LabelFrame(left_panel, text="Trip Information",
                                     font=('Arial', 12, 'bold'),
                                     bg='#f0f0f0', padx=10, pady=10)
        input_frame.pack(fill='x', pady=(0, 10))

        # Origin
        tk.Label(input_frame, text="Origin SCATS Site:", font=('Arial', 10),
                bg='#f0f0f0').grid(row=0, column=0, sticky='w', pady=5)
        self.origin_var = tk.StringVar()
        self.origin_combo = ttk.Combobox(input_frame, textvariable=self.origin_var, width=25)
        self.origin_combo.grid(row=0, column=1, pady=5, padx=(10, 0))
        tk.Button(input_frame, text="📍", command=lambda: self._locate_site(self.origin_var),
                 font=('Arial', 10), width=3).grid(row=0, column=2, padx=5)

        # Destination
        tk.Label(input_frame, text="Destination SCATS Site:", font=('Arial', 10),
                bg='#f0f0f0').grid(row=1, column=0, sticky='w', pady=5)
        self.dest_var = tk.StringVar()
        self.dest_combo = ttk.Combobox(input_frame, textvariable=self.dest_var, width=25)
        self.dest_combo.grid(row=1, column=1, pady=5, padx=(10, 0))
        tk.Button(input_frame, text="📍", command=lambda: self._locate_site(self.dest_var),
                 font=('Arial', 10), width=3).grid(row=1, column=2, padx=5)

        # Time
        tk.Label(input_frame, text="Departure Time:", font=('Arial', 10),
                bg='#f0f0f0').grid(row=2, column=0, sticky='w', pady=5)
        self.time_var = tk.StringVar(value="12:00")
        tk.Entry(input_frame, textvariable=self.time_var, width=10, font=('Arial', 10)).grid(
                 row=2, column=1, sticky='w', pady=5, padx=(10, 0))
        tk.Label(input_frame, text="(HH:MM, 24-hour)", font=('Arial', 8),
                bg='#f0f0f0').grid(row=2, column=1, sticky='e', padx=(0, 10))

        # Model selection
        model_frame = tk.LabelFrame(left_panel, text="Model Selection",
                                     font=('Arial', 12, 'bold'),
                                     bg='#f0f0f0', padx=10, pady=10)
        model_frame.pack(fill='x', pady=(0, 10))

        models = [('LSTM', 'lstm'), ('GRU', 'gru'), ('XGBoost', 'xgboost')]
        for i, (text, value) in enumerate(models):
            tk.Radiobutton(model_frame, text=text, variable=self.current_model,
                          value=value, font=('Arial', 10), bg='#f0f0f0').grid(
                          row=0, column=i, padx=20, pady=5)

        # Number of routes
        tk.Label(model_frame, text="Number of routes (K):", font=('Arial', 10),
                bg='#f0f0f0').grid(row=1, column=0, sticky='w', pady=5)
        self.k_value = tk.IntVar(value=DEFAULT_K_ROUTES)
        tk.Spinbox(model_frame, from_=1, to=10, textvariable=self.k_value,
                  width=5, font=('Arial', 10)).grid(row=1, column=1, sticky='w', pady=5, padx=(10, 0))

        # Buttons
        button_frame = tk.Frame(left_panel, bg='#f0f0f0')
        button_frame.pack(fill='x', pady=(0, 10))

        tk.Button(button_frame, text="FIND ROUTES", command=self.find_routes,
                 bg='#2e7d32', fg='white', font=('Arial', 12, 'bold'),
                 padx=20, pady=5).pack(side='left', padx=5)

        tk.Button(button_frame, text="CLEAR MAP", command=self.clear_map,
                 bg='#ef6c00', fg='white', font=('Arial', 10),
                 padx=15, pady=5).pack(side='left', padx=5)

        # Results section
        results_frame = tk.LabelFrame(left_panel, text="Route Results",
                                       font=('Arial', 12, 'bold'),
                                       bg='#f0f0f0', padx=10, pady=10)
        results_frame.pack(fill='both', expand=True)

        self.results_text = scrolledtext.ScrolledText(results_frame, height=12,
                                                       width=55, font=('Courier', 9))
        self.results_text.pack(fill='both', expand=True)

        # === RIGHT PANEL VISUALIZATION ===
        vis_header = tk.Frame(right_panel, bg='#e0e0e0', height=30)
        vis_header.pack(fill='x')
        tk.Label(vis_header, text="Borondara SCATS Network Map", font=('Arial', 10, 'bold'),
                bg='#e0e0e0').pack(pady=5)

        self.visualization_canvas = tk.Canvas(right_panel, width=self.canvas_width, 
                                               height=self.canvas_height, bg='#fafafa',
                                               highlightthickness=0)
        self.visualization_canvas.pack(fill='both', expand=True, padx=5, pady=5)

        # Legend
        legend_frame = tk.Frame(right_panel, bg='#f5f5f5', height=50)
        legend_frame.pack(fill='x')
        
        tk.Label(legend_frame, text="●", fg='#1a237e', font=('Arial', 12), bg='#f5f5f5').pack(side='left', padx=(10, 2))
        tk.Label(legend_frame, text="SCATS Intersection", font=('Arial', 9), bg='#f5f5f5').pack(side='left', padx=(0, 15))
        
        tk.Label(legend_frame, text="●", fg='#2e7d32', font=('Arial', 12), bg='#f5f5f5').pack(side='left', padx=(10, 2))
        tk.Label(legend_frame, text="Origin", font=('Arial', 9), bg='#f5f5f5').pack(side='left', padx=(0, 15))
        
        tk.Label(legend_frame, text="●", fg='#c62828', font=('Arial', 12), bg='#f5f5f5').pack(side='left', padx=(10, 2))
        tk.Label(legend_frame, text="Destination", font=('Arial', 9), bg='#f5f5f5').pack(side='left', padx=(0, 15))
        
        tk.Label(legend_frame, text="━", fg='#ff6f00', font=('Arial', 12, 'bold'), bg='#f5f5f5').pack(side='left', padx=(10, 2))
        tk.Label(legend_frame, text="Route Path", font=('Arial', 9), bg='#f5f5f5').pack(side='left', padx=(0, 15))

        # Status bar
        self.status_var = tk.StringVar(value="Ready. Select origin and destination to find routes.")
        status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1,
                              relief='sunken', anchor='w', font=('Arial', 9))
        status_bar.pack(side='bottom', fill='x')

    def _get_lat_lon_bounds(self):
        """Get min/max lat/lon for scaling"""
        sites = self.processor.get_sites()
        lats = []
        lons = []
        
        for site_id, info in sites.items():
            if info.get('lat') and info.get('lon'):
                lats.append(info['lat'])
                lons.append(info['lon'])
        
        if not lats:
            # Fallback to approximate Borondara bounds
            return -37.87, -37.81, 145.04, 145.10
        
        return min(lats), max(lats), min(lons), max(lons)

    def _lat_lon_to_canvas(self, lat, lon):
        """Convert lat/lon to canvas coordinates"""
        min_lat, max_lat, min_lon, max_lon = self._get_lat_lon_bounds()
        
        # Add padding (10%)
        lat_range = max_lat - min_lat
        lon_range = max_lon - min_lon
        lat_padding = lat_range * 0.1
        lon_padding = lon_range * 0.1
        
        min_lat -= lat_padding
        max_lat += lat_padding
        min_lon -= lon_padding
        max_lon += lon_padding
        
        # Scale to canvas
        x = ((lon - min_lon) / (max_lon - min_lon)) * self.canvas_width
        y = ((lat - max_lat) / (min_lat - max_lat)) * self.canvas_height  # Flip Y axis
        
        return int(x), int(y)

    def _draw_map(self):
        """Draw the SCATS network map"""
        self.visualization_canvas.delete("all")
        
        sites = self.processor.get_sites()
        graph = self.processor.get_graph()
        
        # First, draw all edges (roads)
        drawn_edges = set()
        for site_id, neighbors in graph.items():
            site_info = sites.get(site_id)
            if not site_info or not site_info.get('lat'):
                continue
            
            x1, y1 = self._lat_lon_to_canvas(site_info['lat'], site_info['lon'])
            
            for neighbor_id, distance in neighbors:
                if (neighbor_id, site_id) in drawn_edges:
                    continue
                drawn_edges.add((site_id, neighbor_id))
                
                neighbor_info = sites.get(neighbor_id)
                if not neighbor_info or not neighbor_info.get('lat'):
                    continue
                
                x2, y2 = self._lat_lon_to_canvas(neighbor_info['lat'], neighbor_info['lon'])
                
                # Draw road edge
                self.visualization_canvas.create_line(x1, y1, x2, y2, fill='#bdbdbd', width=2)
                
                # Add distance label
                mx, my = (x1 + x2) // 2, (y1 + y2) // 2
                self.visualization_canvas.create_text(mx, my - 8, text=f"{distance:.1f}km",
                                                       font=('Arial', 7), fill='#757575')
        
        # Then, draw all nodes (SCATS sites)
        for site_id, info in sites.items():
            if not info.get('lat'):
                continue
            
            x, y = self._lat_lon_to_canvas(info['lat'], info['lon'])
            
            # Draw node circle
            self.visualization_canvas.create_oval(x-6, y-6, x+6, y+6, fill='#1a237e', outline='white', width=2)
            
            # Draw site number label
            self.visualization_canvas.create_text(x, y-10, text=str(site_id), 
                                                   font=('Arial', 8, 'bold'), fill='white')
            
            # Store position for later use
            self.node_positions[site_id] = (x, y)
            
            # Tooltip on hover
            self.visualization_canvas.tag_bind(self.visualization_canvas.create_oval(x-8, y-8, x+8, y+8, 
                                                                                      fill='', outline=''),
                                                "<Enter>", lambda e, sid=site_id: self._show_tooltip(sid))
        
        self.visualization_canvas.create_text(10, 20, text=f"Total: {len(sites)} SCATS sites", 
                                               anchor='nw', font=('Arial', 9, 'bold'), fill='#555')

    def _show_tooltip(self, site_id):
        """Show tooltip with site information"""
        sites = self.processor.get_sites()
        info = sites.get(site_id, {})
        directions = info.get('directions', [])
        first_dir = directions[0] if directions else "Unknown"
        
        tooltip_text = f"SCATS {site_id}\n{first_dir[:40]}"
        self.status_var.set(tooltip_text)

    def _locate_site(self, var):
        """Center map on a specific SCATS site"""
        site_str = var.get()
        if not site_str:
            return
        
        try:
            site_id = int(site_str)
            sites = self.processor.get_sites()
            info = sites.get(site_id)
            
            if info and info.get('lat'):
                x, y = self._lat_lon_to_canvas(info['lat'], info['lon'])
                # Flash the node
                self.visualization_canvas.create_oval(x-15, y-15, x+15, y+15, 
                                                       outline='#ff6f00', width=3, tags='flash')
                self.root.after(500, lambda: self.visualization_canvas.delete('flash'))
                self.status_var.set(f"Located SCATS {site_id}")
        except:
            pass

    def _draw_path(self, path):
        """Draw a route path on the map"""
        # Clear previous path
        self.visualization_canvas.delete('route')
        self.visualization_canvas.delete('route_node')
        
        if not path or len(path) < 2:
            return
        
        for i in range(len(path) - 1):
            node1 = path[i]
            node2 = path[i+1]
            
            if node1 in self.node_positions and node2 in self.node_positions:
                x1, y1 = self.node_positions[node1]
                x2, y2 = self.node_positions[node2]
                
                # Draw thick route line
                self.visualization_canvas.create_line(x1, y1, x2, y2, fill='#ff6f00', 
                                                       width=4, tags='route')
        
        # Highlight nodes in path
        for node in path:
            if node in self.node_positions:
                x, y = self.node_positions[node]
                self.visualization_canvas.create_oval(x-8, y-8, x+8, y+8, 
                                                       outline='#ff6f00', width=2, tags='route_node')
        
        # Mark origin and destination specially
        if path:
            origin = path[0]
            dest = path[-1]
            if origin in self.node_positions:
                x, y = self.node_positions[origin]
                self.visualization_canvas.create_oval(x-10, y-10, x+10, y+10, 
                                                       fill='#2e7d32', outline='white', width=2, tags='route_node')
                self.visualization_canvas.create_text(x, y, text="S", font=('Arial', 8, 'bold'), 
                                                       fill='white', tags='route_node')
            
            if dest in self.node_positions:
                x, y = self.node_positions[dest]
                self.visualization_canvas.create_oval(x-10, y-10, x+10, y+10, 
                                                       fill='#c62828', outline='white', width=2, tags='route_node')
                self.visualization_canvas.create_text(x, y, text="E", font=('Arial', 8, 'bold'), 
                                                       fill='white', tags='route_node')

    def clear_map(self):
        """Clear the map and redraw base network"""
        self._draw_map()
        self.current_path = []
        self.results_text.delete(1.0, tk.END)
        self.status_var.set("Map cleared.")

    def _update_site_lists(self):
        """Populate site dropdowns"""
        sites = sorted(self.processor.get_sites().keys())
        self.origin_combo['values'] = sites
        self.dest_combo['values'] = sites

        if len(sites) >= 2:
            self.origin_combo.set(str(sites[0]))
            self.dest_combo.set(str(sites[1]))

    def find_routes(self):
        """Find and display top-K routes"""
        origin_str = self.origin_var.get()
        dest_str = self.dest_var.get()

        if not origin_str or not dest_str:
            messagebox.showwarning("Input Error", "Please select both origin and destination")
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

        # Parse departure time
        try:
            time_str = self.time_var.get()
            if ':' in time_str:
                hour = int(time_str.split(':')[0])
            else:
                hour = int(time_str)
            if hour < 0 or hour > 23:
                hour = 12
        except:
            hour = 12

        self.status_var.set(f"Calculating top-{self.k_value.get()} routes from {origin} to {dest} "
                           f"using {self.current_model.get().upper()} at {hour}:00...")
        self.root.update()

        self.results_text.delete(1.0, tk.END)

        # Set model and find paths
        self.pathfinder.set_model(self.current_model.get())
        paths = self.pathfinder.find_top_k_paths(origin, dest, self.k_value.get(), hour)

        # Display results
        self._display_results(origin, dest, hour, paths)

        # Draw the best route on map
        if paths:
            self._draw_path(paths[0][0])
            best_time = paths[0][1]
            self.status_var.set(f"✓ Found {len(paths)} routes. Best route: {best_time:.1f} minutes")
        else:
            self.status_var.set("No routes found. Try different origin/destination.")

    def _display_results(self, origin, dest, hour, paths):
        """Display formatted results"""
        self.results_text.insert(tk.END, "=" * 60 + "\n")
        self.results_text.insert(tk.END, "TBRGS ROUTE RESULTS\n")
        self.results_text.insert(tk.END, "=" * 60 + "\n\n")
        self.results_text.insert(tk.END, f"Origin:      SCATS {origin}\n")
        self.results_text.insert(tk.END, f"Destination: SCATS {dest}\n")
        self.results_text.insert(tk.END, f"Departure:   {self.time_var.get()} (Hour {hour}:00)\n")
        self.results_text.insert(tk.END, f"Model:       {self.current_model.get().upper()}\n")
        self.results_text.insert(tk.END, "=" * 60 + "\n\n")

        if not paths:
            self.results_text.insert(tk.END, "❌ No routes found!\n\n")
            return

        for i, (path, total_time) in enumerate(paths, 1):
            self.results_text.insert(tk.END, f"\n{'─' * 55}\n")
            self.results_text.insert(tk.END, f"ROUTE {i} │ {total_time:.1f} min ({total_time/60:.1f} hr)\n")
            self.results_text.insert(tk.END, f"{'─' * 55}\n")
            
            # Show path as arrow-separated
            path_str = " → ".join(str(n) for n in path)
            self.results_text.insert(tk.END, f"  {path_str}\n")

        self.results_text.insert(tk.END, f"\n{'=' * 60}\n")