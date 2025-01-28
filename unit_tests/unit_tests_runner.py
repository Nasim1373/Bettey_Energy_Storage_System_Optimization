import unittest
from itertools import product

import numpy as np
import pandas as pd
from unit_tests.test_functions import TestFunctions


class TestCalc(unittest.TestCase):
    """
    Unit tests for battery storage system calculations using unittest.
    """

    def setUp(self):
        """
        Initialize the parameters and load data from CSV files.
        """
        self.q_max_d = 100  # Nameplate of discharge power
        self.q_max_r = 100  # Nameplate of recharge power
        self.max_charge = 200  # Maximum charge capacity
        self.state_charge_df = pd.read_csv(
            "./data/output/state_of_charge.csv"
        )  # Load state of charge data
        self.optimal_df = pd.read_csv(
            "./data/output/schedule.csv"
        )  # Load optimal schedule data
        
        self.months = self.state_charge_df[
            "Month"
        ].unique()  # Extract the number of unique months

        self.days = self.state_charge_df.groupby("Month")["Day"].apply(lambda x: sorted(x.unique())).to_dict()  # Extract the number of unique days


        self.hours = self.state_charge_df[
            "Hour"
        ].unique()  # Extract the number of unique hours

    def test_state_of_charge_upper_bound(self):
        """
        Test that state of charge does not exceed the maximum charge limit.
        """
        for k,  j in product(self.months,self.hours):
            for i in  self.days[k]:
                with self.subTest(k=k, i=i, j=j):
                    result = TestFunctions.state_of_charge_check(
                        self.state_charge_df, k, i, j
                    )  # Calculate state of charge
                    self.assertLessEqual(
                        result,
                        self.max_charge,
                        f"Validation test for state of charge upper bound failed for Month {k}, Day {i}, Hour {j}",
                    )

    def test_state_of_charge_lower_bound(self):
        """
        Test that state of charge is not below zero.
        """
        for k,  j in product(self.months,self.hours):
            for i in  self.days[k]:
                with self.subTest(k=k, i=i, j=j):
                    result = TestFunctions.state_of_charge_check(
                        self.state_charge_df, k, i, j
                    )  # Calculate state of charge
                    self.assertGreaterEqual(
                        result,
                        0,
                        f"Validation test failed: Month={k}, Day={i}, Hour={j}, State of charge is below 0",
                    )

    def test_recharge_upper_bound(self):
        """
        Test that recharge does not exceed the maximum limit.
        """
        for k,  j in product(self.months,self.hours):
            for i in  self.days[k]:
                with self.subTest(k=k, i=i, j=j):
                    result = TestFunctions.recharge_check(
                        self.optimal_df, k, i, j
                    )  # Calculate recharge
                    self.assertLessEqual(
                        result,
                        self.q_max_r,
                        f"Validation test failed: Month={k}, Day={i}, Hour={j}, Recharge exceeds upper bound ({self.q_max_r})",
                    )

    def test_recharge_lower_bound(self):
        """
        Test that recharge is not below zero.
        """
        for k,  j in product(self.months,self.hours):
            for i in  self.days[k]:
                with self.subTest(k=k, i=i, j=j):
                    result = TestFunctions.recharge_check(
                        self.optimal_df, k, i, j
                    )  # Calculate recharge
                    self.assertGreaterEqual(
                        result,
                        0,
                        f"Validation test failed: Month={k}, Day={i}, Hour={j}, Recharge is below 0",
                    )

    def test_discharge_upper_bound(self):
        """
        Test that discharge does not exceed the maximum limit.
        """
        for k,  j in product(self.months,self.hours):
            for i in  self.days[k]:
                with self.subTest(k=k, i=i, j=j):
                    result = TestFunctions.discharge_check(
                        self.optimal_df, k, i, j
                    )  # Calculate discharge
                    self.assertLessEqual(
                        result,
                        self.q_max_d,
                        f"Validation test failed: Month={k}, Day={i}, Hour={j}, Discharge exceeds upper bound ({self.q_max_d})",
                    )

    def test_discharge_lower_bound(self):
        """
        Test that discharge is not below zero.
        """
        for k,  j in product(self.months,self.hours):
            for i in  self.days[k]:
                with self.subTest(k=k, i=i, j=j):
                    result = TestFunctions.discharge_check(
                        self.optimal_df, k, i, j
                    )  # Calculate discharge
                    self.assertGreaterEqual(
                        result,
                        0,
                        f"Validation test failed: Month={k}, Day={i}, Hour={j}, Discharge is below 0",
                    )

    def test_cycle_number(self):
        """
        Test that the number of cycles does not exceed the limit.
        """
        for k in self.months:
            for i in  self.days[k]:
                with self.subTest(k=k, i=i):  # Subtest for each combination
                    result = TestFunctions.number_of_cycles_check(
                        self.optimal_df, k, i, self.q_max_r, self.q_max_d
                    )  # Calculate the number of cycles
                    self.assertLessEqual(
                        result,
                        1,
                        f"Validation test for the number of cycles for Day {i} failed",
                    )
