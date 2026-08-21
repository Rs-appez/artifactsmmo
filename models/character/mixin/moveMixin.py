import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from itertools import chain
from typing import TYPE_CHECKING, AsyncGenerator, Callable
from uuid import UUID

from exceptions import (
    ImpossibleCraftException,
    NotEnoughInBankException,
    TimeoutButSuccessException,
)
from models import Encyclopedia, LocationRegistry
from models.dataclass import Item, Map, Resource
from models.dataclass.bank import Bank
from models.enums import ZoneType
from routines import generate_missing_items
from utils.pathfinding import get_route

if TYPE_CHECKING:
    from models.character import Character


@dataclass
class MoveMixin:
    _location: Map

    @property
    def location(self: "Character") -> Map:
        return self._location

    async def move(self: "Character", destination: Map) -> None:
        async with self.plan_move(destination) as plan:
            await plan.quick_move()

    @asynccontextmanager
    async def plan_move(
        self: "Character", destination: Map
    ) -> AsyncGenerator[MovePlan]:
        try:
            if destination == self.location:
                yield MovePlan(self, ([destination], 0))
                return

            path = await get_route(self.location, destination)
            with MovePlan(self, path) as plan:
                yield plan

        except Exception as e:
            print(f"❌ {self.surname} failed to plan move : {e}")
            raise e

    async def _move(self: "Character", destination: Map) -> None:
        if destination == self.location:
            return

        try:
            await self.post_api("/move", json_data={"map_id": destination.map_id})

            arrived = self.location

            print(
                f"🏃 {self.surname} Moved to ({arrived.x}, {arrived.y}) on {arrived.name} (layer : {arrived.layer.value})"
            )
        except TimeoutButSuccessException:
            print(
                f"🏃 {self.surname} Moved to ({destination.x}, {destination.y}) on {destination.name} (layer : {destination.layer.value}) (timeout but success)"
            )

    async def _transition(self: "Character") -> bool:
        try:
            await self.post_api("/transition")
            destination = self.location

            print(
                f"󰓡 {self.surname} Transitioned to ({destination.x}, {destination.y}) on {destination.name} (layer : {destination.layer.value})"
            )
            return True
        except TimeoutButSuccessException:
            destination = self.location
            print(
                f"󰓡 {self.surname} Transitioned to ({destination.x}, {destination.y}) on {destination.name} (layer : {destination.layer.value}) (timeout but success)"
            )
            return True
        except Exception as e:
            print(f"❌ {self.surname} transition : {e}")
            return False


