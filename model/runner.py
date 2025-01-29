class BatteryStorageOptimization:
    """
    Class representing the process of optimizing a battery energy storage system using given data and an optimization model.
    """

    def __init__(self, data_handler: object, optimization_model: object, month: str, day : int ):
        """
        Initialize the BatteryStorageOptimization.
        Args:
            data_handler (object): A handler object to manage data inputs, cleaning, and processing.
            optimization_model (object): An instance of the optimization model class.
        """
        self.data_handler = data_handler  # Data handler for managing data inputs, cleaning, and processing
        self.optimization_model = (
            optimization_model  # Optimization model for the battery storage system
        )
        self.month=month # The month of running the model
        self.day=day # The day of running the model

    def run(self, desired_months: list, initial_state_of_charge: float, previous_day_state: float) -> tuple:
        """
        Run the optimization process for the battery storage system.
        Args:
            desired_months (list): The months for which the optimization is run.
            initial_state_of_charge (float): The initial state of charge of the battery.
        Returns:
            tuple: Solution of the optimization model and the intervals.
        """
        # Create variables for the optimization model
        self.optimization_model.create_variables(
            self.data_handler.energy_price_params.keys(),self.month,self.day,
        )
        # Set the objective function
        self.optimization_model.set_objective_function(
            self.data_handler.energy_price_params.keys(),
            self.data_handler.energy_price_params,
            self.data_handler.regulation_up_params,
            self.data_handler.regulation_down_params,
        )
        # Add constraints
        self.optimization_model.add_constraints(
            self.data_handler.energy_price_params.keys(),
            initial_state_of_charge,
            self.data_handler.missing_energy,
            self.data_handler.missing_regulation_up,
            self.data_handler.missing_regulation_down,
            previous_day_state
        )
        # Solve optimization model
        model,solution, q_max_d, q_max_r = (
            self.optimization_model.solve()
        )
        # Return the solutions
        return (
            model,
            solution,
            self.data_handler.energy_price_params.keys(),
            self.data_handler.energy_price_params,
            self.data_handler.regulation_up_params,
            self.data_handler.regulation_down_params,
            q_max_d,
            q_max_r,
        )
