import pandas as pd


class TestFunctions:
    """
    Class containing test functions for battery storage system calculations.
    """

    def state_of_charge_check(
        df: pd.DataFrame, month: int, day: int, hour: int
    ) -> float:
        """
        Get the state of charge for a specific time.
        Args:
            df (pd.DataFrame): DataFrame with state of charge data.
            month (int): Month for which data is needed.
            day (int): Day for which data is needed.
            hour (int): Hour for which data is needed.
        Returns:
            float: State of charge value.
        """
        return df.loc[
            (df["Month"] == month) & (df["Day"] == day) & (df["Hour"] == hour),
            "State_of_Charge",
        ].iloc[0]

    def recharge_check(df: pd.DataFrame, month: int, day: int, hour: int) -> float:
        """
        Get the total recharge (energy charged + regulation down) for a specific time.
        Args:
            df (pd.DataFrame): DataFrame with recharge data.
            month (int): Month for which data is needed.
            day (int): Day for which data is needed.
            hour (int): Hour for which data is needed.
        Returns:
            float: Total recharge value.
        """
        #  Filter DataFrame rows where the Month, Day, and Hour match the given inputs for energy charged  and regulation_down deployed
        return (
            df.loc[
                (df["Month"] == month) & (df["Day"] == day) & (df["Hour"] == hour),
                "Energy_Charged",
            ].iloc[0]
            + df.loc[
                (df["Month"] == month) & (df["Day"] == day) & (df["Hour"] == hour),
                "Regulation_Down",
            ].iloc[0]
        )

    def discharge_check(df: pd.DataFrame, month: int, day: int, hour: int) -> float:
        """
        Get the total discharge (energy discharged + regulation up) for a specific time.
        Args:
            df (pd.DataFrame): DataFrame with discharge data.
            month (int): Month for which data is needed.
            day (int): Day for which data is needed.
            hour (int): Hour for which data is needed.
        Returns:
            float: Total discharge value.
        """
        #  Filter DataFrame rows where the Month, Day, and Hour match the given inputs for energy discharged and regulation_up deployed
        return (
            df.loc[
                (df["Month"] == month) & (df["Day"] == day) & (df["Hour"] == hour),
                "Energy_Discharged",
            ].iloc[0]
            + df.loc[
                (df["Month"] == month) & (df["Day"] == day) & (df["Hour"] == hour),
                "Regulation_UP",
            ].iloc[0]
        )

    def energy_check(df: pd.DataFrame, month: int, day: int, hour: int) -> float:
        """
        Get the total energy (energy charged + energy discharged) for a specific time.
        Args:
            df (pd.DataFrame): DataFrame with energy data.
            month (int): Month for which data is needed.
            day (int): Day for which data is needed.
            hour (int): Hour for which data is needed.
        Returns:
            float: Total energy value.
        """
        #  Filter DataFrame rows where the Month, Day, and Hour match the given inputs for energy charged and discharged 
        return (
            df.loc[
                (df["Month"] == month) & (df["Day"] == day) & (df["Hour"] == hour),
                "Energy_Charged",
            ].iloc[0]
            + df.loc[
                (df["Month"] == month) & (df["Day"] == day) & (df["Hour"] == hour),
                "Energy_Discharged",
            ].iloc[0]
        )

    def regulation_up_check(df: pd.DataFrame, month: int, day: int, hour: int) -> float:
        """
        Get the regulation up value for a specific time.
        Args:
            df (pd.DataFrame): DataFrame with regulation up data.
            month (int): Month for which data is needed.
            day (int): Day for which data is needed.
            hour (int): Hour for which data is needed.
        Returns:
            float: Regulation up value.
        """

        #  Filter DataFrame rows where the Month, Day, and Hour match the given inputs for regulation_up
        return df.loc[
            (df["Month"] == month) & (df["Day"] == day) & (df["Hour"] == hour),
            "Regulation_UP",
        ].iloc[0]

    def regulation_down_check(
        df: pd.DataFrame, month: int, day: int, hour: int
    ) -> float:
        """
        Retrieve the Regulation Down value for a specific month, day, and hour.
        Args:
            df: pd.DataFrame - DataFrame containing the data.
            month: int - Month as an integer (1-12).
            day: int - Day of the month as an integer (1-31).
            hour: int - Hour of the day as an integer (0-23).
        Returns:
            float - The Regulation_Down value for the specified month, day, and hour.
        """
        # Filter DataFrame rows where the Month, Day, and Hour match the given inputs
        return df.loc[
            (df["Month"] == month) & (df["Day"] == day) & (df["Hour"] == hour),
            "Regulation_Down",
        ].iloc[0]

    def number_of_cycles_check(df: pd.DataFrame, month: int, day: int, max_d: float, max_r: float) -> int:
        """
        Calculate the number of full charge and discharge cycles for a given month and day.
        Args:
            df: pd.DataFrame - DataFrame containing the data.
            month: int - Month as an integer (1-12).
            day: int - Day of the month as an integer (1-31).
            max_d: float - Maximum discharge value.
            max_r: float - Maximum charge value.
        Returns:
        int - The number of full charge and discharge cycles for the specified day and month.
        """
        cycles = 0
        full_charge = 0
        full_discharge = 0
        # Calculate the total Energy_Charged and Regulation_Down for the day
        total_charge = (
            df[(df["Day"] == day) & (df["Month"] == month)]["Energy_Charged"].sum()
            + df[(df["Day"] == day) & (df["Month"] == month)]["Regulation_Down"].sum()
        )
        # Calculate the total Energy_Discharged and Regulation_UP for the day
        total_discharge = (
            df[(df["Day"] == day) & (df["Month"] == month)]["Energy_Discharged"].sum()
            + df[(df["Day"] == day) & (df["Month"] == month)]["Regulation_UP"].sum()
        )
        # Check if the total charge equals max_r and set full_charge to 1 if true
        if total_charge == 2*max_r:
            full_charge = 1
        # Check if the total discharge equals max_d and set full_discharge to 1 if true
        if total_discharge == 2*max_d:
            full_discharge = 1
        # If both full charge and full discharge occurred, increment the cycles counter
        if full_charge == 1 and full_discharge == 1:
            cycles += 1
        return cycles
