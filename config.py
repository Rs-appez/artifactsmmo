from decouple import config
from zoneinfo import ZoneInfo

LOCAL = config("LOCAL", default=False, cast=bool)
SANDBOX = config("SANDBOX", default=False, cast=bool)

ARTIFACTSMMO_URL = (
    "https://api.artifactsmmo.com"
    if not SANDBOX
    else "https://api.sandbox.artifactsmmo.com"
)
ARTIFACTSMMO_WS_URL = (
    "wss://realtime.artifactsmmo.com"
    if not SANDBOX
    else "wss://realtime.sandbox.artifactsmmo.com"
)
ARTIFACTSMMO_API_KEY = config("ARTIFACTSMMO_API_KEY")
HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": f"Bearer {ARTIFACTSMMO_API_KEY}",
}
TIMEZONE = ZoneInfo("Europe/Brussels")
DATA_DIR = "game_datas/"


# Game constants
MAX_LEVEL_CHARACTER = 50
MAX_LEVEL_JOB = 50
CRITICAL_STRIKE_MULTIPLIER = 1.5
