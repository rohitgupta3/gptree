import firebase_admin
from firebase_admin import credentials, auth

# cred = credentials.Certificate("path/to/serviceAccountKey.json")

# Instead, base64 encoded the 'private_key' key in the JSON file, then following this logic:
# const firebase_private_key_b64 = process.env.FIREBASE_PRIVATE_KEY_BASE64;
# const firebase_private_key = Buffer.from(firebase_private_key_b64, 'base64').toString('utf8');

# admin.initializeApp({
#     credential: admin.credential.cert({
#     "project_id": process.env.FIREBASE_PROJECT_ID,
#     "private_key": firebase_private_key,
#     "client_email": process.env.FIREBASE_CLIENT_EMAIL,
#     }),
#     databaseURL: process.env.FIREBASE_DATABASE_URL
# });

# Python version:
import os
import base64

# Decode the base64 private key
firebase_private_key_b64 = os.environ["FIREBASE_PRIVATE_KEY_BASE64"]
firebase_private_key = base64.b64decode(firebase_private_key_b64).decode("utf-8")

# # Create credentials object
# cred = credentials.Certificate({
#     "project_id": os.environ['FIREBASE_PROJECT_ID'],
#     "private_key": firebase_private_key,
#     "client_email": os.environ['FIREBASE_CLIENT_EMAIL']
# })

# # Initialize the app
# firebase_admin.initialize_app(cred, {
#     'databaseURL': os.environ['FIREBASE_DATABASE_URL']
# })


firebase_admin.initialize_app(cred)


def verify_token(id_token: str):
    return auth.verify_id_token(id_token)
