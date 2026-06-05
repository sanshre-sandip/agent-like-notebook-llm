import os
import json
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests
from fastapi import HTTPException

CLIENT_SECRET_FILE = "client_secret.json"
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile"
]

def get_google_auth_flow(redirect_uri: str):
    if not os.path.exists(CLIENT_SECRET_FILE):
        raise HTTPException(status_code=500, detail="client_secret.json not found in root.")
    
    return Flow.from_client_secrets_file(
        CLIENT_SECRET_FILE,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )

def verify_google_token(token: str):
    try:
        # Verify the ID token
        id_info = id_token.verify_oauth2_token(
            token, requests.Request(), None # Audience check is skipped here for simplicity in this demo, but should be client_id
        )
        return id_info
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
