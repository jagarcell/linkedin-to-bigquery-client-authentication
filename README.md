# Linkedin Metrics Client Authentication
This project is meant to  be used to create a callback function service for the Linkedin OAUTH authentication process to grant access toe Linkedin's API.

# Prepare you local development environment
You will need to install Python in your environment and make sure that is added to your PATH.

Install Google Cloud SDK in your local

# Run this commands in your local
gcloud auth login  (authenticate your local with Google Cloud)

gcloud config set project <google_cloud_projec_id>  (Select your project, can be other than this one)

# Instructions
The steps to use it are as follows:

1 - Make sure that you have a project in Google Cloud or create it https://console.cloud.google.com/

2-  Within the peoject you will find the project_id and project_number, you will nedd them in the environment variables.

3 - Set the build_env.py and .env.yaml variables. Follow the comments for each env variable.

4 - Run build_and_deploy_callback.py

5 - Create the OAUTH URL by running create_callback_url.bat, copy it and paste to share with the client that has to authorize access to their Linkedin API.
    
    Note: This script could be written in Python to make it independent of the development environment OS

6 - After the client grants authorization by following the previous URL an email should comes into the RECEPIENT_EMAIL set in .env.yaml containig the ACCESS and REFRESH tokens,
    it will also containg the name of the user that is authorizing and a new STATE, the new STATE may be used in case that you need the user to authorize
    the API access againg in case that something went wrong. If that is the case you will need to set the environment variables again using the new STATE
    value by runnig set_env.py.

7 - Create a collection at https://console.cloud.google.com/firestore/databases/ to be used as the STATES_COLLECTION variable in .env.yaml

8 - Enable API and services at https://console.cloud.google.com/apis/dashboard

Once the service is created you don't need to use build_and_deploy_callback.py when you make changes in the code, to deploy your changes you can use
deploy.py

Linkedin API documentation:

https://learn.microsoft.com/en-us/linkedin/
