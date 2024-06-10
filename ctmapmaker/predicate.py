import functools
import math
import yaml

from ctmapmaker.eval import mapmaker_compile


with open('/ctmapgen-data/conf/conf.yaml', 'r') as f:
    conf = yaml.safe_load(f)


class TowerCategory:
    @staticmethod
    def validlist():
        return ['Primary', 'Military', 'Magic', 'Support']

    def __init__(self, tile, category):
        self.tile = tile
        self.category = category

    def __getitem__(self, name):
        if name == 'count':
            sum = 0
            towers_category = conf['towers'][self.category.lower()]
            for tower in self.tile['GameData']['dcModel']['towers']['_items']:
                if tower['tower'] in towers_category:
                    count = tower['max']
                    if count < 0:
                        count = math.inf
                    sum += count
            return sum
        raise AttributeError(name)

    def __bool__(self):
        return bool(self['count'])

    def __eq__(self, other):
        if isinstance(other, TowerCategory):
            return self.category == other.category
        if isinstance(other, int):
            return self['count'] == other
        return NotImplemented

    def __lt__(self, other):
        if isinstance(other, int):
            return self['count'] < other
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, int):
            return self['count'] <= other
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, int):
            return self['count'] > other
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, int):
            return self['count'] >= other
        return NotImplemented


class Tower:
    @staticmethod
    def validlist():
        return conf['towers']['regular']

    def __init__(self, tile, tower):
        self.tile = tile
        self.tower = tower

    def __getitem__(self, name):
        if name == 'category':
            for category in TowerCategory.validlist():
                if self.tower in conf['towers'][category.lower()]:
                    return TowerCategory(self.tile, category)
            assert False
        if name == 'count':
            for tower in self.tile['GameData']['dcModel']['towers']['_items']:
                if tower['tower'] == self.tower:
                    count = tower['max']
                    if count < 0:
                        count = math.inf
                    return count
            return 0
        raise AttributeError(name)

    def __bool__(self):
        return bool(self['count'])

    def __eq__(self, other):
        if isinstance(other, Tower):
            return self.tower == other.tower
        if isinstance(other, TowerCategory):
            return self['category'] == other
        if isinstance(other, int):
            return self['count'] == other
        return NotImplemented

    def __lt__(self, other):
        if isinstance(other, int):
            return self['count'] < other
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, int):
            return self['count'] <= other
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, int):
            return self['count'] > other
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, int):
            return self['count'] >= other
        return NotImplemented


class Hero:
    @staticmethod
    def validlist():
        return conf['towers']['hero']

    def __init__(self, tile, hero):
        self.tile = tile
        self.hero = hero

    def __getitem__(self, name):
        if name == 'enabled':
            for tower in self.tile['GameData']['dcModel']['towers']['_items']:
                if tower['tower'] == 'ChosenPrimaryHero':
                    if tower['max']:
                        return True
                if tower['tower'] == self.hero:
                    if tower['max']:
                        return True
            return False
        raise AttributeError(name)

    def __bool__(self):
        return self['enabled']

    def __eq__(self, other):
        if isinstance(other, Hero):
            return self.hero == other.hero
        if isinstance(other, bool):
            return self['enabled'] == other
        return NotImplemented


@functools.total_ordering
class MapDifficulty:
    @staticmethod
    def validlist():
        return ['Beginner', 'Intermediate', 'Advanced', 'Expert']

    def __init__(self, tile, difficulty):
        self.tile = tile
        self.difficulty = difficulty
        self.difficultyidx = self.validlist().index(difficulty)

    def __eq__(self, other):
        if isinstance(other, MapDifficulty):
            return self.difficultyidx == other.difficultyidx
        return NotImplemented

    def __lt__(self, other):
        if isinstance(other, MapDifficulty):
            return self.difficultyidx < other.difficultyidx
        return NotImplemented

    def __bool__(self):
        return self == Map(self.tile, self.tile['GameData']['selectedMap'])[
                'difficulty']


