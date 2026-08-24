import asyncio
from collections import deque
from types import FunctionType
from typing import TYPE_CHECKING

from routines import make_food

if TYPE_CHECKING:
    from models.character import Character


async def seeking_the_meaning_of_life(character: "Character"):
    print(f"🤔 {character.surname} is seeking the meaning of life...")
    await asyncio.sleep(float("inf"))


class WorkRoutine:
    def __init__(self, task: FunctionType, *args, is_routine: bool = False, **kwargs):
        self.name = task.__name__
        self.module = task.__module__
        self.args = args
        self.kwargs = kwargs
        self._is_routine = is_routine
        self._is_paused = False
        self._task = task

    def __call__(self, character: "Character") -> asyncio.Future:
        return self._task(character, *self.args, **self.kwargs)

    @property
    def is_pauseable(self) -> bool:
        return self._is_routine

    @property
    def is_paused(self) -> bool:
        return self._is_paused

    def pause(self):
        if not self.is_pauseable:
            raise Exception("This routine cannot be paused")
        self._is_paused = True

    def resume(self):
        if not self.is_pauseable:
            raise Exception("This routine cannot be resumed")
        self._is_paused = False


class WorkMixin:
    _routine: WorkRoutine
    _previous_routine: WorkRoutine | None = None
    _work_task: asyncio.Task | None = None
    _interrupted: bool = False
    _priority_tasks: deque[WorkRoutine]
    _character_lock: asyncio.Lock

    def __init_work_mixin__(self: "Character"):
        try:
            self._routine = self.load_routine()
        except Exception as e:
            print(
                f"❌ No routine found for {self.surname}, defaulting to seeking the meaning of life. Error: {e}"
            )
            self.seek_the_meaning_of_life()
        self._priority_tasks = deque()
        self._character_lock = asyncio.Lock()

    @property
    def is_working(self) -> bool:
        return self.work_on != seeking_the_meaning_of_life.__name__

    @property
    def work_on(self) -> str:
        return self._routine.name

    @property
    def priority_tasks(self) -> list[str]:
        return [task.name for task in self._priority_tasks]

    @property
    def is_interrupted(self) -> bool:
        return self._interrupted

    @property
    def get_routine_data(self) -> dict:
        return {
            "routine_name": self._routine.name,
            "routine_module": self._routine.module,
            "routine_args": self._routine.args or [],
            "routine_kwargs": self._routine.kwargs or {},
        }

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
                        self._routine.pause()
                        priority = self._priority_tasks.popleft()
                        await priority(self)
                    else:
                        self._routine.resume()
                        await self._routine(self)
                except asyncio.CancelledError:
                    if not self._interrupted:
                        raise
                    _ = await self.refresh()
                    self._interrupted = False
                except Exception as e:
                    print(f"❌ {self.surname} work error : {e}")
                    if not self._routine.is_paused:
                        self.make_default_routine()

        except asyncio.CancelledError:
            pass
        finally:
            self._work_task = None

    def do_one_time_task(self: "Character", task: FunctionType, *args, **kwargs):
        mission = WorkRoutine(task, *args, **kwargs)
        self._priority_tasks.append(mission)
        if not self._routine.is_paused:
            self._interrupt_routine()

    def seek_the_meaning_of_life(self: "Character"):
        self._routine = WorkRoutine(seeking_the_meaning_of_life, is_routine=True)

    def make_default_routine(self: "Character"):
        self._routine = WorkRoutine(make_food, "cooked_salmon", is_routine=True)

    def stop(self: "Character"):
        self._previous_routine = self._routine
        if not self._routine.is_paused and self.is_working:
            self.seek_the_meaning_of_life()
        self._interrupt_routine()
        print("previous routine was:")
        print(self._previous_routine.name)

    async def resume(self: "Character"):
        if self.is_working:
            print("❌ Character is already working on a routine")
            return
        if self._routine.is_paused:
            print("❌ Current routine is not a valid routine, cannot resume")
            self._priority_tasks.clear()
            self._interrupt_routine()
            return

        if self._previous_routine is None:
            print("❌ No previous routine to resume")
            return
        print(f"Resuming previous routine: {self._previous_routine.name}")
        self._routine = self._previous_routine
        self._interrupt_routine()

    def _interrupt_routine(self: "Character"):
        if self._work_task is not None:
            self._interrupted = True
            _ = self._work_task.cancel()

    def assign_routine(self: "Character", task: FunctionType, *args, **kwargs):

        self._interrupt_routine()
        self._routine = WorkRoutine(task, *args, is_routine=True, **kwargs)
