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
        # Continuous variable for regulation up quantity at hour i in day j month k
        self.quantity_regulation_up = self.model.continuous_var_dict(
            (hour for hour in self.hour_set), name="quantity_regulation_up"
        )
        # Continuous variable for regulation down quantity at hour i in day j month k
        self.quantity_regulation_down = self.model.continuous_var_dict(
            (hour for hour in self.hour_set), name="quantity_regulation_down"
        )
        # Continuous variable for state of charge at hour i in day j month k
        self.state_of_charge = self.model.continuous_var_dict(
            (hour for hour in self.hour_set), name="state_of_charge"
        )
        # self.discharge_cycle = self.model.binary_var_dict(
        #     (hour for hour in self.hour_set), name="discharge_cycle_activation"
        # )  # Binary variable for discharge cycle activation at hour i in day j month k
        # self.charge_cycle = self.model.binary_var_dict(
        #     (hour for hour in self.hour_set), name="charge_cycle_activation"
        # )  # Binary variable for charge cycle activation at hour i in day j month k
        # self.regulation_up_cycle = self.model.binary_var_dict(
        #     (hour for hour in self.hour_set), name="regulation_up_cycle_activation"
        # )  # Binary variable for regulation up cycle activation at hour i in day j month k
        # self.regulation_down_cycle = self.model.binary_var_dict(
        #     (hour for hour in self.hour_set), name="regulation_down_cycle_activation"
        # )  # Binary variable for regulation down cycle activation at hour i in day j month k

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
        # Maximizing profit by balancing discharge, charge, reg up, and reg down
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
            + self.model.sum(
                self.quantity_regulation_down[hour] * regulation_down_params[self.month, hour,self.day ]
                for hour in self.hour_set
            )
        )

    def add_constraints(
        self,
        interval: list,
        initial_charge: float,
        missing_energy: list,
        missing_regulation_up: list,
        missing_regulation_down: list,
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
                    + self.lambda_c
                    * self.lambda_reg
                    * self.quantity_regulation_up[hour]
                    + self.lambda_c
                    * self.lambda_reg
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
                    self.state_of_charge[self.hour_set[0]] == initial_charge,
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

        # # Discharge, charge, and regulation cycle constraints: making sure the decision varibles for each of them takes value only if there is an active cycle for each category
        # [
        #     self.model.add_constraint(
        #         self.quantity_discharge[hour]
        #         <= self.q_max_d * self.discharge_cycle[hour],
        #         f"discharge_cycle_{self.month,hour,self.day}",
        #     )
        #     for hour in self.hour_set
        # ]
        # [
        #     self.model.add_constraint(
        #         self.quantity_charge[hour] <= self.q_max_r * self.charge_cycle[hour],
        #         f"charge_cycle_{self.month,hour,self.day}",
        #     )
        #     for hour in self.hour_set
        # ]
        # [
        #     self.model.add_constraint(
        #         self.quantity_regulation_up[hour]
        #         <= self.q_max_d * self.regulation_up_cycle[hour],
        #         f"quantity_regulation_up_cycle_{self.month,hour,self.day}",
        #     )
        #     for hour in self.hour_set
        # ]
        # [
        #     self.model.add_constraint(
        #         self.quantity_regulation_down[hour]
        #         <= self.q_max_r * self.regulation_down_cycle[hour],
        #         f"quantity_regulation_down_cycle_{self.month,hour,self.day}",
        #     )
        #     for hour in self.hour_set
        # ]

        # ## Maximum 1 cycle per day constraints
        # [
        #     self.model.add_constraint(
        #         self.model.sum(self.quantity_discharge[hour] for hour in range(1, 25))
        #         <= 1,
        #         f"discharge_cycle_constraint_{self.month,self.day}",
        #     )
        
        # ]
        # [
        #     self.model.add_constraint(
        #         self.model.sum(self.quantity_charge[hour] for hour in range(1, 25)) <= 1,
        #         f"charge_cycle_constraint_{self.month,self.day}",
        #     )
        
        # ]
        # [
        #     self.model.add_constraint(
        #         self.model.sum(self.quantity_regulation_up[hour] for hour in range(1, 25))
        #         <= 1,
        #         f"quantity_regulation_up_cycle_constraint_{self.month,self.day}",
        #     )
        
        # ]
        # [
        #     self.model.add_constraint(
        #         self.model.sum(
        #             self.quantity_regulation_down[hour] for hour in range(1, 25)
        #         )
        #         <= 1,
        #         f"quantity_regulation_down_cycle_constraint_{self.month,self.day}",
        #     )
        
        # ]

        # Charge and regulation down cycle constraints to satisfy the requiremnt of having maximum 1 cycle per day
        [
            self.model.add_constraint(
                self.model.sum(self.quantity_charge[hour] for hour in range(1, 25))
                + self.model.sum(
                    self.quantity_regulation_down[hour] for hour in range(1, 25)
                )
                <= self.q_max_r,
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
                <= self.q_max_d,
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
