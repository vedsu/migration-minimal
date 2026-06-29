# app/__init__.py

from flask import Flask
from flask_pymongo import PyMongo
from flask_cors import CORS
from flask_mail import Mail
import boto3
import json


app = Flask(__name__)

REGION_NAME = "us-east-1"


def get_secret(secret_name):
    session = boto3.session.Session()
    client = session.client(
        service_name="secretsmanager",
        region_name=REGION_NAME
    )

    response = client.get_secret_value(SecretId=secret_name)
    secret_string = response["SecretString"]

    return json.loads(secret_string)


# --------------------------------------------------
# Load all website secrets
# --------------------------------------------------

healthprofs_secret = get_secret("healthprofs")
pharmaprofs_secret = get_secret("pharmaprofs")
hrprofs_secret = get_secret("hrprofs")


# --------------------------------------------------
# Common configuration
# DB and S3 are same for all websites.
# Using PHARMAPROFS secret for common DB and S3 values.
# --------------------------------------------------

common_secret = pharmaprofs_secret
stripe_secret_key = common_secret["stripe_secret_key"]


# --------------------------------------------------
# MongoDB configuration
# Existing variable name kept same: mongo
# --------------------------------------------------

connection_string = common_secret["CONNECTION_STRING"]

app.config["MONGO_URI"] = connection_string

mongo = PyMongo(app)


# --------------------------------------------------
# CORS
# --------------------------------------------------

CORS(app)


# --------------------------------------------------
# Mail configuration
# Mail credentials are different for each website.
# Existing variable name kept same: mail
# --------------------------------------------------

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USE_SSL"] = True
app.config["MAIL_USERNAME"] = hrprofs_secret.get("MAIL_USERNAME", "cs@profstraining.com")
app.config["MAIL_PASSWORD"] = hrprofs_secret["MAIL_PASSWORD"]

mail = Mail(app)


WEBSITE_MAIL_CONFIGS = {
    "HEALTHPROFS": {
        "MAIL_USERNAME": healthprofs_secret.get(
            "MAIL_USERNAME",
            "registration@healthprofs.com"
        ),
        "MAIL_PASSWORD": healthprofs_secret["MAIL_PASSWORD"],
    },
    "PHARMAPROFS": {
        "MAIL_USERNAME": pharmaprofs_secret.get(
            "MAIL_USERNAME",
            "registration@pharmaprofs.com"
        ),
        "MAIL_PASSWORD": pharmaprofs_secret["MAIL_PASSWORD"],
    },
    "HRPROFS": {
        "MAIL_USERNAME": hrprofs_secret.get(
            "MAIL_USERNAME",
            "registration@hrprofs.com"
        ),
        "MAIL_PASSWORD": hrprofs_secret["MAIL_PASSWORD"],
    },
}


def normalize_website(website):
    if not website:
        return None

    return website.upper().strip()

VALID_WEBSITES = ["HEALTHPROFS", "PHARMAPROFS", "HRPROFS"]

WEBSITE_URLS = {
    "HEALTHPROFS": "https://healthprofs.com/",
    "PHARMAPROFS": "https://pharmaprofs.com/",
    "HRPROFS": "https://hrprofs.com/",
}

WEBSITE_NAMES = {
    "HEALTHPROFS": "HealthProfs",
    "PHARMAPROFS": "PharmaProfs",
    "HRPROFS": "HRProfs",
}

WEBSITE_SUPPORT_EMAILS = {
    "HEALTHPROFS": "support@healthprofs.com",
    "PHARMAPROFS": "support@pharmaprofs.com",
    "HRPROFS": "support@hrprofs.com",
}

WEBSITE_QUERY_EMAILS = {
    "HEALTHPROFS": "support@healthprofs.com",
    "PHARMAPROFS": "support@pharmaprofs.com",
    "HRPROFS": "support@hrprofs.com",
}


def validate_website(website):
    website = normalize_website(website)

    if not website:
        return None

    if website not in VALID_WEBSITES:
        return None

    return website


def get_website_url(website):
    website = normalize_website(website)
    return WEBSITE_URLS.get(website)


def get_website_name(website):
    website = normalize_website(website)
    return WEBSITE_NAMES.get(website, "PharmaProfs")


def get_support_email(website):
    website = normalize_website(website)
    return WEBSITE_SUPPORT_EMAILS.get(website)


def get_query_email(website):
    website = normalize_website(website)
    return WEBSITE_QUERY_EMAILS.get(website)

def get_mail_config_by_website(website):
    website = normalize_website(website)

    if not website:
        return None

    return WEBSITE_MAIL_CONFIGS.get(website)


def apply_mail_config_by_website(website):
    mail_config = get_mail_config_by_website(website)

    if not mail_config:
        return False

    app.config["MAIL_USERNAME"] = mail_config["MAIL_USERNAME"]
    app.config["MAIL_PASSWORD"] = mail_config["MAIL_PASSWORD"]

    return True


def get_mail_sender_by_website(website):
    mail_config = get_mail_config_by_website(website)

    if not mail_config:
        return None

    return mail_config["MAIL_USERNAME"]


# --------------------------------------------------
# S3 configuration
# S3 credentials/resources are same for all websites.
# Existing variable names kept same:
# s3_resource, s3_client
# --------------------------------------------------

access_id = common_secret["aws_access_key_id"]
access_key = common_secret["aws_secret_access_key"]

s3_resource = boto3.resource(
    service_name="s3",
    region_name=REGION_NAME,
    aws_access_key_id=access_id,
    aws_secret_access_key=access_key
)

s3_client = boto3.client(
    service_name="s3",
    region_name=REGION_NAME,
    aws_access_key_id=access_id,
    aws_secret_access_key=access_key
)


# --------------------------------------------------
# Routes import should remain at the end
# --------------------------------------------------

from app import routes