class Map:
    @staticmethod
    @functools.cache
    def validlist():
        return [map['id'] for map in conf['maps']]

    @classmethod
    def of(cls, tile):
        return cls(tile, tile['GameData']['selectedMap'])

    def __init__(self, tile, map):
        self.tile = tile
        self.map = map

    def __getitem__(self, name):
        if name == 'difficulty':
            for map in conf['maps']:
                if map['id'] == self.map:
                    return MapDifficulty(
                        self.tile, MapDifficulty.validlist()[
                            map['difficulty']])
            assert False
        raise AttributeError(name)

    def __eq__(self, other):
        if isinstance(other, Map):
            return self.map == other.map
        return NotImplemented

    def __bool__(self):
        return self.map == self.tile['GameData']['selectedMap']


@functools.total_ordering
class Difficulty:
    @staticmethod
    def validlist():
        return ['Easy', 'Medium', 'Hard', 'Impoppable']

    @classmethod
    def of(cls, tile):
        return cls(tile, tile['GameData']['selectedDifficulty'])

    def __init__(self, tile, difficulty):
        self.tile = tile
        self.difficulty = difficulty
        self.difficultyidx = self.validlist().index(difficulty)

    def __eq__(self, other):
        if isinstance(other, Difficulty):
            return self.difficultyidx == other.difficultyidx
        return NotImplemented

    def __lt__(self, other):
        if isinstance(other, Difficulty):
            return self.difficultyidx < other.difficultyidx
        return NotImplemented

    def __bool__(self):
        return self.difficulty == self.tile['GameData']['selectedDifficulty']


class GameType:
    GAMEMODEMAP = {
        'Race': 2,
        'LeastCash': 8,
        'LeastTiers': 9,
        'Boss': 4,
    }

    @classmethod
    def validlist(cls):
        return list(cls.GAMEMODEMAP.keys())

    @classmethod
    def of(cls, tile):
        gametypenum = tile['GameData']['subGameType']
        for k, v in cls.GAMEMODEMAP.items():
            if v == gametypenum:
                return cls(tile, k)
        assert False

    def __init__(self, tile, gametype):
        self.tile = tile
        self.gametype = gametype
        self.gametypenum = self.GAMEMODEMAP[gametype]

    def __eq__(self, other):
        if isinstance(other, GameType):
            return self.gametypenum == other.gametypenum
        return NotImplemented

    def __bool__(self):
        return self.gametypenum == self.tile['GameData']['subGameType']


class Boss:
    @classmethod
    def validlist(cls):
        return ['Bloonarius', 'Lych', 'Vortex', 'Dreadbloon', 'Phayze']

    @classmethod
    def of(cls, tile):
        if 'bossData' not in tile['GameData']:
            return None

        return cls(tile, cls.validlist()[
            tile['GameData']['bossData']['bossBloon']])

    def __init__(self, tile, boss):
        self.tile = tile
        self.boss = boss
        self.bossnum = self.validlist().index(boss)

    def __eq__(self, other):
        if isinstance(other, Boss):
            return self.bossnum == other.bossnum
        if isinstance(other, GameType):
            return other.gametype == 'Boss'
        return NotImplemented

    def __bool__(self):
        if 'bossData' not in self.tile['GameData']:
            return False
        return self.bossnum == self.tile['GameData']['bossData']['bossBloon']


class TileType:
    @classmethod
    def validlist(cls):
        return ['Regular', 'Banner', 'Relic']

    @classmethod
    def of(cls, tile):
        return cls(tile, cls.fixup_teamfirst(tile['TileType']))

    @staticmethod
    def fixup_teamfirst(tiletype):
        if tiletype == 'TeamFirstCapture':
            return 'Regular'
        return tiletype

    def __init__(self, tile, tiletype):
        self.tile = tile
        self.tiletype = tiletype

    def __eq__(self, other):
        if isinstance(other, TileType):
            return self.tiletype == other.tiletype
        return NotImplemented

    def __bool__(self):
        return self.tiletype == self.fixup_teamfirst(self.tile['TileType'])


