import importlib
import json
from typing import TYPE_CHECKING

from models.character.mixin.workMixin import WorkRoutine

if TYPE_CHECKING:
    from models.character import Character


class SaveMixin:
    _save_folder = "saves"

    def save(self: "Character"):
        with open(f"{self._save_folder}/{self.name}.json", "w") as f:
            json.dump(self.get_routine_data, f, ensure_ascii=False, indent=4)

    def load_routine(self: "Character") -> WorkRoutine:
        with open(f"{self._save_folder}/{self.name}.json", "r") as f:
            save_data = json.load(f)
            routine_name = save_data.get("routine_name")
            routine_module = save_data.get("routine_module")
            routine_args = save_data.get("routine_args")
            routine_kwargs = save_data.get("routine_kwargs")
            if routine_name and routine_module:
                module = importlib.import_module(routine_module)
                func = getattr(module, routine_name)

                return WorkRoutine(
                    func, *routine_args, is_routine=True, **routine_kwargs
                )
            else:
                raise Exception("No routine found in save file")
