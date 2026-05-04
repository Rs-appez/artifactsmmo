#!.venv/bin/python
from models import Character
from routines import chicken_farm, copper_farm, ash_farm, gudgeon_farm, sunflower_farm
import asyncio


async def main():
    bob = Character("rs_bob")
    bob.assign_routine(chicken_farm)

    alice = Character("rs_alice")
    alice.assign_routine(ash_farm)

    john = Character("rs_john")
    john.assign_routine(copper_farm)

    jane = Character("rs_jane")
    jane.assign_routine(gudgeon_farm)

    charlie = Character("rs_charlie")
    charlie.assign_routine(sunflower_farm)

    _ = await asyncio.gather(
        bob.work(),
        alice.work(),
        john.work(),
        jane.work(),
        charlie.work(),
    )


if __name__ == "__main__":
    asyncio.run(main())
