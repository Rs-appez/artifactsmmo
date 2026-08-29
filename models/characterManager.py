from models import Character
from models.dataclass import Event, Monster, Raid, Resource
from routines import gather, mob_farm
from routines.monster_farm import raid_farm


class CharacterManager:
    def __init__(self, characters: dict[str, Character]):
        self.characters = characters

    def start_raid(self, raid: Raid):

        # tmp implementation

        raid_boss = raid.boss

        charlie = self.characters.get("charlie")
        dave = self.characters.get("dave")
        eve = self.characters.get("eve")

        teammates = [charlie, eve, dave]

        if not dave or not charlie or not eve:
            print("❌ Missing characters for the test")
            return
        dave.assign_routine(raid_farm, teammates, raid_boss, True)
        charlie.assign_routine(raid_farm, teammates, raid_boss, False)
        eve.assign_routine(raid_farm, teammates, raid_boss, False)

    def new_event_occurred(self, event: Event):
        match event.content:
            case Resource():
                self._farm_gather_event(event)
            case Monster():
                self._farm_monster_event(event)
            case _:
                pass

    def _farm_monster_event(self, event: Event):
        if not isinstance(event.content, Monster):
            print(f"❌ Invalid event content for hunting: {event.content}")
            return
        monster = event.content
        if monster.is_boss or monster.code in [
            "corrupted_ogre",
            "bandit_lizard",
            "demon",
            "full_moon_vampire",
        ]:
            return
            # TODO: Implement boss hunting logic

        for character in self.characters.values():
            if character.work_on in ["raid_farm", "boss_farm"]:
                continue
            if character.level >= monster.level:
                character.do_one_time_task(mob_farm, monster)

    def _farm_gather_event(self, event: Event):
        if not isinstance(event.content, Resource):
            print(f"❌ Invalid event content for gathering: {event.content}")
            return
        item = min(event.content.drops.items(), key=lambda d: d[1]["rate"])[0]
        for character in self.characters.values():
            if character.work_on in ["raid_farm", "boss_farm"]:
                continue
            if character.has_job(item.job, item.level):
                character.do_one_time_task(gather, item)
