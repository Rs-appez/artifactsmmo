from typing import TYPE_CHECKING

import httpx

from config import ARTIFACTSMMO_URL, HEADERS

if TYPE_CHECKING:
    from models import Character


async def reset_cooldown(character: "Character") -> None:
    """
    Reset the cooldown of the character's actions.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{ARTIFACTSMMO_URL}/sandbox/clear_cooldown",
            headers=HEADERS,
            json={"character": character.name},
        )
        if response.status_code != 200:
            raise Exception(
                f"Failed to reset cooldown: {response.status_code} - {response.text}"
            )

    await character.update_from_dict(response.json()["data"]["character"])
