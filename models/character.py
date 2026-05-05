import asyncio
from collections import deque
from datetime import datetime
from typing import Callable

import httpx
from config import ARTIFACTSMMO_URL, HEADERS, TIMEZONE
from models.items import Item

from .bank import nearest_bank
from .enums import Layer
from .character_data import CharacterData


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
    def __init__(self, data: CharacterData):
        self.__name = data.name
        self.__surname = data.surname
        self.__url = f"{ARTIFACTSMMO_URL}/my/{self.name}"
        self.__client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)

        self.__task: Callable | None = None
        self.__working = False
        self.__work_task: asyncio.Task | None = None
        self.__interrupted: bool = False
        self.__priority_task: deque[Callable] = deque()

        self.__current_location = data.location
        self.__current_layer = data.layer
        self.__current_map_id = data.map

        self.__cooldown = data.cooldown

        self.__hp = data.hp
        self.__max_hp = data.max_hp
        self.__level = data.level
        self.__xp = data.xp
        self.__max_xp = data.max_xp
        self.__gold = data.gold
        self.__inventory = data.inventory
        self.__inventory_max_items = data.inventory_max_items

        self.__jobs = data.jobs

    async def refresh(self):
        try:
            response = await self.__client.get(
                f"{ARTIFACTSMMO_URL}/characters/{self.name}", headers=HEADERS
            )
            data = response.json()
            if "error" in data:
                print("data : ", data)
                raise Exception(data["error"]["message"])
            character_data = data["data"]
            self.__refresh(CharacterData.from_dict(character_data))

        except Exception as e:
            print(f"❌ {e}")
            return

    @property
    def name(self):
        return self.__name

    @property
    def surname(self):
        return self.__surname

    @property
    def is_working(self) -> bool:
        return self.__working

    @property
    def work_on(self) -> str | None:
        if self.__task is None:
            return None
        return self.__task.__name__

    @property
    def is_interrupted(self) -> bool:
        return self.__interrupted

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
    async def available(self):
        while True:
            remaining = self.cooldown
            if remaining <= 0:
                break
            await asyncio.sleep(min(3.0, remaining))

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
    def inventory_max_items(self) -> int:
        return self.__inventory_max_items

    @property
    def is_inventory_full(self) -> bool:
        return sum(self.__inventory.values()) >= self.__inventory_max_items - 5

    def assign_routine(self, task: Callable):
        self.__task = task

    async def work(self):
        if self.__task is None:
            print("❌ No task assigned to character")
            return
        self.__working = True
        self.__work_task = asyncio.current_task()
        print(f"🚀 {self.name} started working on routine {self.__task.__name__}")
        try:
            while self.__working:
                if self.__task is None:
                    print("❌ No task assigned to character")
                    self.stop()
                    return
                try:
                    await self.__task(self)
                except asyncio.CancelledError:
                    if not self.__interrupted:
                        raise
                    self.__interrupted = False
                    while self.__priority_task:
                        priority = self.__priority_task.popleft()
                        await priority(self)
        except asyncio.CancelledError:
            pass
        finally:
            self.__working = False
            self.__work_task = None

    def do_one_time_task(self, task: Callable):
        self.__queue_priority_task(task)
        if not self.is_working:
            _ = asyncio.create_task(self.__do_priority_task())

    async def __do_priority_task(self):
        self.__working = True
        await self.refresh()
        while self.__priority_task:
            priority = self.__priority_task.popleft()
            await priority(self)
        self.__working = False

    def stop(self):
        self.__working = False
        if self.__work_task is not None:
            _ = self.__work_task.cancel()
            self.__work_task = None

    def __queue_priority_task(self, task: Callable):
        self.__priority_task.append(task)
        if self.__work_task is not None:
            self.__interrupted = True
            _ = self.__work_task.cancel()

    def has_job(self, job_name: str, level=1) -> bool:
        return self.__jobs.get(job_name, 0) >= level

    @request_action
    async def move(self, position: tuple[int, int]) -> bool:
        if position == self.location:
            return True
        try:
            response = await self.__client.post(
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
            self.__refresh(CharacterData.from_dict(character_data))

            print(
                f"🏃{self.name} Moved to ({destination['x']}, {destination['y']}) on {destination['name']}"
            )
            return True
        except Exception as e:
            print(f"❌ {e}")
            return False

    @request_action
    async def gather(self) -> bool:
        try:
            response = await self.__client.post(
                f"{self.__url}/action/gathering",
                headers=HEADERS,
            )
            data = response.json()

            if "error" in data:
                print("data : ", data)
                raise Exception(data["error"]["message"])

            character_data = data["data"]["character"]
            self.__refresh(CharacterData.from_dict(character_data))

            return True
        except Exception as e:
            print(f"❌ {e}")
            return False

    @request_action
    async def fight(self) -> bool:
        try:
            response = await self.__client.post(
                f"{self.__url}/action/fight",
                headers=HEADERS,
            )
            data = response.json()["data"]

            fight = data["fight"]
            characters = data["characters"]
            for character in characters:
                if character["name"] == self.name:
                    self.__refresh(CharacterData.from_dict(character))
                    break
            result = True if fight["result"] == "win" else False
            print(
                f"󰓥 {self.surname} Fought and {'won' if result else 'lost'} against {fight['opponent']}"
            )

            return result
        except Exception as e:
            print(f"❌ {e}")
            return False

    @request_action
    async def rest(self) -> bool:
        try:
            response = await self.__client.post(
                f"{self.__url}/action/rest",
                headers=HEADERS,
            )
            data = response.json()

            if "error" in data:
                print("data : ", data)
                raise Exception(data["error"]["message"])

            character_data = data["data"]["character"]
            self.__refresh(CharacterData.from_dict(character_data))

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

    @need_bank
    @request_action
    async def deposit_gold_in_bank(self, quantity: int, comeback: bool = True) -> bool:
        if quantity > self.gold:
            print(f"❌ Cannot deposit {quantity} gold, only {self.gold} available")
            return False
        if quantity <= 0:
            print(f"❌ Cannot deposit non-positive quantity of gold: {quantity}")
            return False
        try:
            response = await self.__client.post(
                f"{self.__url}/action/bank/deposit/gold",
                headers=HEADERS,
                json={"quantity": quantity},
            )
            data = response.json()

            if "error" in data:
                print("data : ", data)
                raise Exception(data["error"]["message"])

            character_data = data["data"]["character"]
            self.__refresh(CharacterData.from_dict(character_data))

            print(f"󱉏  {self.surname} Deposited {quantity} gold in bank")
            return True
        except Exception as e:
            print(f"❌ {e}")
            return False

    @need_bank
    @request_action
    async def deposit_item_in_bank(
        self, items: list[dict[str, int]], comeback: bool = True
    ) -> bool:
        try:
            response = await self.__client.post(
                f"{self.__url}/action/bank/deposit/item",
                headers=HEADERS,
                json=items,
            )
            data = response.json()

            if "error" in data:
                print("data : ", data)
                raise Exception(data["error"]["message"])

            character_data = data["data"]["character"]
            self.__refresh(CharacterData.from_dict(character_data))

            print(
                f"📥 {self.surname} Deposited {', '.join([f'{item["quantity"]}x {item["code"]}' for item in items])} in bank"
            )
            return True
        except Exception as e:
            print(f"❌ {e}")
            return False

    @need_bank
    @request_action
    async def withdraw_item_from_bank(
        self, items: list[tuple[str, int]], comeback: bool = False
    ) -> bool:
        try:
            response = await self.__client.post(
                f"{self.__url}/action/bank/withdraw/item",
                headers=HEADERS,
                json=[{"code": item, "quantity": quantity} for item, quantity in items],
            )
            data = response.json()

            if "error" in data:
                print("data : ", data)
                raise Exception(data["error"]["message"])

            character_data = data["data"]["character"]
            self.__refresh(CharacterData.from_dict(character_data))

            print(
                f"📤 {self.surname} Withdrew {', '.join([f'{item[0]}x {item[0]}' for item in items])} from bank"
            )
            return True
        except Exception as e:
            print(f"❌ {e}")
            return False

    @request_action
    async def craft(self, item: Item, quantity: int) -> bool:
        if not self.has_job(item.job, item.craft_level):
            print(
                f"❌ Cannot craft {item.name}, requires {item.job} level {item.craft_level}"
            )
            return False
        if quantity <= 0:
            print(f"❌ Cannot craft non-positive quantity of items: {quantity}")
            return False

        try:
            response = await self.__client.post(
                f"{self.__url}/action/crafting",
                headers=HEADERS,
                json={"code": item.code, "quantity": quantity},
            )
            data = response.json()

            if "error" in data:
                print("data : ", data)
                raise Exception(data["error"]["message"])

            character_data = data["data"]["character"]
            self.__refresh(CharacterData.from_dict(character_data))

            print(f"✅ {self.surname} Crafted {quantity}x {item.name}")
            return True
        except Exception as e:
            print(f"❌ {e}")
            return False

    def __refresh(self, data: CharacterData):
        self.__current_location = data.location
        self.__current_layer = data.layer
        self.__current_map_id = data.map
        self.__cooldown = data.cooldown
        self.__hp = data.hp
        self.__max_hp = data.max_hp
        self.__xp = data.xp
        self.__max_xp = data.max_xp
        self.__level = data.level
        self.__gold = data.gold
        self.__inventory = data.inventory
        self.__inventory_max_items = data.inventory_max_items
        self.__jobs = data.jobs
