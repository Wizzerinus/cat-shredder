# Cat Shredder

Welcome to the repository of the Cat Shredder toontown source!

## Design goals

Cat Shredder is an ultra-compact source of Toontown Online (under 39 thousand LOC at the time of writing) made for use in Crane League. This size was achieved by removing (or rather, not including) all functionality that is not going to be used in Crane League. This includes:

* Cog battles, cogs, gags, inventory management, experience, etc.
* Streets, playgrounds, trolley games, etc.
* Estates, catalog, mailbox delivery, house decoration
* Parties, activities like fishing, holidays, fireworks.
* RPC functionality, Disney launcher integration, etc.
* Buildings, suit buildings, field offices, etc.
* The unused cog bosses (VP, CJ, CEO)
* Cog facilities such as Sellbot Factory, Cashbot Mint
* Cog disguises
* Toontorial
* Moderation capabilities such as name approval, chat filtering
* Sticker book

Implementation of the following is planned:

* Make-a-toon and related functionality - done
* Toon movement, orbital camera - done
* Chat, emotes, unites, magic words - done
  * Currently only a small set of magic words is implemented, more will be added as needed
* Cashbot HQ trainyard and lobby - done
* The final phase of the CFO fight (without cog battles) - in progress

## Credits

This source code is vaguely based on source codes of Open-Toontown, Toontown Galaxy and Toontown: Event Horizon mixed together with other additions and cleanup. Other credits include:

* [Astron](https://github.com/Astron/Astron)
* [Panda3D](https://github.com/panda3d/panda3d)
* Reverse-engineered Toontown Online client/server source code is property of The Walt Disney Company.

## Dependencies

### Panda3D

This source code requires a customized version of Panda3D to run. [Open-Toontown builds](https://github.com/open-toontown/panda3d) are fully supported. Note that only Python 3 builds will be supported (the minimum compatible version right now is Python 3.8).

[Open-Toontown build for Windows](https://mega.nz/file/uAMxEKqL#yQfS9UPpYHzKYDR5vq-LF5gxxLa6HUmxLUp65uzneVo)

### Astron

This source code requires Astron to run. [Official builds](https://github.com/astron/astron) are fully supported.
