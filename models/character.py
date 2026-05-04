import asyncio
from collections import defaultdict
from datetime import datetime, timezone
from typing import Callable
from .enums import Layer
from .bank import nearest_bank

import requests

from config import ARTIFACTSMMO_URL, HEADERS, TIMEZONE


def request_action(func):
    async def wrapper(self, *args, **kwargs):
        await self.available
        return await func(self, *args, **kwargs)

    return wrapper


def need_bank(func):
    async def wrapper(self, *args, **kwargs):
        bank_location = nearest_bank(self.layer, self.location)
        current_location = self.location
        if current_location != bank_location and not await self.move(bank_location):
            print("❌ Failed to move to bank")
            return
        result = await func(self, *args, **kwargs)
        if (
            "comeback" in kwargs
            and kwargs["comeback"]
            and current_location != bank_location
        ):
            if not await self.move(current_location):
                print("❌ Failed to move back to original location")

        return result

    return wrapper


class Character:
    def __init__(self, name: str):
        self.__name = name
        self.__url = f"{ARTIFACTSMMO_URL}/my/{self.name}"

        self.__task: Callable | None = None
        self.__working = False

        self.__current_location: tuple[int, int] = (0, 0)
        self.__current_layer: Layer = Layer.INTERIOR
        self.__current_map_id: int = 0

        self.__cooldown: datetime | None = None

        self.__hp: int = 0
        self.__max_hp: int = 0
        self.__level: int = 0
        self.__xp: int = 0
        self.__max_xp: int = 0
        self.__gold: int = 0
        self.__inventory: defaultdict[str, int] = defaultdict(int)
        self.__inventory_max_items: int = 0

        self.refresh()

    def refresh(self):
        try:
            response = requests.get(
                f"{ARTIFACTSMMO_URL}/characters/{self.name}", headers=HEADERS
            )
            data = response.json()
            if "error" in data:
                print("data : ", data)
                raise Exception(data["error"]["message"])
            character_data = data["data"]
            self.__refresh(character_data)

        except Exception as e:
            print(f"❌ {e}")
            return

    @property
    def name(self):
        return self.__name

    @property
    def is_working(self) -> bool:
        return self.__working

    @property
    def location(self) -> tuple[int, int]:
        return self.__current_location

    @property
    def layer(self) -> Layer:
        return self.__current_layer

    @property
    def map(self) -> int:
        return self.__current_map_id

    @property
    def cooldown(self) -> float:
        cooldown = self.__cooldown
        if cooldown is None:
            return 0.0
        return (cooldown - datetime.now(TIMEZONE)).total_seconds()

    @property
    def hp(self) -> int:
        return self.__hp

    @property
    def max_hp(self) -> int:
        return self.__max_hp

    @property
    def xp(self) -> int:
        return self.__xp

    @property
    def max_xp(self) -> int:
        return self.__max_xp

    @property
    def level(self) -> int:
        return self.__level

    @property
    def gold(self) -> int:
        return self.__gold

    @property
    def inventory(self) -> dict[str, int]:
        return self.__inventory.copy()

    @property
    def is_inventory_full(self) -> bool:
        return sum(self.__inventory.values()) >= self.__inventory_max_items - 5

    @property
    async def available(self):
        while True:
            remaining = self.cooldown
            if remaining <= 0:
                break
            await asyncio.sleep(min(1.0, remaining))

    def assign_routine(self, task: Callable):
        self.__task = task

    async def work(self):
        if self.__task is None:
            print("❌ No task assigned to character")
            return
        self.__working = True
        while self.__working:
            if self.__task is None:
                print("❌ No task assigned to character")
                self.__working = False
                return
            await self.__task(self)

    @request_action
    async def move(self, position: tuple[int, int]) -> bool:
        if position == self.location:
            return True
        try:
            response = requests.post(
                f"{self.__url}/action/move",
                json={"x": position[0], "y": position[1]},
                headers=HEADERS,
            )
            data = response.json()

            if "error" in data:
                print("data : ", data)
                if data["error"]["code"] == 490:
                    return True
                raise Exception(data["error"]["message"])

            destination = data["data"]["destination"]
            character_data = data["data"]["character"]
            self.__refresh(character_data)

            print(
                f"✅ Moved to ({destination['x']}, {destination['y']}) on {destination['name']}"
            )
            return True
        except Exception as e:
            print(f"❌ {e}")
            return False

    @request_action
    async def gather(self) -> bool:
        try:
            response = requests.post(
                f"{self.__url}/action/gathering",
                headers=HEADERS,
            )
            data = response.json()

            if "error" in data:
                print("data : ", data)
                raise Exception(data["error"]["message"])

            character_data = data["data"]["character"]
            self.__refresh(character_data)

            return True
        except Exception as e:
            print(f"❌ {e}")
            return False

    @request_action
    async def fight(self) -> bool:
        try:
            response = requests.post(
                f"{self.__url}/action/fight",
                headers=HEADERS,
            )
            data = response.json()["data"]

            fight = data["fight"]
            characters = data["characters"]
            for character in characters:
                if character["name"] == self.name:
                    self.__refresh(character)
                    break
            result = True if fight["result"] == "win" else False
            print(
                f"✅ Fought and {'won' if result else 'lost'} against {fight['opponent']}"
            )

            return result
        except Exception as e:
            print(f"❌ {e}")
            return False

    @request_action
    async def rest(self) -> bool:
        try:
            response = requests.post(
                f"{self.__url}/action/rest",
                headers=HEADERS,
            )
            data = response.json()

            if "error" in data:
                print("data : ", data)
                raise Exception(data["error"]["message"])

            character_data = data["data"]["character"]
            self.__refresh(character_data)

            print(f"✅ Rested and recovered HP to {self.hp}/{self.max_hp}")
            return True
        except Exception as e:
            print(f"❌ {e}")
            return False

    async def deposit_all_in_bank(self, comeback: bool = True):
        if self.gold > 0:
            if not await self.deposit_gold_in_bank(self.gold, comeback=comeback):
                print("❌ Failed to deposit gold in bank")
                return
        if not await self.deposit_item_in_bank(
            [
                {"code": code, "quantity": quantity}
                for code, quantity in self.inventory.items()
                if code
            ],
            comeback=comeback,
        ):
            print("❌ Failed to deposit items in bank")
            return

    @request_action
    @need_bank
    async def deposit_gold_in_bank(self, quantity: int, comeback: bool = True) -> bool:
        if quantity > self.gold:
            print(f"❌ Cannot deposit {quantity} gold, only {self.gold} available")
            return False
        if quantity <= 0:
            print(f"❌ Cannot deposit non-positive quantity of gold: {quantity}")
            return False
        try:
            response = requests.post(
                f"{self.__url}/action/bank/deposit/gold",
                headers=HEADERS,
                json={"quantity": quantity},
            )
            data = response.json()

            if "error" in data:
                print("data : ", data)
                raise Exception(data["error"]["message"])

            character_data = data["data"]["character"]
            self.__refresh(character_data)

            print(f"✅ Deposited {quantity} gold in bank")
            return True
        except Exception as e:
            print(f"❌ {e}")
            return False

    @request_action
    @need_bank
    async def deposit_item_in_bank(
        self, items: list[dict[str, int]], comeback: bool = True
    ) -> bool:
        print("items : ", items)
        try:
            response = requests.post(
                f"{self.__url}/action/bank/deposit/item",
                headers=HEADERS,
                json=items,
            )
            data = response.json()

            if "error" in data:
                print("data : ", data)
                raise Exception(data["error"]["message"])

            character_data = data["data"]["character"]
            self.__refresh(character_data)

            print(
                f"✅ Deposited {', '.join([f'{item["quantity"]}x {item["code"]}' for item in items])} in bank"
            )
            return True
        except Exception as e:
            print(f"❌ {e}")
            return False

    def __setup_cooldown(self, cooldown: str):
        self.__cooldown = datetime.strptime(cooldown, "%Y-%m-%dT%H:%M:%S.%fZ").replace(
            tzinfo=timezone.utc
        )

    def __refresh(self, data: dict):
        self.__current_location = (data["x"], data["y"])
        self.__current_layer = Layer(data["layer"])
        self.__current_map_id = data["map_id"]
        self.__level = data["level"]
        self.__hp = data["hp"]
        self.__max_hp = data["max_hp"]
        self.__xp = data["xp"]
        self.__max_xp = data["max_xp"]
        self.__gold = data["gold"]
        self.__inventory = defaultdict(
            int,
            {item["code"]: item["quantity"] for item in data["inventory"]},
        )
        self.__inventory_max_items = data["inventory_max_items"]
        self.__setup_cooldown(data["cooldown_expiration"])