class RelicType:
    @classmethod
    def validlist(cls):
        return conf['relics']

    @classmethod
    def of(cls, tile):
        if tile['RelicType'] == 'None':
            return None
        return cls(tile, tile['RelicType'])

    def __init__(self, tile, relictype):
        self.tile = tile
        self.relictype = relictype

    def __eq__(self, other):
        if isinstance(other, RelicType):
            return self.relictype == other.relictype
        if isinstance(other, TileType):
            return other.tiletype == 'Relic'
        return NotImplemented

    def __bool__(self):
        return self.relictype == self.tile['RelicType']


class Context:
    ALIASES = {
        'monkeymeadow': 'tutorial',

        # tower
        'dart': 'dartmonkey',
        'boomerang': 'boomerangmonkey',
        'boomer': 'boomerangmonkey',
        'bomb': 'bombshooter',
        'tack': 'tackshooter',
        'ice': 'icemonkey',
        'glue': 'gluegunner',
        'sniper': 'snipermonkey',
        'sub': 'monkeysub',
        'buccaneer': 'monkeybuccaneer',
        'boat': 'monkeybuccaneer',
        'ace': 'monkeyace',
        'heli': 'helipilot',
        'mortar': 'mortarmonkey',
        'dartling': 'dartlinggunner',
        'wizard': 'wizardmonkey',
        'super': 'supermonkey',
        'ninja': 'ninjamonkey',
        'alch': 'alchemist',
        # 'druid',
        'farm': 'bananafarm',
        'spike': 'spikefactory',
        'spact': 'spikefactory',
        'spac': 'spikefactory',
        'village': 'monkeyvillage',
        'engineer': 'engineermonkey',
        'engi': 'engineermonkey',
        'beast': 'beasthandler',

        # hero
        # 'quincy',
        'gwen': 'gwendolin',
        'striker': 'strikerjones',
        'jones': 'strikerjones',
        'obyn': 'obyngreenfoot',
        'churchill': 'captainchurchill',
        'ben': 'benjamin',
        # 'ezili',
        'pat': 'patfusty',
        # 'adora',
        'brickell': 'admiralbrickell',
        'etn': 'etienne',
        # 'sauda',
        # 'psi',
        # 'geraldo',
        # 'corvus',
        # 'rosalia',

        # misc
        'start': 'startround',
        'end': 'endround',
        'cash': 'startcash',

        'timeattack': 'race',
        'lc': 'leastcash',
        'lt': 'leasttier',
        'leasttier': 'leasttiers',

        'bosstier': 'bosstiers',
        'reg': 'regular',
        'blank': 'regular',

        # disamb workaround
        'relic': 'relictype',
    }
    CONSTANTS = {
        'true': True,
        'false': False,
        'inf': 'inf',
    }

    def __init__(self, tile):
        self.tile = tile

    def __getitem__(self, name):
        name = name.lower().replace('_', '')

        name = self.ALIASES.get(name, name)

        if name == 'startcash':
            return self.tile['GameData']['dcModel']['startRules']['cash']
        if name == 'startround':
            return self.tile['GameData']['dcModel']['startRules']['round']
        if name == 'endround':
            end = self.tile['GameData']['dcModel']['startRules']['endRound']
            if end == -1:
                return math.inf
            return end
        if name == 'bosstiers':
            if 'bossData' not in self.tile['GameData']:
                return 0
            return self.tile['GameData']['bossData']['TierCount']

        if name == 'map':
            return Map.of(self.tile)
        if name == 'difficulty':
            return Difficulty.of(self.tile)
        if name == 'gametype':
            return GameType.of(self.tile)
        if name == 'boss':
            return Boss.of(self.tile)
        if name == 'tiletype':
            return TileType.of(self.tile)
        if name == 'relictype':
            return RelicType.of(self.tile)

        for cls in [
            TowerCategory,
            Tower,
            Hero,
            MapDifficulty,
            Map,
            Difficulty,
            GameType,
            Boss,
            TileType,
            RelicType,
        ]:
            for entry in cls.validlist():
                if name == entry.lower():
                    return cls(self.tile, entry)

        raise NameError(name)


def make_predicate(predicate_str):
    if not predicate_str.strip():
        return lambda _: False

    func = mapmaker_compile(predicate_str)

    def apply(tile):
        return func(Context(tile))

    return apply
