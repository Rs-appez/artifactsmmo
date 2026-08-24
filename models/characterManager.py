from models import Character
from models.dataclass import Event, Monster, Resource
from routines import gather, mob_farm


class CharacterManager:
    def __init__(self, characters: dict[str, Character]):
        self.characters = characters

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
            if character.work_on == "boss_farm":
                continue
            if character.level >= monster.level:
                character.do_one_time_task(mob_farm, monster)

    def _farm_gather_event(self, event: Event):
        if not isinstance(event.content, Resource):
            print(f"❌ Invalid event content for gathering: {event.content}")
            return
        item = min(event.content.drops.items(), key=lambda d: d[1]["rate"])[0]
        for character in self.characters.values():
            if character.work_on == "boss_farm":
                continue
            if character.has_job(item.job, item.level):
                character.do_one_time_task(gather, item)
