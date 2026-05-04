from models import Character


async def empty_farm(character: Character):
    _ = await character.deposit_all_in_bank()
