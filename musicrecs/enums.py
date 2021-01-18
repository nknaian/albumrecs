import enum


class MusicRecsEnum(enum.Enum):
    @classmethod
    def choices(cls):
        return [(choice, choice.name) for choice in cls]

    @classmethod
    def coerce(cls, item):
        return cls(int(item)) if not isinstance(item, cls) else item

    def __str__(self):
        return str(self.value)


class MusicType(MusicRecsEnum):
    track = 0
    album = 1


class RoundStatus(MusicRecsEnum):
    submit = 0
    listen = 1
    revealed = 2


class SnoozinRecType(MusicRecsEnum):
    random = 0
    similar = 1


class NewType(MusicRecsEnum):
    random = 0
    similar = 1