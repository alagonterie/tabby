class Args:
    def __init__(self):
        from argparse import ArgumentParser

        arg_parser = ArgumentParser(description='Start Tabby - Tableau/Rally Integration.')

        arg_parser.add_argument(
            '--run_as_script', action='store_true',
            help='Option to run Tabby as a one-time script with no persistent service and live updates. If enabled, all Rally data will be retrieved/updated once and the script will finish.'
        )
        arg_parser.add_argument(
            '--port', type=int, default=5000,
            help='The port of the local development server. Default: 5000.'
        )

        # ngrok
        arg_parser.add_argument(
            '--ngrok_auth_token', type=str, required=True,
            help='The ngrok authentication token.'
        )
        arg_parser.add_argument(
            '--ngrok_domain', type=str, default='',
            help='The url for the static domain provided by ngrok.'
        )

        # Tableau
        arg_parser.add_argument(
            '--tableau_token_name', type=str, required=True,
            help='The name of your authentication token for Tableau Server/Cloud. See this url for more details: https://help.tableau.com/current/server/en-us/security_personal_access_tokens.htm'
        )
        arg_parser.add_argument(
            '--tableau_token_value', type=str, required=True,
            help='The value of your authentication token for Tableau Server/Cloud. See this url for more details: https://help.tableau.com/current/server/en-us/security_personal_access_tokens.htm'
        )
        arg_parser.add_argument(
            '--tableau_server_url', type=str, default='https://us-west-2b.online.tableau.com',
            help='The url of Tableau Server / Cloud, e.g. https://us-west-2b.online.tableau.com'
        )
        arg_parser.add_argument(
            '--tableau_site_name', type=str, default='vertaforehackathon',
            help='The name of your site, e.g., use "default" for your default site. Note that you cannot use "default" in Tableau Cloud but must use the site name.'
        )
        arg_parser.add_argument(
            '--tableau_project_name', type=str, default='Rally',
            help='The name of your project, e.g., use an empty string ('') for your default project.'
        )
        arg_parser.add_argument(
            '--tableau_datasource_dir', type=str, default='data_sources',
            help='The relative path to the directory that will contain hyper database files.'
        )
        arg_parser.add_argument(
            '--tableau_publish_frequency', type=int, default=300,
            help='The time in seconds between each refresh of the Tableau Cloud/Server datasource.'
        )
        arg_parser.add_argument(
            '--tableau_publish', action='store_true',
            help='Enables publishing to Tableau Cloud/Server.'
        )

        # Rally
        arg_parser.add_argument(
            '--rally_apikey', type=str, required=True,
            help='Valid Rally API Key value.'
        )
        arg_parser.add_argument(
            '--rally_entities',
            type=str,
            default='Defect,DefectSuite,HierarchicalRequirement',
            help='A comma separated list of Rally entity names that will be converted to Tableau data sources, e.g., Defect,DefectSuite,HierarchicalRequirement.'
        )
        arg_parser.add_argument(
            '--rally_get_limit', type=int, default=75,
            help='The limit of total records that can be retrieved from Rally in a single get request.'
        )
        arg_parser.add_argument(
            '--rally_get_pagesize', type=int, default=150,
            help='The page size for every Rally get request. Determines performance and stability while retrieving large datasets.'
        )
        arg_parser.add_argument(
            '--rally_webhook_buffer', type=int, default=2,
            help='The seconds to account for random latency from Rally when receiving webhooks. Helps to ensure that webhooks are processed in chronological order. Adds delay.'
        )
        arg_parser.add_argument(
            '--rally_refresh_on_start', action='store_true',
            help='Enables refreshing the local Rally data on start. This can be time consuming.'
        )

        parsed_args = arg_parser.parse_args()

        self.run_as_script = bool(parsed_args.run_as_script)
        self.port = int(parsed_args.port)

        self.ngrok_auth_token = str(parsed_args.ngrok_auth_token)
        self.ngrok_domain = str(parsed_args.ngrok_domain)

        self.tableau_token_name = str(parsed_args.tableau_token_name)
        self.tableau_token_value = str(parsed_args.tableau_token_value)
        self.tableau_server_url = str(parsed_args.tableau_server_url)
        self.tableau_site_name = str(parsed_args.tableau_site_name)
        self.tableau_project_name = str(parsed_args.tableau_project_name)
        self.tableau_datasource_dir = str(parsed_args.tableau_datasource_dir)
        self.tableau_publish_frequency = int(parsed_args.tableau_publish_frequency)
        self.tableau_publish = bool(parsed_args.tableau_publish)

        self.rally_apikey = str(parsed_args.rally_apikey)
        self.rally_entities = str(parsed_args.rally_entities).split(',')
        self.rally_get_limit = int(parsed_args.rally_get_limit)
        self.rally_get_pagesize = int(parsed_args.rally_get_pagesize)
        self.rally_webhook_buffer = int(parsed_args.rally_webhook_buffer)
        self.rally_refresh_on_start = bool(parsed_args.rally_refresh_on_start)


args = Args()
