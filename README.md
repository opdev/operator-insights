# Operator-Insights Report generation tool
This code provides a set of functions to compare cluster IDs from different datasets(superset, Telesense and Salesforce tickets), filter the data based on the comparison results, and generate a report based on the filtered data. The code is written in Python.

# How it works:
The code is divided into 3 main parts:

1. Get all the data from the different datasets and store them in the same directory.
2. Compare the cluster IDs from the different datasets and filter the Cluster IDs that are missing from Telesense and Superset but are present in Salesforce Cases based on the comparison results.
3. Use the filtered data and download the must-gather files for the filtered cluster IDs.
4. Once the must-gather are downloaded, we use the OMG tool to get the cluster insights and generate the report.
5. The report generated is in the form of a json file.

## Prerequisites
The code requires the following Python dependencies to be installed:

json: a built-in module for working with JSON data.
csv: a built-in module for reading and writing CSV files.
os: a built-in module for interacting with the operating system.
subprocess: a built-in module for running external commands.
Note: In this case, we are using python3

## Usage
1. Clone the repo
2. Download the datasets from Superset, Telesense and Salesforce and store them in the same directory as the code.
3. Change [this](https://github.com/yashoza19/operator-insights/blob/c34b12363a11ab101c59ebfe414fba06ff8f2dbc/generate_report.py#LL170C23-L170C46) to the path of the report generated by salesforce, Telesense and superset respectively.
4. Run the code using the following command:
```
python3 generate_report.py
```
5. The report will be generated in the same directory as the code.