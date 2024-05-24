import yaml

# postgre credential setting
with open('credential/postgre_credentials.yaml', 'r') as file:
    cred_pg = yaml.safe_load(file)

POSTGRE_HOST = cred_pg['postgre']['host']
POSTGRE_PORT = cred_pg['postgre']['port']
POSTGRE_USERNAME = cred_pg['postgre']['username']
POSTGRE_PASSWORD = cred_pg['postgre']['password']
POSTGRE_DATABASE_1 = cred_pg['postgre']['database_1']
POSTGRE_DATABASE_2 = cred_pg['postgre']['database_2']

# gpt-4 api secret key
with open('credential/gptapi_credentials.yaml', 'r') as file:
    cred_gpt = yaml.safe_load(file)

GPT_SECRET = cred_gpt['gpt']['secret_key']
AZURE_OPENAI_API_KEY = cred_gpt['gpt']['azure_openai_api_key']
AZURE_OPENAI_ENDPOINT = cred_gpt['gpt']['azure_openai_endpoint']
AZURE_OPENAI_API_VERSION = cred_gpt['gpt']['azure_openai_api_version']