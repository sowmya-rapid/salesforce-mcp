from app.config import SF_CLIENT_ID

SALESFORCE_AUTH_BASE = "https://login.salesforce.com/services/oauth2/authorize"


def get_authorization_url(redirect_uri: str) -> str:
    return (
        f"{SALESFORCE_AUTH_BASE}"
        f"?response_type=code"
        f"&client_id={SF_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&scope=refresh_token"
    )
