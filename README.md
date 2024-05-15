# Tabby

Tabby is a Python application that integrates Rally and Tableau, enabling real-time data synchronization for enhanced project management and data visualization.

## Features

- **Real-time Data Synchronization:** Tabby leverages Rally webhooks to capture data changes in real-time and update corresponding Tableau data sources.
- **Automated Data Publishing:** Tabby automatically publishes updated data sources to Tableau Server or Tableau Cloud at a configurable frequency.
- **Customizable Data Selection:** Users can specify the Rally entities (e.g., Defects, User Stories) to be synchronized with Tableau.
- **Secure Authentication:** Tabby utilizes personal access tokens for secure authentication with both Rally and Tableau.
- **Ngrok Integration:** Tabby integrates with Ngrok to expose the local development server to the internet, enabling webhook reception from Rally.

## Requirements

- Tableau Server or Tableau Cloud account
- Rally API key
- Ngrok account and authentication token

## Installation

1. Clone the repository:

```
git clone https://github.com/alagonterie/tabby.git
```

2. Install the required Python packages:

```
pip install -r requirements.txt
```

## Usage

1. Start the Tabby application:

```
python tabby.py
```

2. Optionally configure a Rally webhook to send data change notifications to the Ngrok URL provided by Tabby. If using `--run_as_script` below, this is not necessary.

## Command-Line Arguments

Tabby supports the following command-line arguments:

- `--run_as_script`: Run Tabby as a one-time script, retrieving and updating Rally data once without a persistent service.
- `--port`: Specify the port for the local development server (default: 5000).
- `--ngrok_domain`: Set the URL for the static domain provided by Ngrok.
- `--tableau_datasource_dir`: Specify the directory for storing hyper database files (default: `data_sources`).
- `--tableau_publish_frequency`: Set the time interval (in seconds) between data source refreshes (default: 300).
- `--tableau_publish`: Enable publishing to Tableau Server/Cloud.
- `--rally_entities`: Specify a comma-separated list of Rally entities to synchronize (default: `Defect,DefectSuite,HierarchicalRequirement`).
- `--rally_get_limit`: Set the maximum number of records to retrieve from Rally in a single request. Increase from default if not testing. (default: 75).
- `--rally_get_pagesize`: Specify the page size for Rally get requests. Affects stability and performance. (default: 150).
- `--rally_webhook_buffer`: Set the buffer time (in seconds) to account for Rally webhook latency (default: 2).
- `--rally_refresh_on_start`: Enable refreshing local Rally data on application start.