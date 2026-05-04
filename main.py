#!.venv/bin/python
from models import Character
from routines import chicken_farm, copper_farm
import asyncio


async def main():
    bob = Character("rs_bob")
    bob.assign_routine(chicken_farm)

    alice = Character("rs_alice")
    alice.assign_routine(copper_farm)

    _ = await asyncio.gather(
        bob.work(),
        alice.work(),
    )


if __name__ == "__main__":
    asyncio.run(main())
