from docplex.mp.model import Model


class OptimizationModel():
    """
    Class representing an optimization model for battery energy storage system in a simplified wholesale market.
    """
    def __init__(
        self,
        data_handler: object,
        max_charge: float = 200.0,
        q_max_d: float = 100.0,
        q_max_r: float = 100.0,
        lambda_c: float = 0.9,
        lambda_reg: float = 0.1,
    
    ):
        """
        Initialize the OptimizationModel.
        Args:
            data_handler (object): Data handler object to manage data inputs.
            max_charge (float): Nameplate energy capacity.
            q_max_d (float): Nameplate power capacity.
            q_max_r (float): Nameplate power capacity.
            lambda_c (float): Efficiency of charge/discharge.
            lambda_reg (float): Regulation rate.
        """
        # Initialize the optimization model needs
        self.data_handler = data_handler  # Data handler for managing data inputs
        self.max_charge = max_charge  # Nameplate energy capacity.
        self.q_max_d = q_max_d  # Maximum discharge quantity
        self.q_max_r = q_max_r  # Maximum charge quantity
        self.lambda_c = lambda_c  # Efficiency of charge/discharge
        self.lambda_reg = lambda_reg  # Efficiency of regulation
    def create_variables(self, interval: list,desired_month:str,day:int):
        """
        Create decision variables for the optimization model.
        Args:
            interval (list): List of tuples representing time intervals.
        """
        # Create an instance of the Model class
        self.model = Model(
            name="Battery_Energy_Storage_System"+str(desired_month)+str(day)
        )
        # Get the set of hours fpr a specific day in a specific month
        self.hour_set = range(1, 25)
        self.month = desired_month
        self.day = day

        # Create decision variables for the optimization model
        # Continuous variable for discharge quantity at hour i in day j month k
        self.quantity_discharge = self.model.continuous_var_dict(
            (hour for hour in self.hour_set), name="quantity_discharge"
        )
        # Continuous variable for charge quantity at hour i in day j month k
        self.quantity_charge = self.model.continuous_var_dict(
            (hour for hour in self.hour_set), name="quantity_charge"
        )
        # Continuous variable for regulation up capacity reserved at hour i in day j month k
        self.quantity_regulation_up_capcity = self.model.continuous_var_dict(
            (hour for hour in self.hour_set), name="quantity_regulation_up_capacity"
        )
        # Continuous variable for regulation down capacity reserved at hour i in day j month k
        self.quantity_regulation_down_capacity = self.model.continuous_var_dict(
            (hour for hour in self.hour_set), name="quantity_regulation_down_capacity"

        )
        # Continuous variable for regulation up quantity deployed  at hour i in day j month k
        self.quantity_regulation_up = self.model.continuous_var_dict(
            (hour for hour in self.hour_set), name="quantity_regulation_up_deployed"
        )
        # Continuous variable for regulation down quantity  deployed at hour i in day j month k
        self.quantity_regulation_down = self.model.continuous_var_dict(
            (hour for hour in self.hour_set), name="quantity_regulation_down_deployed")
        # Continuous variable for state of charge at hour i in day j month k
        self.state_of_charge = self.model.continuous_var_dict(
            (hour for hour in self.hour_set), name="state_of_charge"
        )

    def set_objective_function(
        self,
        interval: list,
        energy_price_params: dict,
        regulation_up_params: dict,
        regulation_down_params: dict,
    ):
        """
        Set the objective function for the optimization model.
        Args:
            interval (list): List of tuples representing time intervals.
            energy_price_params (dict): Dictionary of energy prices.
            regulation_up_params (dict): Dictionary of regulation up prices.
            regulation_down_params (dict): Dictionary of regulation down prices.
        """
        # Maximizing profit by balancing discharge, charge, reg up, and reg down deployed and capacities
        self.model.maximize(
            self.model.sum(
                self.quantity_discharge[hour] * energy_price_params[self.month, hour,self.day ]
                for hour in self.hour_set
            )
            - self.model.sum(
                self.quantity_charge[hour] * energy_price_params[self.month, hour,self.day ]
                for hour in self.hour_set
            )
            + self.model.sum(
                self.quantity_regulation_up[hour] * regulation_up_params[self.month, hour,self.day ]
                for hour in self.hour_set
            )
            - self.model.sum(
                self.quantity_regulation_down[hour] * regulation_down_params[self.month, hour,self.day ]
                for hour in self.hour_set
            )
            + self.model.sum(
                self.quantity_regulation_up_capcity[hour] * regulation_up_params[self.month, hour,self.day ]
                for hour in self.hour_set
            )
            + self.model.sum(
                self.quantity_regulation_down_capacity[hour] * regulation_down_params[self.month, hour,self.day ]
                for hour in self.hour_set
            )
        )

    

    def add_constraints(
        self,
        interval: list, # List of tuples representing time intervals.
        initial_charge: float, # Initial charge of the battery at initial day and hour.
        missing_energy: list, # List of tuples representing intervals with missing energy data.
        missing_regulation_up: list, # List of tuples representing intervals with missing regulation up data.
        missing_regulation_down: list, # List of tuples representing intervals with missing regulation down data.
        past_day_state_of_charge: float, # The state of charge at the end of the previous day
    ):
        """
        Add constraints to the optimization model.
        Args:
            interval (list): List of tuples representing time intervals.
            initial_charge (float): Initial charge of the battery at initial day and hour.
            missing_energy (list): List of tuples representing intervals with missing energy data.
            missing_regulation_up (list): List of tuples representing intervals with missing regulation up data.
            missing_regulation_down (list): List of tuples representing intervals with missing regulation down data.
        """
        # State of charge constraints to keep track of all the battery changes in charge due to charging, discharge, regulation up and down
        [
            (
                self.model.add_constraint(
                    self.state_of_charge[hour]
                    == self.state_of_charge[hour-1]
                    + self.lambda_c * self.quantity_charge[hour]
                    - self.lambda_c * self.quantity_discharge[hour]
                    - self.lambda_c
                    * self.quantity_regulation_up[hour]
                    + self.lambda_c
                    * self.quantity_regulation_down[hour],
                    f"state_of_charge_{self.month,hour,self.day}",
                )
                if hour > 1
                else None
            )
            for hour in self.hour_set
        ]

        # State of charge initial values : the initial state of charge at the beginning of each day equals the state of charge at the end of the previous day
        # Assumtion is that no charge loss happen due to environment condistions
        [
            (
                self.model.add_constraint(
                    self.state_of_charge[self.hour_set[0]] == past_day_state_of_charge,
                    f"initial_state_of_charge{self.month,self.day}",
                )
                if self.day > 1
                else None
            )
            
        ]
        # State of charge initial values : the initial state of charge at the beginning of the first day based on the given value
        [   self.model.add_constraint(
                self.state_of_charge[self.hour_set[0]] == initial_charge,
            f"initial_state_of_charge_day_1{self.month,self.day}",
        )
        if self.day == 1
        else None
        ]
        # State of charge upper bound constraints
        [
            self.model.add_constraint(
                self.state_of_charge[hour] <= self.max_charge,
                f"state_of_charge_upper_bound_{self.month,hour,self.day}",
            )
            for hour in self.hour_set
        ]
        # State of charge lower bound constraints
        [
            self.model.add_constraint(
                self.state_of_charge[hour] >= 0, f"state_of_charge_lower_bound_{self.month,hour,self.day}"
            )
            for hour in self.hour_set
        ]
        # Charge of battery upper bound constraints based on nameplate power value given in the model
        [
            self.model.add_constraint(
                self.quantity_charge[hour] + self.quantity_regulation_down[hour]
                <= self.q_max_r,
                f"recharge_upper_bound_{self.month,hour,self.day}",
            )
            for hour in self.hour_set
        ]
        # Charge of battery lower bound constraints
        [
            self.model.add_constraint(
                self.quantity_charge[hour] + self.quantity_regulation_down[hour] >= 0,
                f"recharge_lower_bound_{self.month,hour,self.day}",
            )
            for hour in self.hour_set
        ]
        # Discharge of battery upper bound constraints based on Nameplate power value given in the model
        [
            self.model.add_constraint(
                self.quantity_discharge[hour] + self.quantity_regulation_up[hour]
                <= self.q_max_d,
                f"discharge_upper_bound_{self.month,hour,self.day}",
            )
            for hour in self.hour_set
        ]
        # Discharge of battery lower bound constraints
        [
            self.model.add_constraint(
                self.quantity_discharge[hour] + self.quantity_regulation_up[hour] >= 0,
                f"discharge_lower_bound_{self.month,hour,self.day}",
            )
            for hour in self.hour_set
        ]

        
        # Relation of regulation up deployed and regulation up capacity 
        [
            
                self.model.add_constraint(
                    self.quantity_regulation_up[hour] -self.quantity_regulation_up_capcity[hour]* self.lambda_reg==0,
                    f"deployment_of_reg_up_{self.month,self.day}",
                )
                for hour in self.hour_set
            
            
        ]


        #Relation of regulation down deployed and regulation down capacity 
        [
            
                self.model.add_constraint(
                    self.quantity_regulation_down[hour] -self.quantity_regulation_down_capacity[hour]* self.lambda_reg==0,
                    f"deployment_of_reg_down_{self.month,self.day}",
                )
                for hour in self.hour_set
            
            
        ]

        # Handling the missing hours in each day: if an hour is missed in data we will not bid that hour so the charge, discharge, regulation up and downs should be zero for that hour
        [
            self.model.add_constraint(
                self.quantity_discharge[hour] + self.quantity_charge[hour] == 0,
                f"missing_energy_{self.month,hour,self.day}",
            )
            for (self.month, hour, self.day) in missing_energy
        ]
        [
            self.model.add_constraint(
                self.quantity_regulation_up[hour] == 0, f"missing_regulation_up_{self.month,hour,self.day}"
            )
            for (self.month, hour, self.day) in missing_regulation_up
        ]
        [
            self.model.add_constraint(
                self.quantity_regulation_down[hour] == 0,
                f"missing_regulation_down_{self.month,hour,self.day}",
            )
            for (self.month, hour, self.day) in missing_regulation_down
        ]


        # Charge and regulation down cycle constraints to satisfy the requiremnt of having maximum 1 cycle per day
        [
            self.model.add_constraint(
                self.model.sum(self.quantity_charge[hour] for hour in range(1, 25))
                + self.model.sum(
                    self.quantity_regulation_down[hour] for hour in range(1, 25)
                )
                <= self.max_charge,
                f"charge_cycle_constraint_{self.month,self.day}",
            )
            
        ]
        # Discharge and regulation up cycle constraints to satisfy the requiremnt of having maximum 1 cycle per day
        [
            self.model.add_constraint(
                self.model.sum(self.quantity_discharge[hour] for hour in range(1, 25))
                + self.model.sum(
                    self.quantity_regulation_up[hour] for hour in range(1, 25)
                )
                <= self.max_charge,
                f"discharge_cycle_constraint_{self.month,self.day}",
            )
        
        ]

    def solve(self) -> object:
        """
        Solve the optimization model.
        Returns:
            object: Solution of the optimization model.
        """
        # Export the model file to lp format
        self.model.export("./data/output/model.lp")
        return self.model, self.model.solve(), self.q_max_d, self.q_max_r
