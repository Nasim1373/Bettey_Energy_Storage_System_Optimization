import os
import unittest
from data_preprocess.data_process import DataProcess
from data_preprocess.data_handler import DataHandler
from model.optimization_model import OptimizationModel
from model.output_handler import OutputHandler
from model.runner import BatteryStorageOptimization
from unit_tests import unit_tests_runner


class OptimizationWorkflow:
    """
    High-level class to handle the battery storage optimization workflow:
        - Manage input and output data.
        - Run the optimization model.
        - Validate the outputs of the optimization.
    """
    def __init__(self, input_path, output_path, energy_files, months, initial_state_of_charge=100):
        self.input_path = input_path
        self.output_path = output_path
        self.energy_files = energy_files
        self.months = months
        self.initial_state_of_charge = initial_state_of_charge

    def validate_paths(self):
        """
        Ensures that the input and output paths exists. Create the output folder if it does not exist.
        """
        if not os.path.exists(self.input_path):
            raise FileNotFoundError(f"Input path does not exist: {self.input_path}")
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

    def run_optimization_workflow(self):
        """
        Executes the entire battery storage optimization workflow.
        """
        # Clean the output folder
        for file in os.listdir('data/output'):
            if file.endswith('.csv'):
                os.remove(os.path.join('data/output/', file))
        data_handler = DataHandler(self.input_path, self.energy_files)
        optimization_model = OptimizationModel(data_handler)
        for month in self.months:
            for day in data_handler.data_loader(month):
                print(f"Running optimization for month {month}, day {day}")
                # Perform optimization for the month and day
                self.run_optimization(data_handler, optimization_model, month, day)
        # Update the database with output data
        data_process = DataProcess()
        data_process.connect_db(db_dir='data/database.db')
        # Optimal schedule data
        data_process.create_db_table_from_csv(
            csv_dir='data/output/schedule.csv',
            table_name='schedule',
            column_formats={'Hour': 'INTEGER', 'Day': 'INTEGER', 'Month': 'INTEGER', 'Energy_Charged': 'REAL', 'Energy_Discharged': 'REAL', 'Regulation_UP': 'REAL', 'Regulation_Down': 'REAL'},
            overwrite_table=True
        )
        # State of charge data
        data_process.create_db_table_from_csv(
            csv_dir='data/output/state_of_charge.csv',
            table_name='state_of_charge',
            column_formats={'Hour': 'INTEGER', 'Day': 'INTEGER', 'Month': 'INTEGER', 'State_of_Charge': 'REAL'},
            overwrite_table=True
        )
        data_process.disconnect_db()

    def run_optimization(self, data_handler, optimization_model, month, day):
        """
        Run the optimization model for a specific month and day.
        Args:
            data_handler (DataHandler): Instance of the DataHandler class.
            optimization_model (OptimizationModel): Instance of the OptimizationModel class.
            month (int): The month being optimized.
            day (int): The day being optimized.
        """
        # Initialize/build the optimization model
        battery_optimization = BatteryStorageOptimization(
            data_handler, optimization_model, month, day
        )
        # Optimize the model
        results = battery_optimization.run(
            desired_months=month, initial_state_of_charge=self.initial_state_of_charge
        )
        # Unpack the results
        (
            model,
            optimal_solution,
            interval,
            energy_price_params,
            regulation_up_params,
            regulation_down_params,
            q_max_d,
            q_max_r
        ) = results
        # Save the outputs
        self.handle_outputs(
            optimal_solution,
            month,
            day,
            q_max_d,
            q_max_r,
            interval,
            energy_price_params,
            regulation_up_params,
            regulation_down_params
        )
        model.end()

    def handle_outputs(
        self,
        optimal_solution,
        month,
        day,
        q_max_d,
        q_max_r,
        interval,
        energy_price_params,
        regulation_up_params,
        regulation_down_params
    ):
        """
        Save and summarize outputs for a specific optimization run.
        Args:
            optimal_solution (dict): Optimal schedule.
            month (int): The month being optimized.
            day (int): The day being optimized.
            q_max_d (float): Maximum discharge capacity.
            q_max_r (float): Maximum recharge capacity.
            interval (list): Time intervals for optimization.
            energy_price_params (dict): Energy price parameters.
            regulation_up_params (dict): Regulation up parameters.
            regulation_down_params (dict): Regulation down parameters.
        """
        output_handler = OutputHandler(
            solution=optimal_solution,
            desired_months=month,
            desired_days=day,
            q_max_d=q_max_d,
            q_max_r=q_max_r,
            interval=interval,
            energy_price_params=energy_price_params,
            regulation_up_params=regulation_up_params,
            regulation_down_params=regulation_down_params,
            output_path=self.output_path,
            file_names=[
                "state_of_charge.csv",
                "schedule.csv",
                "total_cycles_daily.csv",
                "total_revenue.csv",
                "daily_schedule.csv",
                "total_cycles.csv"
            ]
        )
        output_handler.save_all_outputs()
        output_handler.print_summary()

class TestRunner:
    """
    Class to perform the unit tests.
    """
    @staticmethod
    def run_tests():
        """
        Executes all unit tests.
        """
        print("Running the unit tests...")
        test_suite = unittest.TestLoader().loadTestsFromTestCase(
            unit_tests_runner.TestCalc
        )
        result = unittest.TextTestRunner().run(test_suite)
        if not result.wasSuccessful():
            print("Unit tests failed.")
            exit(1)
        print("Unit tests passed successfully.")


if __name__ == "__main__":
    # Determine th paths and parameters
    input_path = "./data/input"
    output_path = "./data/output"
    energy_files = ["energy_prices.csv", "regulation_prices.csv"]
    months = [1, 2]

    # Initialize and run the optimization model
    optimization_workflow = OptimizationWorkflow(
        input_path=input_path,
        output_path=output_path,
        energy_files=energy_files,
        months=months,
        initial_state_of_charge=100,
    )
    optimization_workflow.validate_paths()
    optimization_workflow.run_optimization_workflow()
    # Run the unit tests
    TestRunner.run_tests()
