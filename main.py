#!.venv/bin/python
from models import Character
from routines import chicken_farm


def main():
    bob = Character("rs_bob")
    bob.assign_routine(chicken_farm)
    bob.work()

    # alice = Character("rs_alice")
    # asyncio.run(chicken_farm(alice))


if __name__ == "__main__":
    main()
