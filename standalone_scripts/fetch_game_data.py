import asyncio
import json
from pathlib import Path

import httpx

from config import ARTIFACTSMMO_URL, DATA_DIR, HEADERS

NEEDED_ENDPOINTS = [
    "items",
    "effects",
    "monsters",
    "resources",
    "events",
    "npcs/details",
    "raids",
]


async def fetch_game_data():
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    async with httpx.AsyncClient(
        base_url=ARTIFACTSMMO_URL, headers=HEADERS, timeout=30.0
    ) as client:
        await asyncio.gather(
            *[fetch(client, endpoint) for endpoint in NEEDED_ENDPOINTS]
        )


async def fetch(client: httpx.AsyncClient, endpoint: str):
    data = await _make_call(client, endpoint)
    filename = endpoint.split("/")[0]
    await _save_loaded(data, filename)


async def _make_call(
    client: httpx.AsyncClient, endpoint: str, params: dict | None = None
) -> list[dict]:
    if params is None:
        params = {}
    page = 1
    max_pages = 2
    data_list = []
    while page <= max_pages:
        response = await client.get(
            f"{ARTIFACTSMMO_URL}/{endpoint}",
            headers=HEADERS,
            params={**params, "page": page, "size": 600},
            timeout=30.0,
        )
        if response.status_code != 200:
            raise Exception(
                f"Failed to fetch {endpoint}: {response.status_code} - {response.text}"
            )

        data = response.json()
        data_list.extend(data.get("data", []))
        page += 1
        max_pages = data["pages"]

    print(f"Fetched {len(data_list)} {endpoint}")
    return data_list


async def _save_loaded(data: list[dict], filename: str):
    with open(DATA_DIR + f"{filename}_data.json", "w") as f:
        f.write(json.dumps(data))


if __name__ == "__main__":
    asyncio.run(fetch_game_data())
