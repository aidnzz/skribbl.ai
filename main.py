# -*- coding: utf-8 -*-

import asyncio
import logging

from skribbl import Skribbl, Player, Avatar, Mouth, Colour, Eye

log = logging.getLogger("skribbl")
log.setLevel(logging.INFO)

async def main():
    player = Player("test", Avatar(Colour.Red, Eye.Annoyed, Mouth.Killer))
    skribbl = await Skribbl.join(player)
    async with skribbl:
        print("Game in progress...")

if __name__ == "__main__":
    asyncio.run(main())
