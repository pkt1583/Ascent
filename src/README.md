# Introduction 
This repo hosts the API code and its testing artifacts for Multi-store deployment at scale platform.

# Setting up the dev environment

## Prerequisites
- Docker - To run the local mongodb docker container for local development, optionally you can run a Mongodb locally
- Python 3.10.9

## Running the local dev environment

### Prepare the environment variables
- Create a copy of .env.template file and rename it as .env
- A sample .env file at local enviroment may look like as shown below
```
AZURE_COSMOS_CONNECTION_STRING="mongodb://root:rootpassword@localhost:27017"
AZURE_COSMOS_DATABASE_NAME="contoso"
APPLICATIONINSIGHTS_CONNECTION_STRING=""
AZURE_DEVOPS_PAT=""
BYPASS_AUTH_FOR_BEHAVE_TESTING="true"
TENANT_ID=""
CLIENT_ID=""
BASE_URL_FOR_E2E="http://127.0.0.1:3100"
```
- The devops PAT token can be taken from admin, and must not be checked in. APIs should work without the PAT token.

### Start the local database
- Run the command from terminal - 
```
docker-compose up -d mongodb_container
```

### Run the code
- Install the python requirements, run the following command from terminal

    ```
    > pip install -r .\requirements.txt
    ```
- Option 1 - Run the local API using following command from terminal

    ```
    > python -m uvicorn app.app:app --port 3100 --reload
    ```
- Option 2 - If you are using VS code, the .vscode folder contains the launch.json and other settings to enable a fully functional debugging experience. Just run the debug from VS Code or use `ctrl + shift + D ` to start the debugging experience

### Running tests

If you want to run without authentication (preferred mode for tests on local dev) then please have 
'BYPASS_AUTH_FOR_BEHAVE_TESTING="true"' in your .env file
If you need to run with authentication then you would need to have CLIENT_ID and TENANT_ID set. The values can be 
obtained from appropriate App Registration of Azure active directory

Behave_main.py is the main file that sets up things and triggers BDD tests, but before that you must install the test requirements using following command

```
> pip install -r test-requirements.txt
```
After the required python modules are installed, you can run the tests using the following command.

```
> python behave_main.py
```

The output summary should look like below


`` 4 features passed, 0 failed, 0 skipped
5 scenarios passed, 0 failed, 0 skipped
36 steps passed, 0 failed, 0 skipped, 0 undefined
Took 0m3.517s ``

Numbers might change as more tests are added