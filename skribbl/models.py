# -*- coding: utf-8 -*-

import attr

from typing import Iterable, Type
from enum import IntEnum, unique, Enum


__all__ = (
    'Language',
    'Colour',
    'Mouth',
    'Hat',
    'Eye',
    'Avatar',
    'Player'
)

@unique
class Language(Enum):
    English = "English"
    German = "German"
    Bulgarian = "Bulgarian"
    Czech = "Czech"
    Danish = "Danish"
    Dutch = "Dutch"
    Finnish = "Finnish"
    French = "French"
    Estonian = "Estonian"
    Greek = "Greek"
    Hebrew = "Hebrew"
    Hungarian = "Hungarian"
    Italian = "Italian"
    Korean = "Korean"
    Latvian = "Latvian"
    Macedonian = "Macedonian"
    Norwegian = "Norwegian"
    Portuguese = "Portuguese"
    Polish = "Polish"
    Romanian = "Romanian"
    Serbian = "Serbian"
    Slovakian = "Slovakian"
    Spanish = "Spanish"
    Swedish = "Swedish"
    Tagalog = "Tagalog"
    Turkish = "Turkish"


@unique
class Colour(IntEnum):
    Red = 0
    Orange = 1
    Yellow = 2
    Green = 3
    Cyan = 4
    Blue = 5
    Pink = 6
    Purple = 7
    Grey = 8
    Brown = 9
    DarkBrown = 10
    Cream = 11
    RedStriped = 12
    YellowStriped = 13
    GreenStriped = 14
    BlueStriped = 15
    PinkStriped = 16
    GreyStriped = 17


@unique
class Mouth(IntEnum):
    Gritted = 0
    Sad = 1
    Smile = 2
    Neutral = 3
    Suprised = 4
    Vampire = 5
    Muted = 6
    HigherSmile = 7
    WideSmile = 8
    Wobbly = 9
    Triangle = 10
    Baby = 11
    Woah = 12
    Cheeky = 13
    Gentleman = 14
    MexicanoLong = 15
    Killer = 16
    Dog = 17
    Opened = 18
    Shocked = 19
    Stiched = 20
    SlightSmile = 21
    Mexicano = 22
    Stache = 23


@unique
class Hat(IntEnum):
    Default = -1


@unique
class Eye(IntEnum):
    Default = 0
    Blinking = 1
    Browless = 2
    TiredBlinking = 3
    Concerned = 4
    Happy = 5
    Unpleased = 6
    Cyclop = 7
    Cross = 8
    Annoyed = 9
    Shut = 10
    Crossed = 11
    CrossedFrown = 12
    Gone = 13
    Tired = 14
    Three = 15
    Sunglasses = 16
    Sad = 17
    WideCyclop = 18
    AlienCyclop = 19
    Glasses = 20
    Eggs = 21
    Patch = 22
    Alien = 23
    DarkGlasses = 24
    Crosses = 25
    SmallBig = 26
    BigSmall = 27
    Frown = 28
    Upset = 29
    Monobrow = 30


@attr.s(slots=True)
class Avatar:
    colour: Colour = attr.ib(converter=Colour)
    eye: Eye = attr.ib(converter=Eye)
    mouth: Mouth = attr.ib(converter=Mouth)
    hat: Hat = attr.ib(default=Hat.Default)

    @classmethod
    def from_iterable(cls: Type['Avatar'], it: Iterable[int]) -> 'Avatar':
        return cls(*it)


@attr.s(slots=True)
class Player:
    name: str = attr.ib()
    avatar: Avatar = attr.ib(converter=Avatar.from_iterable)
