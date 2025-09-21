import os
import base64

import firebase_admin
from firebase_admin import credentials, auth

# Normally would generate creds via the JSON file provided. Instead we base64-encoded
# the "private_key" value and put it into the environment, and put the other values
# into the environment as well
firebase_private_key_b64 = os.environ["FIREBASE_PRIVATE_KEY_BASE64"]
firebase_private_key = base64.b64decode(firebase_private_key_b64).decode("utf-8")


def initialize_firebase_admin():
    if not firebase_admin._apps:
        private_key_b64 = os.environ["FIREBASE_PRIVATE_KEY_B64"]
        private_key = base64.b64decode(private_key_b64).decode("utf-8")

        cred_dict = {
            "type": "service_account",
            "project_id": os.environ["FIREBASE_PROJECT_ID"],
            "private_key_id": os.environ.get("FIREBASE_PRIVATE_KEY_ID", "placeholder"),
            "private_key": private_key,
            "client_email": os.environ["FIREBASE_CLIENT_EMAIL"],
            "client_id": os.environ.get("FIREBASE_CLIENT_ID", "placeholder"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{os.environ['FIREBASE_CLIENT_EMAIL']}",
        }

        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)


# TODO: don't like how importing this module will run this side effect
initialize_firebase_admin()


def verify_token(id_token: str) -> dict:
    return auth.verify_id_token(id_token)
