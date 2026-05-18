import asyncio
from collections import deque
from collections.abc import Callable
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from models.character import Character


async def seeking_the_meaning_of_life(character: "Character"):
    print(f"🤔 {character.surname} is seeking the meaning of life...")
    await asyncio.sleep(float("inf"))


class WorkMixin(Protocol):
    _routine: Callable  # pyright: ignore[reportRedeclaration]
    _previous_routine: Callable | None = None
    _work_task: asyncio.Task | None = None
    _interrupted: bool = False
    _priority_tasks: deque[Callable]
    _character_lock: asyncio.Lock

    def __init_work_mixin__(self: "Character"):
        try:
            self._routine = self.load_routine()
        except Exception:
            self._routine: Callable = seeking_the_meaning_of_life
        self._priority_tasks = deque()
        self._character_lock = asyncio.Lock()

    @property
    def is_working(self) -> bool:
        return self.work_on != seeking_the_meaning_of_life.__name__

    @property
    def work_on(self) -> str:
        routine = self._routine.__name__
        if self._priority_tasks:
            routine += " (with priority tasks: " + ", ".join(self.priority_tasks) + ")"
        return self._routine.__name__

    @property
    def priority_tasks(self) -> list[str]:
        return [task.__name__ for task in self._priority_tasks]

    @property
    def is_interrupted(self) -> bool:
        return self._interrupted

    async def start(self: "Character"):
        async with self._character_lock:
            if self._work_task is not None:
                print("❌ Character is already started")
                return
            self._work_task = asyncio.current_task()
        try:
            print(f"🚀 {self.surname} started working on routine {self.work_on}")
            while True:
                try:
                    if self._priority_tasks:
                        priority = self._priority_tasks.popleft()
                        await priority(self)
                    else:
                        await self._routine(self)
                except asyncio.CancelledError:
                    if not self._interrupted:
                        raise
                    _ = await self.refresh()
                    self._interrupted = False
        except asyncio.CancelledError:
            pass
        finally:
            self._work_task = None

    def do_one_time_task(self: "Character", task: Callable):
        self._priority_tasks.append(task)
        if len(self._priority_tasks) == 1:
            self._interrupt_routine()

    def stop(self: "Character"):
        self._previous_routine = self._routine
        self._routine = seeking_the_meaning_of_life
        self._interrupt_routine()

    async def resume(self: "Character"):
        if self.is_working:
            print("❌ Character is already working on a routine")
            return

        if self._previous_routine is None:
            print("❌ No previous routine to resume")
            return
        self._routine = self._previous_routine

        if len(self._priority_tasks) == 0:
            self._interrupt_routine()

    def _interrupt_routine(self: "Character"):
        if self._work_task is not None:
            self._interrupted = True
            _ = self._work_task.cancel()

    def assign_routine(self: "Character", task: Callable, *args, **kwargs):
        def routine(char):
            return task(char, *args, **kwargs)

        routine.__name__ = f"{task.__name__} on {', '.join(map(str, args))}"
        routine.__name__ = f"{task.__name__}"

        self._interrupt_routine()
        self._routine = routine
