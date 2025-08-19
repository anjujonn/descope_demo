import os
from dotenv import load_dotenv


load_dotenv()
DB_PATH = os.path.join(os.path.dirname(__file__), "gtm.db")
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK", "")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
D_ID_KEY = os.getenv("D_ID_KEY")
PATH_TO_SERVICEACC = os.getenv("PATH_TO_SERVICEACC")
STORAGEBUCKET = os.getenv("STORAGEBUCKET")


SAFE_MODE = True

AUTH_KEYWORDS = [
    "sso", "single sign-on", "oauth", "oidc", "saml", "mfa", "2fa",
    "authentication", "authorization", "passwordless", "magic link",
    "passkey", "auth0", "okta", "firebase auth", "descope"
]
TECH_HINTS = {
    "Auth0": r"auth0|auth0\.com",
    "Okta": r"okta|okta\.com",
    "FirebaseAuth": r"firebase\s*auth|firebase\.google|identitytoolkit",
    "Descope": r"descope|descope\.com",
    "SAML": r"saml",
    "OIDC": r"oidc|open id connect|openid connect",
}