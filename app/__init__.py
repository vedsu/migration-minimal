from flask import Flask
from flask_pymongo import PyMongo
import boto3
import json

app = Flask(__name__)


def get_secret():
    secret_name = "pharmaprofsbackend"
    region_name = "us-east-1"

    session = boto3.session.Session()
    client = session.client(
        service_name="secretsmanager",
        region_name=region_name
    )

    response = client.get_secret_value(SecretId=secret_name)
    secret_string = response["SecretString"]
    secret_data = json.loads(secret_string)

    return secret_data["CONNECTION_STRING"]


connection_string = get_secret()

app.config["MONGO_URI"] = connection_string
mongo = PyMongo(app)

from app import routes
