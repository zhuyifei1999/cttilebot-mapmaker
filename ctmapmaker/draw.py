import json
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont
from aggdraw import Draw, Brush, Pen

from ctmapmaker.coords import TILECOORDS, MYRIN_CODEMAP
from ctmapmaker.predicate import make_predicate

ASSETS = os.path.join(os.path.dirname(__file__), 'assets')
HEXSIZE = 32


def HexagonGenerator(edge_length, offsetx=0, offsety=0):
    col_width = edge_length * 3
    row_height = math.sin(math.pi / 3) * edge_length

    def gen(row, col):
        vertices = []
        x = (col + 0.5 * (row % 2)) * col_width
        y = row * row_height
        for angle in range(0, 360, 60):
            x += math.cos(math.radians(angle)) * edge_length
            y += math.sin(math.radians(angle)) * edge_length
            vertices.append(x + offsetx)
            vertices.append(y + offsety)

        center = (
            x + edge_length / 2 + offsetx,
            y + math.sin(math.radians(60)) * edge_length + offsety
        )
        return center, vertices

    return gen


def tilecoord2gencoord(coord, pov):
    tilex, tiley = coord
    if pov == 0:
        return tiley, -tilex // 2
    elif pov == 1:
        return (
            (tilex * 3 + tiley) // 2,
            (-tilex + tiley) // 4
        )
    elif pov == 2:
        return (
            (tilex * 3 - tiley) // 2,
            (tilex + tiley) // 4
        )
    elif pov == 3:
        return -tiley, tilex // 2
    elif pov == 4:
        return (
            (-tilex * 3 - tiley) // 2,
            (tilex - tiley) // 4
        )
    elif pov == 5:
        return (
            (-tilex * 3 + tiley) // 2,
            (-tilex - tiley) // 4
        )


def tileicon(tiledata):
    if tiledata['TileType'] == 'Banner':
        return 'CTPointsBanner.webp'
    elif tiledata['TileType'] == 'Relic':
        return tiledata['RelicType'] + '.png'
    return None


def loadtiles(season):
    tilespath = f'/ctmap/{season}/tiles'
    tiles = {}

    for filename in os.listdir(tilespath):
        if filename.endswith('.json'):
            tilecode = filename[:-len('.json')]
            tilecode = MYRIN_CODEMAP.get(tilecode, tilecode)
            with open(os.path.join(tilespath, filename)) as f:
                tiles[tilecode] = json.load(f)

    return tiles


def render(season, predicate_str, teamid):
    tiles = loadtiles(season)
    predicate = make_predicate(predicate_str)

    # TODO: support mapsize 8 in CT 24
    if 'AAA' in tiles:
        mapsize, outercode = 8, 'Z'
    elif 'AAB' in tiles:
        mapsize, outercode = 7, 'A'
    else:
        mapsize, outercode = 6, 'B'

    teamstarts = {
        f'AA{outercode}': (160, 95, 240),
        f'BA{outercode}': (236, 138, 184),
        f'CA{outercode}': (89, 190, 114),
        f'DA{outercode}': (78, 173, 234),
        f'EA{outercode}': (242, 204, 69),
        f'FA{outercode}': (229, 80, 73),
    }

    imagew = 20 + (3 * mapsize + 2) * HEXSIZE
    imageh = 18 + (4 * mapsize + 2) * HEXSIZE * math.sin(math.pi / 3)
    offx = imagew/2 - HEXSIZE/2
    offy = imageh/2 - HEXSIZE * math.sin(math.pi / 3)
    image = Image.new('RGBA', (int(imagew), int(imageh)), 'black')
    draw = Draw(image)
    hexagon_generator = HexagonGenerator(HEXSIZE, offx, offy)
    icons = []
    labels = []

    def paste_icon(icon, center, size=36):
        icon = Image.open(os.path.join(ASSETS, icon))
        iconw, iconh = icon.size
        if iconw >= iconh:
            iconh = iconh * size / iconw
            iconw = size
        else:
            iconw = iconw * size / iconh
            iconh = size

        centerx, centery = center
        icon = icon.resize((int(iconw), int(iconh)))
        icons.append(((int(centerx-iconw/2), int(centery-iconh/2)), icon))

    def bordered(vertices, center, size):
        result = []
        for i in range(0, len(vertices), 2):
            vx, vy = vertices[i], vertices[i+1]
            cx, cy = center
            d = math.sqrt((vx - cx) ** 2 + (vy - cy) ** 2)
            result.append(vx + size/d * (cx - vx))
            result.append(vy + size/d * (cy - vy))
        return result

    for tilecode, fillcolor in teamstarts.items():
        row, col = tilecoord2gencoord(TILECOORDS[tilecode], teamid)
        center, vertices = hexagon_generator(row, col)
        draw.polygon(vertices, Pen('white', 2), Brush(fillcolor))

    num_selected = 0
    for tilecode, tiledata in tiles.items():
        row, col = tilecoord2gencoord(TILECOORDS[tilecode], teamid)

        selected = predicate(tiledata)
        fillcolor = 'grey' if selected else 'black'
        icon = tileicon(tiledata)

        center, vertices = hexagon_generator(row, col)
        draw.polygon(vertices, Pen('white', 2), Brush(fillcolor))

        if icon:
            paste_icon(icon, center)
        if selected:
            labels.append((center, tilecode))
            num_selected += 1

    draw.flush()

    for offset, icon in icons:
        padded_icon = Image.new('RGBA', image.size, (0, 0, 0, 0))
        padded_icon.paste(icon, offset)
        image = Image.alpha_composite(image, padded_icon)

    if labels:
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(
            os.path.join(ASSETS, 'LuckiestGuy-Regular.ttf'), 14)

        for center, label in labels:
            cx, cy = center
            cy += 14
            draw.text((cx+1, cy+1), label, fill='black', anchor='mm', font=font)
            draw.text((cx+1, cy-1), label, fill='black', anchor='mm', font=font)
            draw.text((cx-1, cy+1), label, fill='black', anchor='mm', font=font)
            draw.text((cx-1, cy-1), label, fill='black', anchor='mm', font=font)
            draw.text((cx, cy), label, fill='white', anchor='mm', font=font)

    if num_selected:
        cx, cy = 15, imageh - 15
        label = str(num_selected)
        font = ImageFont.truetype(
            os.path.join(ASSETS, 'LuckiestGuy-Regular.ttf'), 28)
        draw.text((cx+1, cy+1), label, fill='black', anchor='lb', font=font)
        draw.text((cx+1, cy-1), label, fill='black', anchor='lb', font=font)
        draw.text((cx-1, cy+1), label, fill='black', anchor='lb', font=font)
        draw.text((cx-1, cy-1), label, fill='black', anchor='lb', font=font)
        draw.text((cx, cy), label, fill='white', anchor='lb', font=font)

    return image.convert('RGB')


def main():
    season = int(sys.argv[1])
    predicate_str = sys.argv[2]
    teamid = int(sys.argv[3])
    output = sys.argv[4]

    image = render(season, predicate_str, teamid)
    image.save(output)


if __name__ == '__main__':
    main()
