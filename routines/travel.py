from models import Character, Encyclopedia, LocationRegistry
from models.dataclass import Map
from models.dataclass.bank import Bank


async def __get_pre_travel_items(character: Character) -> None:

    tp_potion = await Encyclopedia.get_item_by_code("forest_bank_potion")
    if not character.has_in_inventory({tp_potion: 1}):
        async with Bank.reserve_items({tp_potion: 1}) as bank_token:
            if not await character.withdraw_item_from_bank(bank_token):
                raise Exception(f"Failed to withdraw {tp_potion.name} from bank")

    if character.gold < 1000:
        if not await character.withdraw_gold_from_bank(1000):
            raise Exception("Failed to withdraw 1000 gold from bank")


async def __handle_sandwhisper_travel(character: Character) -> None:

    await __get_pre_travel_items(character)
    boat = await LocationRegistry.get_map_by_id(1093)
    if not await character.move(boat):
        raise Exception(
            f"Failed to travel to {boat.name} from {character.location.name}"
        )

    if not await character.transition():
        raise Exception(f"Failed to transition from {boat.name} to Sandwhisper")


async def handle_travel(character: Character, resource_map: Map) -> None:
    if (
        "Sandwhisper" in resource_map.name
        and "Sandwhisper" not in character.location.name
    ):
        await __handle_sandwhisper_travel(character)


async def handle_return_travel(character: Character) -> None:
    tp_potion = await Encyclopedia.get_item_by_code("forest_bank_potion")
    if not tp_potion:
        raise Exception("Failed to find forest_bank_potion in encyclopedia")

    if "Sandwhisper" in character.location.name:
        if not await character.use_item(tp_potion):
            raise Exception(
                f"Failed to use {tp_potion.name} to return from Sandwhisper"
            )
