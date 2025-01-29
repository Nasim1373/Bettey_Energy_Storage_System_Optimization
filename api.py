import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg') # Used for direct plotting from API to the browser
import random
from flask import Flask, request, jsonify, send_file
from io import BytesIO
from main import OptimizationWorkflow, TestRunner
from data_preprocess.data_process import DataProcess
from datetime import datetime
import numpy as np


class BidOptimizationAPI:
    # Specify variables
    default_input_path = "./data/input"
    default_output_path = "./data/output"
    default_energy_files = ["energy_prices.csv", "regulation_prices.csv"]

    def __init__(self, data_processor: DataProcess):
        # Initialize Flask app
        self.app = Flask(__name__)
        self.data_processor = data_processor
        # Register routes
        self.app.add_url_rule('/run-optimization', 'run_optimization', self.run_optimization, methods=['GET'])
        self.app.add_url_rule('/run-tests', 'run_tests', self.run_tests, methods=['GET'])

    def run_optimization(self):
        """
        Run the optimization model and return the plot
        URL (example): http://127.0.0.1:8080/run-optimization?months=11,12&initial_state_of_charge=100
        """
        try:
            # Parse inputs from the URL
            months_param = request.args.get('months')
            if not months_param:
                return jsonify({"error": "Missing 'months' query parameter."}), 400
            # Convert months to a list of integers
            months = [int(month.strip()) for month in months_param.split(',')]
            # Convert initial state of charge to a float
            initial_state_of_charge = int(request.args.get('initial_state_of_charge', 100))
            # Initialize and execute the optimization model
            optimization_workflow = OptimizationWorkflow(
                input_path=self.default_input_path,
                output_path=self.default_output_path,
                energy_files=self.default_energy_files,
                months=months,
                initial_state_of_charge=initial_state_of_charge,
            )
            optimization_workflow.validate_paths()
            optimization_workflow.run_optimization_workflow()
            # Generate the plot as an in-memory object
            plot_img_stream = self.generate_plot()
            # Return the plot directly as a response
            return send_file(plot_img_stream, mimetype='image/png')
        # If the run fails, return an error message
        except FileNotFoundError as e:
            return jsonify({"error": str(e)}), 404
        except Exception as e:
            return jsonify({"error": f"An error occurred: {str(e)}"}), 500

    def run_tests(self):
        """
        Endpoint to run unit tests.
        Returns:
            JSON response with test results showing whether the test was successful.
        """
        try:
            TestRunner.run_tests()
            return jsonify({"status": "success", "message": "All unit tests passed successfully."})
        except Exception as e:
            return jsonify({"error": f"Unit tests failed: {str(e)}"}), 500

    def generate_plot(self):
        """
        Generates a plot based on the months and returns it in-memory.
        """
        # Query data from the database (make sure the database is up-to-date)
        self.data_processor.connect_db(db_dir='data/database.db')
        bid_schedule_data = self.data_processor.get_data("SELECT * FROM schedule")
        state_of_charge_data = self.data_processor.get_data("SELECT * FROM state_of_charge")
        self.data_processor.disconnect_db()
        # Process data for plotting
        bid_schedule_data['date'] = bid_schedule_data.apply(lambda row: datetime(2023, int(row['month']), int(row['day']), int(row['hour']) - 1), axis=1)
        state_of_charge_data['date'] = state_of_charge_data.apply(lambda row: datetime(2023, int(row['month']), int(row['day']), int(row['hour']) - 1), axis=1)
        time = bid_schedule_data['date']
        series_data = {k + '_cusum': np.cumsum(v) for k, v in bid_schedule_data.items() if k in ['energy_charged', 'energy_discharged', 'regulation_up', 'regulation_down']}
        # Create a figure and axes
        fig, ax = plt.subplots(2, 1, figsize=(12, 10))
        for label, data in series_data.items():
            color = [random.random() for _ in range(3)]  # random RGB color
            ax[0].plot(time, data, label=label, color=color)
        ax[0].legend()
        ax[0].tick_params(axis='x', rotation=20)
        ax[1].plot(state_of_charge_data['date'], state_of_charge_data['state_of_charge'], label='state_of_charge', color=[random.random() for _ in range(3)])
        ax[1].legend()
        ax[1].tick_params(axis='x', rotation=20)
        fig.tight_layout()
        # Show the plots to the user by BytesIO
        img_stream = BytesIO()
        plt.savefig(img_stream, format='png')
        plt.close()
        img_stream.seek(0)
        return img_stream

    def run(self):
        """
        Runs the Flask application.
        """
        self.app.run(debug=True, host='127.0.0.1', port=8080)


# Main function to start the app
if __name__ == '__main__':
    # Run the optimization API
    bid_optimization_api = BidOptimizationAPI(data_processor=DataProcess())
    bid_optimization_api.run()
