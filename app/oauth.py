from app.config import SF_CLIENT_ID, SF_INSTANCE_URL

def get_authorization_url(redirect_uri: str):
    return (
        "https://login.salesforce.com/services/oauth2/authorize"
        f"?response_type=code"
        f"&client_id={SF_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&scope=refresh_token"
    )
