from typing import TYPE_CHECKING
from uuid import UUID

from models.dataclass.bank import Bank

if TYPE_CHECKING:
    from models.character import Character


def need_deposit(character: Character, token: UUID) -> bool:
    """
    Check if the character needs to deposit items in the bank before withdrawing reserved items.
    Returns True if the character needs to deposit items, False otherwise.
    """
    nb_items_to_withdraw = sum(Bank.get_token_info(token).values())
    nb_slots_to_withdraw = len(Bank.get_token_info(token))

    if (
        character.inventory_free_space < nb_items_to_withdraw
        or character.inventory_free_slots < nb_slots_to_withdraw
    ):
        return True

    return False
