import pandas as pd


class DataHandler:
    def __init__(self, path: str, file_names: list):
        """
        Initialize DataHandler with a file path and list of file names needed to run the class.
        Parameters:
            path (str): Path to the directory containing the data files needed to run the class.
            file_names (list): List of file names to be read.
        """
        self.path = path
        self.file_names = file_names

    def read_data(self) -> tuple:
        """
        Read the energy and regulation price data from the provided data files.
        Returns:
            tuple: A tuple containing two DataFrames -
                (energy_price_df, regulation_price_df)
        """
        # Read energy price data
        energy_price_df = pd.read_csv(self.path + "/" + self.file_names[0])
        # Read regulation price data
        regulation_price_df = pd.read_csv(self.path + "/" + self.file_names[1])
        return energy_price_df, regulation_price_df

    def clean_data(
        self, energy_price_df: pd.DataFrame, regulation_price_df: pd.DataFrame
    ) -> tuple:
        """
        Clean missing values in energy and regulation price data.
        Parameters:
            energy_price_df (DataFrame): Energy price data.
            regulation_price_df (DataFrame): Regulation price data.
        Returns:
            tuple: A tuple containing cleaned DataFrames -
                (energy_price_df, regulation_price_df)
        """
        # Drop rows with missing values in the 'Price' column of energy_price_df
        energy_price_df.dropna(subset=["Price"], inplace=True)
        # Drop rows with missing values in the 'Regulation Up' column of regulation_price_df
        regulation_price_df.dropna(subset=["Regulation Up"], inplace=True)
        # Drop rows with missing values in the 'Regulation Down' column of regulation_price_df
        regulation_price_df.dropna(subset=["Regulation Down"], inplace=True)
        return energy_price_df, regulation_price_df

    def process_energy_price(self, energy_price_df: pd.DataFrame, desired_month: list) -> dict:
        """
        Clean energy price data to include only the desired month.
        Parameters:
            energy_price_df (DataFrame): DataFrame containing energy price data.
            desired_month (list): A list of months (1-12) like [1,2,3] to filter the data.
        Returns:
            dict: A dictionary with key-value pairs for energy prices.
        """
        # Make a copy of the energy price DataFrame
        energy_price_df = energy_price_df.copy()
        # Convert 'Operating Day' to datetime
        energy_price_df["Operating Day"] = pd.to_datetime(
            energy_price_df["Operating Day"], format="%m/%d/%y"
        )
        # Filter rows based on the desired month
        energy_price_df = energy_price_df[
            energy_price_df["Operating Day"].dt.month==desired_month
        ]
        # Create a list of tuples (day, hour, price)
        energy_price_df["Month_Day_Hour"] = list(
            zip(
                energy_price_df["Operating Day"].dt.month,
                energy_price_df["Operating Day"].dt.day,
                energy_price_df["Operating Hour"],
                energy_price_df["Price"],
            )
        )
        # Fill missing hours with zeros for prices to make all time units available for model
        return self.fill_missing_hour(
            {(k, j, i): l for (k, i, j, l) in energy_price_df["Month_Day_Hour"]}
        )

    def process_regulation_price(self, regulation_price_df: pd.DataFrame, desired_month: list, price_type: str) -> dict:
        """
        Process regulation price data to include only the desired month.
        Parameters:
            regulation_price_df (DataFrame): Regulation price data.
            desired_month (list): A list of months (1-12) like [1,2,3] to filter the data.
            price_type (str): Column name for the type of regulation price to process.
        Returns:
            dict: A dictionary with key-value pairs for for regulation prices.
        """
        # Make a copy of the regulation price DataFrame
        regulation_price_df = regulation_price_df.copy()
        # Convert 'Operating Day' to datetime
        regulation_price_df["Operating Day"] = pd.to_datetime(
            regulation_price_df["Operating Day"], format="%m/%d/%y"
        )
        # Filter rows based on the desired month
        regulation_price_df = regulation_price_df[
            regulation_price_df["Operating Day"].dt.month==desired_month
        ]
        # Create a list of tuples (day, hour, price)
        regulation_price_df["Month_Day_Hour"] = list(
            zip(
                regulation_price_df["Operating Day"].dt.month,
                regulation_price_df["Operating Day"].dt.day,
                regulation_price_df["Operating Hour"],
                regulation_price_df[price_type],
            )
        )
        # Fill missing hours with zeros for prices to make all time units available for the model
        return self.fill_missing_hour(
            {(k, j, i): l for (k, i, j, l) in regulation_price_df["Month_Day_Hour"]}
        )

    def fill_missing_hour(self, data_dict: dict) -> dict:
        """
        Fill missing hourly data by setting their price values to zero.
        Parameters:
            data_dict (dict): Day-hour data and their corresponding values.
        Returns:
            dict: A dictionary with key-value pairs for filled missing hours.
            dict: A dictionary with key pairs for missing hours in days.
        """
        # Fill missing hour slots with zeros
        return {
            **data_dict,
            **{
                (k, i, j): 0
                for k in {key[0] for key in data_dict}
                for j in {key[2] for key in data_dict}
                for i in range(1, 25)
                if (k, i, j) not in data_dict
            },
        }, {
            (k, i, j): 0
            for k in {key[0] for key in data_dict}
                for j in {key[2] for key in data_dict}
            for i in range(1, 25)
            if (k, i, j) not in data_dict
        }

    def data_loader(self, desired_months: list) -> tuple:
        """
        Run the data processing for the optimization model.
        Args:
            desired_months (list): The months for which the optimization is run.
            initial_state_of_charge (float): The initial state of charge of the battery.
        Returns:
            tuple: Solution of the optimization model and the intervals.
        """
        # Step 1: Read and clean data
        energy_price_df, regulation_price_df = (
            self.read_data()
        ) 
        energy_price_df, regulation_price_df = self.clean_data(
            energy_price_df, regulation_price_df
        ) 
        # Step 2: Process data
        self.energy_price_params, self.missing_energy = self.process_energy_price(
            energy_price_df, desired_months
        )  # energy prices
        self.regulation_up_params, self.missing_regulation_up = (
            self.process_regulation_price(
                regulation_price_df, desired_months, "Regulation Up"
            )
        )  # reg up prices
        self.regulation_down_params, self.missing_regulation_down = (
            self.process_regulation_price(
                regulation_price_df, desired_months, "Regulation Down"
            )
        )  # reg down prices
        return {day for (month, hour, day) in self.energy_price_params.keys() if month == desired_months}
