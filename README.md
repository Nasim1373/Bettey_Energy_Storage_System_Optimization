
# Battery Energy Storage Optimization Model

The **Battery Energy Storage Optimization** project maximizes profits through arbitrage, optimizing charging and discharging strategies based on fluctuating electricity prices, and calculates optimal bidding strategies, helping businesses enhance revenue and operational efficiency by capitalizing on market fluctuations.

For a more in-depth look at the developed mathematical optimization model, along with the detailed formulations, please visit [the mathematical optimizatino model](/documents/battery_energy_storage_optimization_model.pdf).

# Setup and Installation

Follow these steps to set up the project in a machine:


1. **Install Python**:
    Ensure that Python 3.8.2 is installed on your machine. To download it, visit ([Python 3.8.2 installation toturial](https://www.python.org/downloads/release/python-382/)). To check if Python is already installed, run "python --version" in your terminal and check if it displays the version.

2. **Clone the repository**:
    ```bash
    git clone https://github.com/Nasim1373/BatteryStorage.git
    ```

3. **Create and activate a virtual environment**:
    ```bash
    python3 -m venv <directory> # MacOS
    source venv/bin/activate
    ```

4. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

5. **Install CPLEX solver**:
    Visit https://www.ibm.com/docs/en/icos/22.1.2?topic=cplex-setting-up-python-api

---

## Usage

There are several different ways to run the optimization model on a machine as outlined below.

### 1. Running the python script locally

1. Open the terminal and navigate to the script location called "main.py" within the project.
2. Run the script with "python3 main.py" or "python main.py".
3. View the output csv files in "data/output" folder.


### 2. API (Application Programming Interfaces)

The Flask-based API provides endpoints for running/triggering optimization model, executing unit tests, and visualize the outputs either in Python or on a web browser. To use the API:

1. Open the terminal and navigate to the script location called "api.py" within the project.
2. Run the script with "python3 api.py" or "python api.py".
3. View the output csv files in "data/output" folder.

**Example request for unit test**

with parameters `months`, comma-separated list of months (e.g., `11,12`), and `initial_state_of_charge`, initial charge state (default is `100`), Request http://127.0.0.1:8080/run-optimization?months=11,12&initial_state_of_charge=100 (make sure "api.py" is still running).

The API returns a plot of the optimization model. To run unit tests, request http://127.0.0.1:8080/run-tests (make sure "api.py" is still running). The API responds with a json object indicating whether the unit tests passed successfully.

To make the requests through API, "requests" package is required. Example:

```bash
import requests
url = 'http://127.0.0.1:8080/run-optimization'
params = {
    'months': '11,12',
    'initial_state_of_charge': 100
}
response = requests.get(url, params=params)
with open('optimization_plot.png', 'wb') as f:
    f.write(response.content)

# Also, to run the unit tests
url = 'http://127.0.0.1:8080/run-tests'
response = requests.get(url)
print(response.json())
```

---

# Database
The API runs the model and stores necessary output files from the database. Then, it reads the outputs from the database and visualize it. The database is stored to the "data" folder, and there are functions in "data_preprocess/data_process.py" script to write input and output (any csv) files to the database and read them with an efficient query. The data tables replace spaces with underscore and with small letters (e.g., Energy Price -> energy_price). Usage example:

```bash
# Import the class and create an instance
from data_preprocess.data_process import DataProcess
dp = DataProcess()
# Connect to the database with specified directory where the database is stored
dp.connect_db(db_dir='data/database.db')
# Query with SQL language
energy_price_df = dp.get_data(query="SELECT * FROM energy_prices WHERE price IS NOT NULL AND operating_day BETWEEN '11/1/23' AND '11/30/23'")
# Disconnect from the database
dp.disconnect_db()
```

Also, to write the csv files into the database, the users can use the following exmample. This function takes the directory (path) of the csv file, the table name to store to the database, the name of columns and their SQL format. An existing data table can be overwritten by setting overwrite_table=True.

```bash
# Import the class and create an instance
from data_preprocess.data_process import DataProcess
dp = DataProcess()
# Connect to the database with specified directory where the database is stored
dp.connect_db(db_dir='data/database.db')
# Store csv to the database
dp.create_db_table_from_csv(
    csv_dir='data/input/energy_prices.csv',
    table_name='energy_prices',
    column_formats={'Operating Day': 'DATE', 'Operating Hour': 'INTEGER', 'Price': 'REAL'},
    overwrite_table=True
)
# Disconnect from the database
dp.disconnect_db()
```


---

# Contact

For questions, feel free to reach out to nasimmirzavand1373@gmail.com
