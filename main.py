# main.py
"""
TBRGS - Traffic-Based Route Guidance System
Entry point for Assignment 2B

Run: python main.py
"""

import tkinter as tk

from data_processor import BorondaraDataProcessor
from travel_time import TravelTimeCalculator
from traffic_models import TrafficPredictor
from pathfinder import PathFinder
from gui import TBRGSApp


def main():
    print("\n" + "=" * 60)
    print("TBRGS - Traffic-Based Route Guidance System")
    print("COS30019 - Introduction to AI")
    print("Assignment 2B")
    print("=" * 60 + "\n")
    
    # Load data
    print("Step 1: Loading traffic data...")
    processor = BorondaraDataProcessor()
    processor.load_all_data()
    
    # Prepare ML dataset
    print("\nStep 2: Preparing ML training data...")
    X_train, X_test, y_train, y_test = processor.create_ml_dataset()
    print(f"    Training samples: {len(X_train)}")
    print(f"    Test samples: {len(X_test)}")
    
    # Train models
    print("\nStep 3: Training traffic prediction models...")
    predictor = TrafficPredictor()
    predictor.train_lstm(X_train, y_train, X_test, y_test)
    predictor.train_gru(X_train, y_train, X_test, y_test)
    predictor.train_xgboost(X_train, y_train, X_test, y_test)
    
    # Initialize components
    print("\nStep 4: Initializing route guidance system...")
    tt_calc = TravelTimeCalculator()
    pathfinder = PathFinder(processor.get_graph(), tt_calc, predictor)
    
    # Launch GUI
    print("\nStep 5: Starting GUI...\n")
    root = tk.Tk()
    app = TBRGSApp(root, processor, pathfinder, predictor)
    root.mainloop()


if __name__ == "__main__":
    main()