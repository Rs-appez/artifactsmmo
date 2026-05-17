from decouple import config
from zoneinfo import ZoneInfo

LOCAL = config("LOCAL", default=False, cast=bool)

ARTIFACTSMMO_URL = "https://api.artifactsmmo.com"
HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": f"Bearer {config('ARTIFACTSMMO_API_KEY')}",
}
TIMEZONE = ZoneInfo("Europe/Brussels")
