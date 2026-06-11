from decouple import config
from zoneinfo import ZoneInfo

LOCAL = config("LOCAL", default=False, cast=bool)
SANDBOX = config("SANDBOX", default=False, cast=bool)

ARTIFACTSMMO_URL = (
    "https://api.artifactsmmo.com"
    if not SANDBOX
    else "https://api.sandbox.artifactsmmo.com"
)
HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": f"Bearer {config('ARTIFACTSMMO_API_KEY')}",
}
TIMEZONE = ZoneInfo("Europe/Brussels")
