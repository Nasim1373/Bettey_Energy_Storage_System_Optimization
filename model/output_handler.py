import pandas as pd


class OutputHandler:
    """
    Class to handle the output of the optimization solution.
    """
    def __init__(
        self,
        solution: object,
        desired_months: int,
        desired_days: int,
        set_of_months: list,
        set_of_days:list,
        q_max_d: float,
        q_max_r: float,
        interval: list,
        energy_price_params: dict,
        regulation_up_params: dict,
        regulation_down_params: dict,
        output_path: str,
        file_names: list
    ):
        """
        Initialize the OutputHandler.
        Args:
            solution (object): The optimization solution.
            desired_months (int): The month for which the optimization ran.
            desired_days (int): The day for which the optimization ran.
            set_of_months (list): The set of months for which the optimization ran.
            set_of_days  (list): The set of days for which the optimization ran.
            q_max_d (float): Nameplate power capacity.
            q_max_r (float): Nameplate power capacity.
            energy_price_params (dict): Dictionary of energy prices.
            regulation_up_params (dict): Dictionary of regulation up prices.
            regulation_down_params (dict): Dictionary of regulation down prices.
            interval (list): List of tuples representing time intervals.
            output_path (str): Path to save the output files.
            file_names (list): List of file names for the output files.
        """
        self.solution = solution  # The optimization solution
        self.desired_months = desired_months  # The month for which the optimization ran.
        self.desired_days = desired_days  # The day for which the optimization ran.
        self.set_of_months = set_of_months  # The set of months for which the optimization ran.
        self.set_of_days = set_of_days  # The set of days for which the optimization ran.
        self.q_max_d = q_max_d  # Nameplate power capacity.
        self.q_max_r = q_max_r  # Nameplate power capacity.
        self.energy_price_params = energy_price_params  # Dictionary of energy prices
        self.regulation_up_params = regulation_up_params  # Dictionary of regulation up prices.
        self.regulation_down_params =regulation_down_params  # Dictionary of regulation down prices.
        self.interval = interval  # List of tuples representing time intervals
        self.output_path = output_path  # Path to save the output files
        self.file_names = file_names  # List of file names for the output files

    def save_all_outputs(self):
        """
        Save all outputs
        """
        # Save the state of charge to a CSV file
        self.save_state_of_charge()
        # Save the schedule (charge, discharge, regulation) to a CSV file
        self.save_schedule()
        # Save the daily revenue to a CSV file
        schedule_daily=self.save_schedule_daily()
        # Save the total revenue to a CSV file
        self.save_total_revenue()
        # Save the total cycles per day to a CSV file
        total_cycles_daily=self.save_total_cycle_per_day()
        # Save the total cycles per month to a CSV file
        self.save_total_cycles()

    def save_state_of_charge(self):
        """
        Save the state of charge to a CSV file.
        """
        # Create a DataFrame for state of charge and save
        state_of_charges = pd.DataFrame(
            [
                {
                    "Hour": i,
                    "Day": self.desired_days,
                    "Month": self.desired_months,
                    "State_of_Charge": self.solution.get_value(
                        f"state_of_charge_{i}"
                    ),
                }
                for  i  in range(1,25)
            ]
        ) 
        # Append `state_of_charges` to the current data
        mode = 'w' if self.desired_months == 1 and  self.desired_days == 1 else 'a'  # 'w' (write) for the first iteration, 'a' (append) otherwise
        header = self.desired_months == self.set_of_months[0] and self.desired_days == self.set_of_days[0]  # Include the header only in the first write otherwise no need
        state_of_charges.to_csv(
            self.output_path  + '/' + self.file_names[0],
            mode=mode,
            header=header,
            index=False
        )

    def save_schedule(self):
        """
        Save the schedule (charge, discharge, regulation) to a CSV file.
        """
        # Create a DataFrame for schedule and save
        schedule = pd.DataFrame(
            [
                {
                    "Hour": i,
                    "Day": self.desired_days,
                    "Month": self.desired_months,
                    "Energy_Charged": self.solution.get_value(
                        f"quantity_charge_{i}"
                    ),
                    "Energy_Discharged": self.solution.get_value(
                        f"quantity_discharge_{i}"
                    ),
                    "Regulation_UP": self.solution.get_value(
                        f"quantity_regulation_up_{i}"
                    ),
                    "Regulation_Down": self.solution.get_value(
                        f"quantity_regulation_down_{i}"
                    ),
                }
                for  i  in range(1,25)
            ]
        )
        # Append `schedule` to the current data
        mode = 'w' if self.desired_months == 1 and  self.desired_days == 1 else 'a'
        header = self.desired_months == self.set_of_months[0] and self.desired_days == self.set_of_days[0]
        schedule.to_csv(
            self.output_path  + '/' + self.file_names[1],
            mode=mode,
            header=header,
            index=False
        )

    def print_summary(self):
        """
        Print the summary of the optimization solution.
        """
        print(
            "Objective Value:", self.solution.get_objective_value()
        )  # Print objective value of the solution

    def save_total_cycle_per_day(self):
        """
        Save the total cycles per month to a CSV file.
        """
        # Create a set of unique months from intervals
        month_set = {(k, j) for k, _, j in self.interval}
        day_set = {j for __, _, j in self.interval}
        # Precompute values for all time periods (1 to 24) across intervals (months)
        charge_values = {
        (self.desired_months, self.desired_days): sum(
                self.solution.get_value(f"quantity_charge_{i}")
                for i in range(1, 25)
            )
            
        }
        reg_down_values = {
        (self.desired_months, self.desired_days): sum(
                self.solution.get_value(f"quantity_regulation_down_{i}")
                for i in range(1, 25)
            )
            
        }
        discharge_values = {
        (self.desired_months, self.desired_days): sum(
                self.solution.get_value(f"quantity_discharge_{i}")
                for i in range(1, 25)
            )
        
        }
        reg_up_values = {
        (self.desired_months, self.desired_days): sum(
                self.solution.get_value(f"quantity_regulation_up_{i}")
                for i in range(1, 25)
            )
        
        }
        # Combine precomputed values into a single dictionary for quick lookup
        full_charge_discharge = {
        (self.desired_months, self.desired_days): (
                (charge_values[(self.desired_months, self.desired_days)] + reg_down_values[(self.desired_months, self.desired_days)] == self.q_max_r),
                (discharge_values[(self.desired_months, self.desired_days)] + reg_up_values[(self.desired_months, self.desired_days)] == self.q_max_d),
            )
        
        }
        # Calculate cycles for each month and save
        cycles_dict = {(self.desired_months, self.desired_days): 0}
        for (self.desired_months, self.desired_days), (full_charge, full_discharge) in full_charge_discharge.items():
            if full_charge and full_discharge:
                cycles_dict[self.desired_months, self.desired_days] += 1
        # Create a DataFrame for total cycles
        total_cycles_daily = pd.DataFrame(
            [
                { "Month": self.desired_months,  "Day": self.desired_days, "Total_Cycle": cycles_dict[self.desired_months, self.desired_days] }
            ]
        )
        # Append `total_cycles` to the current data
        mode = 'w' if self.desired_months == self.set_of_months[0] and self.desired_days == self.set_of_days[0] else 'a'
        header = self.desired_months == self.set_of_months[0] and self.desired_days == self.set_of_days[0]  
        total_cycles_daily.to_csv(
            self.output_path  + '/' + self.file_names[2],
            mode=mode,
            header=header,
            index=False
        )
        return total_cycles_daily

    def save_schedule_daily(self):
        """
        Save the total daily revenue to a CSV file.
        """
        # Create a DataFrame for daily schedule and save
        schedule_daily = pd.DataFrame(
            [
                {
                    "Month": self.desired_months,
                    "Day":self.desired_days,
                    "Tota_Daily_Revenue": self.solution.get_objective_value()
                }
                
            ]
        )
        # Append `schedule_daily` to the current data
        mode = 'w' if self.desired_months == self.set_of_months[0] and self.desired_days == self.set_of_days[0] else 'a'
        header = self.desired_months == self.set_of_months[0] and self.desired_days == self.set_of_days[0]  
        schedule_daily.to_csv(
            self.output_path  + '/' + self.file_names[4],
            mode=mode,
            header=header,
            index=False
        )


    def save_total_revenue(self):
        """
        Save the total revenue to a CSV file.
        """
        # Process total revenue schedule and save
        total_revenue=pd.read_csv(self.output_path  + '/' + self.file_names[4])

        total_revenue = pd.DataFrame(
            [{"Tota_Revenue": total_revenue["Tota_Daily_Revenue"].sum()}]
        )
        total_revenue.to_csv(self.output_path  + '/' + self.file_names[3])

    def save_total_cycles(self):
        """
        Save the total monthly cycles to a CSV file.
        """
        # Process  total cycles per month 
        total_cycles_daily=pd.read_csv(self.output_path  + '/' + self.file_names[2])

        monthly_cycles = total_cycles_daily.groupby('Month')['Total_Cycle'].sum().reset_index()
        monthly_cycles.to_csv(self.output_path  + '/' + self.file_names[5])