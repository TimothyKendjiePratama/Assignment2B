# travel_time.py
"""
Traffic Flow to Travel Time Conversion
Based on Assignment 2B PDF v1.0

Formula: flow = -1.4648375 * speed^2 + 93.75 * speed
"""

import math
from config import (
    SPEED_LIMIT_KPH,
    INTERSECTION_DELAY_SEC,
    CAPACITY_FLOW,
    FREE_FLOW_THRESHOLD,
    FLOW_TO_SPEED_A,
    FLOW_TO_SPEED_B
)


class TravelTimeCalculator:
    def __init__(self, speed_limit=SPEED_LIMIT_KPH):
        self.speed_limit = speed_limit
        self.a = FLOW_TO_SPEED_A
        self.b = FLOW_TO_SPEED_B
        self.capacity_flow = CAPACITY_FLOW
        self.free_flow_threshold = FREE_FLOW_THRESHOLD
        self.intersection_delay_sec = INTERSECTION_DELAY_SEC

    def flow_to_speed(self, flow_per_hour):
        """
        Convert traffic flow to speed using quadratic relationship.

        For flow <= 351 veh/hr: speed = speed_limit (60 km/h)
        For flow > 351: solve quadratic equation

        Returns speed in km/h
        """
        if flow_per_hour <= self.free_flow_threshold:
            return self.speed_limit

        # Solve: a*s^2 + b*s - flow = 0
        # Using quadratic formula: s = [-b ± sqrt(b^2 - 4*a*(-flow))] / (2*a)
        # Which is: s = [-b ± sqrt(b^2 + 4*a*flow)] / (2*a)

        discriminant = self.b**2 - 4 * self.a * (-flow_per_hour)

        if discriminant < 0:
            return 32  # Default congested speed

        sqrt_disc = math.sqrt(discriminant)
        speed1 = (-self.b + sqrt_disc) / (2 * self.a)
        speed2 = (-self.b - sqrt_disc) / (2 * self.a)

        # Take positive speeds only
        speeds = [s for s in [speed1, speed2] if s > 0]

        if not speeds:
            return 32

        # Green line (under capacity): take higher speed
        # Red line (over capacity): take lower speed
        if flow_per_hour <= self.capacity_flow:
            result = max(speeds)
        else:
            result = min(speeds)

        # Cap at speed limit
        return min(result, self.speed_limit)

    def calculate_travel_time(self, distance_km, flow_per_15min):
        """
        Calculate travel time in minutes for a road segment.

        Args:
            distance_km: Distance between SCATS sites in km
            flow_per_15min: Predicted traffic flow (vehicles per 15 minutes)

        Returns:
            Travel time in minutes
        """
        hourly_flow = flow_per_15min * 4
        speed = self.flow_to_speed(hourly_flow)

        if speed <= 0.1:
            return 999  # Very slow traffic

        # Travel time in minutes = (distance / speed) * 60 + delay in minutes
        travel_time = (distance_km / speed) * 60 + (self.intersection_delay_sec / 60)
        return round(travel_time, 2)

    def test_conversion(self):
        """Test the flow-to-speed conversion with sample values"""
        print("\n" + "=" * 50)
        print("TESTING FLOW TO SPEED CONVERSION")
        print("=" * 50)
        print(f"{'Flow (veh/hr)':<18} {'Speed (km/h)':<15} {'Condition'}")
        print("-" * 50)

        test_flows = [0, 100, 351, 500, 800, 1000, 1500, 2000, 2500, 3000]

        for flow in test_flows:
            speed = self.flow_to_speed(flow)
            if flow <= 351:
                condition = "Free flow"
            elif flow <= 1500:
                condition = "Under capacity"
            else:
                condition = "Over capacity"
            print(f"{flow:<18} {speed:<15.2f} {condition}")