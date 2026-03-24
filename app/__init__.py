from flask import Flask
from flask_pymongo import PyMongo
import boto3
import json

print("STEP 1: starting app import")

app = Flask(__name__)

def get_secret():
    secret_name = "pharmaprofsbackend"
    region_name = "us-east-1"

    print("STEP 2: creating boto3 session")
    session = boto3.session.Session()

    print("STEP 3: creating secretsmanager client")
    client = session.client(
        service_name="secretsmanager",
        region_name=region_name
    )

    print("STEP 4: fetching secret")
    response = client.get_secret_value(SecretId=secret_name)

    print("STEP 5: parsing secret")
    secret_string = response["SecretString"]
    secret_data = json.loads(secret_string)

    print("STEP 6: returning connection string")
    return secret_data["CONNECTION_STRING"]

try:
    connection_string = get_secret()
    print("STEP 7: secret fetched successfully")

    app.config["MONGO_URI"] = connection_string
    mongo = PyMongo(app)
    print("STEP 8: mongo initialized")

    from app import routes
    print("STEP 9: routes imported successfully")

except Exception as e:
    print(f"STARTUP ERROR: {repr(e)}")
    raise
