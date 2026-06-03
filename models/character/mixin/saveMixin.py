from collections.abc import Callable
import importlib
import json
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from models.character import Character


class SaveMixin(Protocol):
    _save_folder = "saves"

    def save(self: "Character"):
        save_data = {
            "routine_name": getattr(self._routine, "__name__", None),  # pyright: ignore[reportPrivateUsage]
            "routine_module": getattr(self._routine, "__module__", None),  # pyright: ignore[reportPrivateUsage]
            "routine_args": self._routine_info,  # pyright: ignore[reportPrivateUsage]
        }
        with open(f"{self._save_folder}/{self.name}.json", "w") as f:
            json.dump(save_data, f, ensure_ascii=False, indent=4)

    def load_routine(self: "Character") -> Callable:
        with open(f"{self._save_folder}/{self.name}.json", "r") as f:
            save_data = json.load(f)
            routine_name = save_data.get("routine_name")
            routine_module = save_data.get("routine_module")
            routine_args = save_data.get("routine_args", [])
            if routine_name and routine_module:
                module = importlib.import_module(routine_module)
                func = getattr(module, routine_name)
                if routine_args:
                    args, kwargs = routine_args

                    def routine(char):
                        return func(char, *args, **kwargs)

                    routine.__name__ = func.__name__
                    routine.__module__ = func.__module__
                    self._routine_info = routine_args  # pyright: ignore[reportPrivateUsage]

                    return routine
                return func
            else:
                raise Exception("No routine found in save file")
