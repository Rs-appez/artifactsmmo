from uuid import UUID
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from exceptions import (
    NeedToRefreshStuffException,
    NotEnoughInBankException,
    TimeoutButSuccessException,
)
from models import Encyclopedia, LocationRegistry
from models.dataclass import Item, Map
from models.dataclass.bank import Bank
from models.enums import Layer, ZoneType
from routines import craft
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
        plan = await self.plan_move(destination)
        await plan.quick_move()

    async def plan_move(self: "Character", destination: Map) -> MovePlan:
        if destination == self.location:
            return MovePlan(self, [])

        path = await get_route(self.location, destination)
        return MovePlan(self, path)

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
    _character: "Character"
    _start_location: Map
    _path: list[Map]

    _actions_for_prepare: list[Callable]
    _has_prepared: bool

    _actions_to_perform: list[Callable]
    _has_executed: bool

    _gold_needed: int
    _items_needed: dict[Item, int]
    _items_token: UUID | None

    def __init__(self, character: Character, path: list[Map]):
        self._character = character
        self._start_location = character.location
        self._path = path

        self._actions_to_perform = []
        self._actions_for_prepare = []
        self._has_prepared = False
        self._has_executed = False

        self._gold_needed = 0
        self._items_needed = {}
        self._items_token = None

        self._compute_actions()

    @property
    def is_ready(self) -> bool:
        return self._has_prepared or len(self._actions_for_prepare) == 0

    @property
    def how_much_gold_needed(self) -> int:
        return self._gold_needed

    @property
    def how_much_items_needed(self) -> dict[Item, int]:
        return self._items_needed

    def _compute_actions(self, with_cost: bool = True) -> None:
        for i, map in enumerate(self._path):
            self._add_action(lambda map=map: self._character._move(map))
            if i + 1 < len(self._path) and map.has_transition:
                if with_cost and (cost := map.transition_cost):
                    self._handle_transition_cost(cost)
                self._add_action(lambda: self._character._transition())

    async def quick_move(self) -> None:
        await self.prepare()
        await self.execute_move()

    async def prepare(self) -> None:
        if self._has_prepared:
            return

        await self._prepare_items_needed()

        for action in self._actions_for_prepare:
            await action()

        self._has_prepared = True

    async def execute_move(self) -> None:
        try:
            if not self.is_ready:
                raise Exception("MovePlan is not ready. Call prepare() first.")

            if self._has_executed:
                return

            await self._get_ready()
            await self._recompute_path()

            for action in self._actions_to_perform:
                await action()

            self._has_executed = True

        finally:
            if self._items_token is not None:
                Bank._unreserve_items(self._items_token)
                self._items_token = None

    async def _get_ready(self) -> None:
        if self._items_needed:
            await self._get_items_needed()
        if self._gold_needed > 0:
            await self._get_gold_needed()

    async def _recompute_path(self) -> None:
        if self._character.location != self._start_location:
            self._path = await get_route(self._character.location, self._path[-1])
            self._actions_to_perform.clear()
            self._compute_actions(with_cost=False)

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

        try:
            async with Bank.reserve_items(
                self._items_needed, auto_unreserve_token=False
            ) as token:
                self._items_token = token
        except NotEnoughInBankException as e:
            print(
                f"❌ {self._character.surname} Not enough items in bank to prepare move: {e}"
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
