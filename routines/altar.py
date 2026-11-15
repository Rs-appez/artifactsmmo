from typing import TYPE_CHECKING

from models import Altar, Encyclopedia
from models.dataclass import Item, Monster, Offering, Resource
from models.dataclass.bank import Bank
from utils.find_nearest import find_nearest_altar

if TYPE_CHECKING:
    from models.character import Character

_LOOKUPS = (
    Encyclopedia.get_resource_by_code,
    Encyclopedia.get_monster_by_code,
    Encyclopedia.get_item_by_code,
)


async def make_offering(
    character: Character, offering: Offering | Resource | Monster | Item | str
) -> None:
    if isinstance(offering, str):
        offering_obj = await _resolve_offering(offering)
        if offering_obj is None:
            print(f"❌ Offering with code '{offering}' not found.")
            return
        else:
            offering = offering_obj

    if not isinstance(offering, Offering):
        offering_obj = await Altar.get_offering(offering)
        if offering_obj is None:
            print(f"❌ No offering found for target '{offering}'.")
            return
        else:
            offering = offering_obj

    item = offering.item
    if item.is_craftable:
        await _make_craft_offering(character, offering)
    else:
        await _make_item_offering(character, offering)


async def _make_craft_offering(character: Character, offering: Offering) -> None:
    raise NotImplementedError(
        "Making offering is not implemented yet. Please implement the logic to make the offering."
    )


async def _make_item_offering(character: Character, offering: Offering) -> None:
    if character.inventory.get(offering.item, 0) < offering.item_quantity:
        async with Bank.reserve_items(
            {offering.item: offering.item_quantity}, inventory=character.inventory
        ) as bank_token:
            if len(Bank.get_token_info(bank_token)) != 0:
                if character.need_deposit(bank_token):
                    await character.deposit_all_in_bank()
                if not await character.withdraw_item_from_bank(bank_token):
                    print(
                        f"❌ {character.surname} does not have enough {offering.item.name} to make the offering."
                    )
                    return

    altar_location = await find_nearest_altar(character)
    await character.move(altar_location)
    await character.accept_offering(offering)
    await character.complete_offering(offering)


async def _resolve_offering(code: str) -> Resource | Monster | Item | None:
    for lookup in _LOOKUPS:
        try:
            return await lookup(code)
        except ValueError:
            continue
    return None
