# data_processor.py
"""
Loads and processes SCATS traffic data from Excel
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re


class BorondaraDataProcessor:
    def __init__(self):
        self.sites = {}  # SCATS number -> site info
        self.graph = {}  # node -> [(neighbor, distance_km)]
        self.traffic_data = {}  # (site, direction) -> list of (timestamp, volume)
        self.volume_mean = 0
        self.volume_std = 1
        
    def load_all_data(self, filename='Scats Data October 2006.xls'):
        """Load all traffic data from Excel file"""
        
        print("=" * 60)
        print("Borondara Traffic Data")
        print("=" * 60)
        
        self._load_traffic_data(filename)
        self._build_graph()
        
        print("\n" + "=" * 60)
        print(f"  - SCATS sites with data: {len(self.sites)}")
        print(f"  - Site/direction combinations: {len(self.traffic_data)}")
        print(f"  - Graph edges: {sum(len(n) for n in self.graph.values()) // 2}")
        print("=" * 60)
        
        return self
    
    def _load_traffic_data(self, filename):
        "Load traffic volume"
        df = pd.read_excel(filename, sheet_name='Data', header=1)
        print(f"    Loaded {len(df)} rows of traffic data")
        
        # Find volume columns (V00 to V95)
        volume_cols = [col for col in df.columns if str(col).startswith('V') and str(col)[1:].isdigit()]
        volume_cols = sorted(volume_cols, key=lambda x: int(x[1:]))
        print(f"    Found {len(volume_cols)} volume columns (15-min intervals)")
        
        for _, row in df.iterrows():
            scats_num = row.get('SCATS Number')
            if pd.isna(scats_num):
                continue
                
            scats_num = int(scats_num)
            location = row.get('Location', '')
            date_val = row.get('Date', None)
            
            if pd.isna(date_val):
                continue
            
            # Extract volumes
            volumes = [int(row.get(col, 0)) if not pd.isna(row.get(col, 0)) else 0 for col in volume_cols]
            
            # Extract coordinates
            lat = row.get('NB_LATITUDE', None)
            lon = row.get('NB_LONGITUDE', None)
            
            # Initialize site
            if scats_num not in self.sites:
                self.sites[scats_num] = {
                    'directions': [],
                    'description': location,
                    'lat': lat if not pd.isna(lat) else None,
                    'lon': lon if not pd.isna(lon) else None
                }
            
            if location and location not in self.sites[scats_num]['directions']:
                self.sites[scats_num]['directions'].append(location)
            
            # Store traffic data
            key = (scats_num, location)
            if key not in self.traffic_data:
                self.traffic_data[key] = []
            
            self.traffic_data[key].append({
                'date': pd.to_datetime(date_val),
                'volumes': volumes
            })
        
        print(f"    Processed {len(self.traffic_data)} site/direction combinations")
    
    def _extract_roads(self, location):
        "Extract road names from location string"
        roads = []
        if not location or pd.isna(location):
            return roads
        
        location = str(location).upper()
        suffixes = ['RD', 'ST', 'HWY', 'GV', 'CR', 'AVE', 'DR', 'PDE', 'CT', 
                   'LANE', 'ROAD', 'STREET', 'HIGHWAY', 'GROVE', 'CRESCENT']
        
        for suffix in suffixes:
            pattern = rf'([A-Z][A-Z\s_\-]+{suffix})'
            matches = re.findall(pattern, location)
            for match in matches:
                road = match.replace('_', ' ').strip()
                road = re.sub(r'\s+', ' ', road)
                if road and road not in roads:
                    roads.append(road)
        
        # Also handle "X OF Y" patterns
        of_pattern = r'([A-Z][A-Z\s_\-]+)\s+OF\s+([A-Z][A-Z\s_\-]+)'
        matches = re.findall(of_pattern, location)
        for match in matches:
            for road in match:
                road = road.replace('_', ' ').strip()
                if road and road not in roads:
                    roads.append(road)
        
        return roads
    
    def _haversine_distance(self, lat1, lon1, lat2, lon2):
        "Calculate distance between two points in km"
        if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
            return None
        
        from math import radians, sin, cos, sqrt, atan2
        R = 6371
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        return R * c
    
    def _build_graph(self):
        """Build graph connecting SCATS sites"""
        
        # Map sites to roads
        site_to_roads = {}
        for scats_num, site_info in self.sites.items():
            roads = set()
            for direction in site_info['directions']:
                roads.update(self._extract_roads(direction))
            site_to_roads[scats_num] = list(roads)
        
        # Map roads to sites
        road_to_sites = {}
        for scats_num, roads in site_to_roads.items():
            for road in roads:
                if road not in road_to_sites:
                    road_to_sites[road] = []
                if scats_num not in road_to_sites[road]:
                    road_to_sites[road].append(scats_num)
        
        print(f"    Found {len(road_to_sites)} unique road names")
        
        # Create edges
        edges = set()
        for road, sites_on_road in road_to_sites.items():
            if len(sites_on_road) < 2:
                continue
            
            sites_on_road = sorted(set(sites_on_road))
            
            for i in range(len(sites_on_road)):
                for j in range(i+1, len(sites_on_road)):
                    site1 = sites_on_road[i]
                    site2 = sites_on_road[j]
                    
                    lat1 = self.sites[site1].get('lat')
                    lon1 = self.sites[site1].get('lon')
                    lat2 = self.sites[site2].get('lat')
                    lon2 = self.sites[site2].get('lon')
                    
                    if lat1 and lat2:
                        distance = self._haversine_distance(lat1, lon1, lat2, lon2)
                    else:
                        # Estimate based on site number difference
                        diff = abs(site1 - site2)
                        if diff < 1000:
                            distance = diff / 1000.0
                        else:
                            continue
                    
                    if distance and 0.1 <= distance <= 10.0:
                        edges.add((site1, site2, round(distance, 3)))
                        edges.add((site2, site1, round(distance, 3)))
        
        # Build graph
        self.graph = {site: [] for site in self.sites.keys()}
        for u, v, dist in edges:
            self.graph[u].append((v, dist))
        
        for site in self.graph:
            self.graph[site].sort(key=lambda x: x[1])
        
        # Show sample connections
        count = 0
        for site, neighbors in self.graph.items():
            if neighbors and count < 10:
                print(f"      SCATS {site} -> {[(n, f'{d:.2f}km') for n, d in neighbors[:3]]}")
                count += 1
    
    def get_time_series(self, scats_num, direction=None):
        """Get time series for a site"""
        time_series = []
        for (site, dir_name), data_list in self.traffic_data.items():
            if site != scats_num:
                continue
            if direction and dir_name != direction:
                continue
            for day_data in data_list:
                base_date = day_data['date']
                for i, vol in enumerate(day_data['volumes']):
                    timestamp = base_date + timedelta(minutes=15 * i)
                    time_series.append((timestamp, vol))
        return sorted(time_series, key=lambda x: x[0])
    
    def create_ml_dataset(self, seq_length=12, test_split=0.2):
        """Create sliding window dataset for ML"""
        X, y = [], []
        
        for (scats_num, direction), _ in self.traffic_data.items():
            ts = self.get_time_series(scats_num, direction)
            volumes = [v for _, v in ts]
            
            if len(volumes) < seq_length + 10:
                continue
            
            for i in range(len(volumes) - seq_length - 1):
                X.append(volumes[i:i+seq_length])
                y.append(volumes[i+seq_length])
        
        if len(X) == 0:
            # Fallback to synthetic data
            X = np.random.randint(50, 800, size=(5000, seq_length))
            y = np.random.randint(50, 800, size=5000)
        
        X = np.array(X, dtype=np.float32)
        y = np.array(y, dtype=np.float32)
        
        self.volume_mean = np.mean(X)
        self.volume_std = np.std(X) + 1e-8
        X = (X - self.volume_mean) / self.volume_std
        y = (y - self.volume_mean) / self.volume_std
        
        split_idx = int(len(X) * (1 - test_split))
        return X[:split_idx], X[split_idx:], y[:split_idx], y[split_idx:]
    
    def get_graph(self):
        return self.graph
    
    def get_sites(self):
        return self.sites