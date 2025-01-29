import csv
import sqlite3
import pandas as pd


class DataProcess:
    """
    Process data for the optimization model.
    """
    def __init__(self):
        pass

    def connect_db(self, db_dir: str = 'data/database.db'):
        """
        Connect to the SQLite database.
        Args:
            db_dir (str): Path to the SQLite database file.
        """
        self.db_connection = sqlite3.connect(db_dir)
        self.cursor = self.db_connection.cursor()

    def disconnect_db(self):
        """
        Close the connection to the SQLite database.
        """
        self.db_connection.close()

    def create_db_table_from_csv(self, csv_dir: str, table_name: str, column_formats: dict, overwrite_table: bool = True):
        """
        Create a data table in the database from a CSV file.
        Args:
            csv_dir (str): Directory to the CSV file.
            table_name (str): Name of the dat table to create.
            column_formats (dict): Dictionary of column names and their SQL data types.
            overwrite_table (bool): Whether to overwrite the existing table if it exists. Default is to overwrite (True).
        """
        # Check if column_formats dictionary is not empty
        if not column_formats:
            raise ValueError("column_formats dictionary must not be empty.")
        # Standardize column names to lowercase and replace spaces with underscores
        column_formats = {k.lower().replace(' ', '_'): v for k, v in column_formats.items()}
        column_format_sql = ', '.join([f"{k} {v}" for k, v in column_formats.items()])
        # Drop the existing table if it exists
        if overwrite_table:
            self.cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        # Create a new table with specified columns and formats
        self.cursor.execute(f"CREATE TABLE {table_name}({column_format_sql})")
        # Open the CSV file and read its contents
        with open(csv_dir, 'r') as file:
            contents = csv.reader(file)
            next(contents) # skip the header, the header will be determined based on the column_formats keys
            insert_records = f"INSERT INTO {table_name} ({', '.join(column_formats.keys())}) VALUES ({', '.join(['?'] * len(column_formats))})"
            # Insert data into the table
            self.cursor.executemany(insert_records, contents)
            # Commit the changes to the database
            self.db_connection.commit()
        print(f"CSV file {table_name} successfully written into the database. Overwrite table: {overwrite_table}")

    def get_data(self, query: str) -> pd.DataFrame:
        """
        Query data from the SQLite database and return it as a pandas DataFrame. We must connect to the database before calling this function.
        Args:
            query (str): SQL query.
        Returns:
            pd.DataFrame: Pandas DataFrame containing the queried data.
        """
        return pd.read_sql_query(query, self.db_connection)

    def clean_energy_price_data(self, energy_price_df: pd.DataFrame, operating_day_name: str, operating_hour_name: str, price_name: str) -> dict:
        """
        Clean the energy price data for the optimization model.
        Args:
            energy_price_df (pd.DataFrame): DataFrame containing energy price data.
            operating_day_name (str): Column name for the operating day.
            operating_hour_name (str): Column name for the operating hour.
            price_name (str): Column name for the price.
        Returns:
            dict: Dictionary with '(day, hour)' as keys and 'price' as values.
        """
        # Convert 'operating_day_name' to datetime format
        energy_price_df[operating_day_name] = pd.to_datetime(energy_price_df[operating_day_name], format="%m/%d/%y")
        # Return a dictionary with '(day, hour)' as keys and 'price' as values
        return {(row[operating_day_name].day, row[operating_hour_name]): row[price_name] for _, row in energy_price_df.iterrows()}


if __name__ == "__main__":
    # Create an instance of the DataProcess class
    data = DataProcess()
    data.connect_db(db_dir='data/database.db')

    # Example 1: Write the input data tables to the database
    # Energy prices data
    data.create_db_table_from_csv(
        csv_dir='data/input/energy_prices.csv',
        table_name='energy_prices',
        column_formats={'Operating Day': 'DATE', 'Operating Hour': 'INTEGER', 'Price': 'REAL'},
        overwrite_table=True
    )
    # Regulation prices data
    data.create_db_table_from_csv(
        csv_dir="data/input/regulation_prices.csv",
        table_name="regulation_prices",
        column_formats={"Operating Day": "DATE", "Operating Hour": "INTEGER", "Regulation Up": "REAL", "Regulation Down": "REAL"},
        overwrite_table=True,
    )

    # Example 2: Write the output data tables to the database
    # Optimal schedule data
    data.create_db_table_from_csv(
        csv_dir='data/output/schedule.csv',
        table_name='schedule',
        column_formats={'Hour': 'INTEGER', 'Day': 'INTEGER', 'Month': 'INTEGER', 'Energy_Charged': 'REAL', 'Energy_Discharged': 'REAL', 'Regulation_UP': 'REAL', 'Regulation_Down': 'REAL','Regulation_UP_Capacity': 'REAL', 'Regulation_Down_Capacity': 'REAL'},
        overwrite_table=True
    )
    # State of charge data
    data.create_db_table_from_csv(
        csv_dir='data/output/state_of_charge.csv',
        table_name='state_of_charge',
        column_formats={'Hour': 'INTEGER', 'Day': 'INTEGER', 'Month': 'INTEGER', 'State_of_Charge': 'REAL'},
        overwrite_table=True
    )
    # Daily schedule data
    data.create_db_table_from_csv(
        csv_dir='data/output/daily_schedule.csv',
        table_name='daily_schedule',
        column_formats={'Day': 'INTEGER', 'Month': 'INTEGER', 'Daily_Cost': 'REAL'},
        overwrite_table=True
    )

    # Example 3: Query and clean the data for the optimization model
    # Query energy price data
    energy_price_df = data.get_data(query="SELECT * FROM energy_prices WHERE price IS NOT NULL AND operating_day BETWEEN '11/1/23' AND '11/30/23'")
    # Clean the energy price data for the optimization model
    energy_prices = data.clean_energy_price_data(
        energy_price_df=energy_price_df,
        operating_day_name='operating_day',
        operating_hour_name='operating_hour',
        price_name='price'
    )

    # Query regulation price data
    regulation_price_df = data.get_data(query="SELECT * FROM regulation_prices WHERE regulation_up IS NOT NULL AND regulation_down IS NOT NULL AND operating_day BETWEEN '11/1/23' AND '11/30/23'")
    # Clean the regulation up price data for the optimization model
    regulation_up_prices = data.clean_energy_price_data(
        energy_price_df=regulation_price_df,
        operating_day_name='operating_day',
        operating_hour_name='operating_hour',
        price_name='regulation_up'
    )
    # Clean the regulation down price data for the optimization model
    regulation_down_prices = data.clean_energy_price_data(
        energy_price_df=regulation_price_df,
        operating_day_name='operating_day',
        operating_hour_name='operating_hour',
        price_name='regulation_down'
    )

    # Disconnect from the database when done
    data.disconnect_db()
