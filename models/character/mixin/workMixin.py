import asyncio
from collections import deque
from collections.abc import Callable
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from models.character import Character


class WorkMixin(Protocol):
    _task: Callable | None = None
    _working = False
    _work_task: asyncio.Task | None = None
    _interrupted: bool = False
    _priority_task: deque[Callable] = deque()

    @property
    def is_working(self) -> bool:
        return self._working

    @property
    def work_on(self) -> str | None:
        if self._task is None:
            return None
        return self._task.__name__

    @property
    def is_interrupted(self) -> bool:
        return self._interrupted

    async def work(self: "Character"):
        if self._task is None:
            print("❌ No task assigned to character")
            return
        self._working = True
        self._work_task = asyncio.current_task()
        print(f"🚀 {self.name} started working on routine {self._task.__name__}")
        try:
            while self._working:
                if self._task is None:
                    print("❌ No task assigned to character")
                    self.stop()
                    return
                try:
                    await self._task(self)
                except asyncio.CancelledError:
                    if not self._interrupted:
                        raise
                    self._interrupted = False
                    while self._priority_task:
                        priority = self._priority_task.popleft()
                        await priority(self)
        except asyncio.CancelledError:
            pass
        finally:
            self._working = False
            self._work_task = None

    def do_one_time_task(self: "Character", task: Callable):
        self._queue_priority_task(task)
        if not self.is_working:
            _ = asyncio.create_task(self._do_priority_task())

    async def _do_priority_task(self: "Character"):
        self._working = True
        _ = await self.refresh()
        while self._priority_task:
            priority = self._priority_task.popleft()
            await priority(self)
        self._working = False

    def stop(self: "Character"):
        self._working = False
        if self._work_task is not None:
            _ = self._work_task.cancel()
            self._work_task = None

    def _queue_priority_task(self: "Character", task: Callable):
        self._priority_task.append(task)
        if self._work_task is not None:
            self._interrupted = True
            _ = self._work_task.cancel()

    def assign_routine(self: "Character", task: Callable):
        self._task = task