class MovePlan:
    def __init__(self, character: Character, path: tuple[list[Map], int]):
        self._character = character
        self._start_location = character.location
        self._path = path[0]
        self._total_cost = path[1]

        self._actions_to_perform: list[Callable] = []
        self._use_potions: list[Callable] = []
        self._actions_for_prepare: list[Callable] = []
        self._has_prepared = False
        self._has_executed = False
        self._can_shortcut = True

        self._gold_needed = 0
        self._items_needed: dict[Item, int] = {}
        self._items_token: UUID | None = None

        self._actions_computed = asyncio.Event()
        asyncio.create_task(self._compute_actions())

    @property
    def is_ready(self) -> bool:
        return self._has_prepared or len(self._actions_for_prepare) == 0

    @property
    def how_much_gold_needed(self) -> int:
        return self._gold_needed

    @property
    def how_much_items_needed(self) -> dict[Item, int]:
        return self._items_needed

    def __enter__(self):
        return self

    def __exit__(self, *_):
        """Cleanup when exiting context"""
        if self._items_token is not None:
            Bank._unreserve_items(self._items_token)
            self._items_token = None

    async def quick_move(self) -> None:
        await self.prepare()
        await self.execute_move()

    async def _compute_actions(self, with_cost: bool = True) -> None:

        if with_cost and self._can_shortcut and self._total_cost > 0:
            await self._check_shortcut()

        for i, map in enumerate(self._path):
            self._add_action(lambda map=map: self._character._move(map))
            if i + 1 < len(self._path) and map.has_transition:
                if with_cost and (cost := map.transition_cost):
                    self._handle_transition_cost(cost)
                self._add_action(lambda: self._character._transition())

        self._actions_computed.set()

    async def prepare(self) -> None:
        await self._actions_computed.wait()

        if self._has_prepared:
            return
        try:
            await self._prepare_items_needed()

        except ImpossibleCraftException:
            self._can_shortcut = False
            self._actions_computed.clear()
            await self._compute_actions(with_cost=True)
            await self._prepare_items_needed()

        for action in self._actions_for_prepare:
            await action()

        self._has_prepared = True

    async def execute_move(self) -> None:
        if not self.is_ready:
            raise Exception("MovePlan is not ready. Call prepare() first.")

        if self._has_executed:
            return

        await self._get_ready()
        await self._recompute_path()

        for action in chain(self._use_potions, self._actions_to_perform):
            await action()

        self._has_executed = True

    async def _get_ready(self) -> None:
        if self._items_token and len(Bank.get_token_info(self._items_token)) > 0:
            await self._get_items_needed()
        if self._gold_needed > 0:
            await self._get_gold_needed()

    async def _recompute_path(self) -> None:
        if self._character.location != self._start_location:
            self._path, self._total_cost = await get_route(
                self._character.location, self._path[-1]
            )
            self._actions_to_perform.clear()
            self._use_potions.clear()
            await self._compute_actions()

    async def _check_shortcut(self) -> None:
        if not self._path:
            return
        final_zone = self._path[-1].zone
        if final_zone != self._character.location.zone:
            match final_zone:
                case ZoneType.ENCHANTED_FOREST:
                    await self._setup_potion("enchanted_potion")
                case ZoneType.SANDWHISPER:
                    # ugly hack before handling correctly the return cost
                    potion = await Encyclopedia.get_item_by_code("forest_bank_potion")
                    self.add_item_needed(potion, 1)
                    pass
                    # TODO : need to handle achievement for this potion
                case ZoneType.DEFAULT:
                    await self._setup_potion("forest_bank_potion")

    async def _get_gold_needed(self) -> None:
        if self._character.gold < self._gold_needed:
            await self._character.withdraw_gold_from_bank(self._gold_needed)

    async def _get_items_needed(self) -> None:
        if self._items_token is None:
            raise Exception("Items token is not set. Cannot retrieve items.")
        await self._character.withdraw_item_from_bank(self._items_token)

    async def _prepare_items_needed(self) -> None:
        if not self._items_needed:
            return

        if self._character.has_in_inventory(self._items_needed):
            return

        retry = True
        while retry:
            retry = False
            try:
                async with Bank.reserve_items(
                    self._items_needed,
                    auto_unreserve_token=False,
                    inventory=self._character.inventory,
                ) as token:
                    self._items_token = token
            except NotEnoughInBankException as e:
                for item in e.missing_items:
                    if item.is_gatherable_resource:
                        if not await self._can_gather(item):
                            # todo : refactor gather to restrict to the current zone if needed
                            raise ImpossibleCraftException(
                                f"Cannot gather {item.name} in the current zone. Missing items: {e.missing_items}"
                            )
                    elif item.is_craftable:
                        # todo : check if we have recipes available to craft the item
                        pass

                await generate_missing_items(self._character, self._items_needed)
                retry = True

    async def _setup_potion(self, potion_name: str) -> None:

        teleport_effect = await Encyclopedia.get_effect_by_code("teleport")
        tp_potion = await Encyclopedia.get_item_by_code(potion_name)
        self.add_item_needed(tp_potion, 1)
        self._use_potions.append(lambda: self._character.use_item(tp_potion))
        tp_destination = tp_potion.effects[teleport_effect]
        tp_destination_map = await LocationRegistry.get_map_by_id(tp_destination)
        self._path, self._total_cost = await get_route(
            tp_destination_map, self._path[-1]
        )

    def _add_action(self, action: Callable) -> None:
        if self._has_executed:
            raise Exception("Cannot add actions after execution.")
        self._actions_to_perform.append(action)

    def add_prepare_action(self, action: Callable) -> None:
        if self._has_prepared:
            raise Exception("Cannot add prepare actions after preparation.")
        self._actions_for_prepare.append(action)

    def add_gold_needed(self, amount: int) -> None:
        self._gold_needed += amount

    def add_item_needed(self, item: Item, amount: int) -> None:
        self._items_needed[item] = self._items_needed.get(item, 0) + amount

    def _handle_transition_cost(self, cost: tuple[Item | None, int]) -> None:
        item, amount = cost
        if item is None:
            self.add_gold_needed(amount)
        else:
            self.add_item_needed(item, amount)

    async def _can_gather(self, item: Item) -> bool:
        if not item.is_gatherable_resource:
            return False
        resources = Resource.from_drop_item(item)
        found_valid_zone = False
        for resource in resources:
            zones = await LocationRegistry.get_zones_locations(resource)
            if any(zone != self._path[-1].zone for zone in zones):
                found_valid_zone = True
                break

        return found_valid_zone
