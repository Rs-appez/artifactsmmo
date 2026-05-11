from collections.abc import Callable
from typing import TYPE_CHECKING, Protocol
import dill  # pyright: ignore[reportMissingTypeStubs]

if TYPE_CHECKING:
    from models.character import Character


class SaveMixin(Protocol):
    _save_folder = "saves"

    def save_routine(self: "Character"):
        with open(f"{self._save_folder}/{self.name}_routine.pkl", "wb") as f:
            dill.dump(self._routine, f)  # pyright: ignore[reportPrivateUsage]

    def load_routine(self: "Character") -> Callable:
        with open(f"{self._save_folder}/{self.name}_routine.pkl", "rb") as f:
            return dill.load(f)
