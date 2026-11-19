"""Step A2: builds the item icons and crop growth sheets from Cozy Lands (tools) and
Farm & Ranch Life (pack 6), recoloring where the pack has no exact match.
Run from the repo root:  python3 tools/convert_pack6_items.py <FarmRanchLife folder> <Cozy Lands pack folder>
Needs: pip install pillow

Writes public/assets/items/*.png (16x16) and public/assets/crops/{carrot,corn,chili,tomato}.png
(one frame per growth stage = growth days + 1; corn uses 16x32 frames, bottom 16 px = soil tile).
Stand-ins (recolored): carrot = parsnip, tomato = bell pepper, chili = cranberry bush + cucumber recolored red (icon),
corn = okra (golden pods).
"""
import colorsys
import os
import sys
from PIL import Image

P6 = sys.argv[1] if len(sys.argv) > 1 else 'FarmRanchLife'
CL = sys.argv[2] if len(sys.argv) > 2 else 'Cozy Lands - Asset Pack - Basic pack'
ITEMS_OUT = os.path.join('public', 'assets', 'items')
CROPS_OUT = os.path.join('public', 'assets', 'crops')
os.makedirs(ITEMS_OUT, exist_ok=True)
os.makedirs(CROPS_OUT, exist_ok=True)


def load(p):
    return Image.open(p).convert('RGBA')


def recolor(im, fn, region=None):
    """fn(h, s, v) -> (h, s, v) or None (keep). Hue 0-360, s/v 0-1."""
    im = im.copy()
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            if region and not (region[0] <= x % 16 < region[2] and region[1] <= y % 16 < region[3]):
                continue
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            out = fn(h * 360, s, v)
            if out is None:
                continue
            h2, s2, v2 = out
            r2, g2, b2 = colorsys.hsv_to_rgb((h2 % 360) / 360, max(0, min(1, s2)), max(0, min(1, v2)))
            px[x, y] = (round(r2 * 255), round(g2 * 255), round(b2 * 255), a)
    return im


# cream / pale yellow (parsnip root, cream packet pictograph) -> carrot orange
def to_orange(h, s, v):
    if 25 <= h <= 75 and s < 0.6 and v > 0.55:
        return (26, 0.78, min(1.0, v * 0.97))
    return None


# any non-dark leaf/pod green -> chili red
def green_to_red(h, s, v):
    if 70 <= h <= 175 and v > 0.3:
        return (4, min(1.0, s * 1.05 + 0.15), min(1.0, v * 1.45 + 0.12))
    return None


# dark berry red -> brighter chili red
def berry_to_chili(h, s, v):
    if (h <= 22 or h >= 335) and s > 0.25 and v > 0.2:
        return (4, min(1.0, s + 0.1), min(1.0, v * 1.35 + 0.08))
    return None


# okra pods: light green / yellow-green -> corn gold
def pods_to_gold(h, s, v):
    if 55 <= h <= 110 and v > 0.58:
        return (46, 0.85, min(1.0, v * 1.05))
    return None


# whole pod icon -> corn gold
def all_green_to_gold(h, s, v):
    if 60 <= h <= 175 and v > 0.3:
        return (46, min(1.0, s * 0.9 + 0.1), min(1.0, v * 1.08))
    return None


def find(root, name):
    for r, _, fs in os.walk(root):
        if name in fs:
            return os.path.join(r, name)
    raise FileNotFoundError(name)


def save_icon(im, name):
    assert im.size == (16, 16), (name, im.size)
    im.save(os.path.join(ITEMS_OUT, name + '.png'))


def p6(sub, name):
    return load(os.path.join(P6, '08_Items', sub, name + '.png'))


# ---------------- tools (Cozy Lands) ----------------
tool = lambda n: load(find(os.path.join(CL, 'Items', 'Tool'), n + '.png'))
save_icon(tool('hoe'), 'hoe')
save_icon(tool('kettle'), 'watering_can')
save_icon(tool('axe'), 'axe')
save_icon(tool('pickaxe'), 'pickaxe')
save_icon(tool('fishing_rod'), 'fishing_rod')

# ---------------- produce + seeds ----------------
PICT = (4, 5, 12, 13)   # the little picture inside a seed packet
save_icon(recolor(p6('crops', 'parsnip'), to_orange), 'carrot')
save_icon(p6('crops', 'bell_pepper'), 'tomato')
save_icon(recolor(p6('crops', 'cucumber'), green_to_red), 'chili')
save_icon(recolor(p6('crops', 'okra'), all_green_to_gold), 'corn')
save_icon(recolor(p6('seeds', 'seeds_parsnip'), to_orange, PICT), 'carrot_seeds')
save_icon(p6('seeds', 'seeds_bell_pepper'), 'tomato_seeds')
save_icon(recolor(p6('seeds', 'seeds_cranberry'), berry_to_chili, PICT), 'chili_seeds')
save_icon(recolor(p6('seeds', 'seeds_okra'), all_green_to_gold, PICT), 'corn_seeds')

# ---------------- everything else ----------------
save_icon(load(find(os.path.join(P6, '05_Buildings_Machines', 'Ranch_Props'), 'sack_chicken_feed.png')), 'animal_feed')
save_icon(p6('animal_products', 'egg_small_white'), 'egg')
save_icon(p6('animal_products', 'milk_bottle'), 'milk')
for game_id, pack_name in [('fish_sardine', 'herring'), ('fish_mackerel', 'mackerel'), ('fish_bass', 'bream'),
                           ('fish_catfish', 'bullhead'), ('fish_snapper', 'sunset_koi'), ('fish_golden_carp', 'carp')]:
    save_icon(p6('fish', pack_name), game_id)
save_icon(load(find(os.path.join(CL, 'Items', 'Products'), 'stone.png')), 'stone')
save_icon(p6('materials', 'copper_ore'), 'copper_ore')
save_icon(p6('materials', 'gold_ore'), 'gold_ore')

# ---------------- crop growth sheets ----------------
def strip(season, name):
    return load(os.path.join(P6, '02_Crops', season, name + '_stages_8f.png'))


def stage_sheet(src, days, out_name, fn=None):
    """Pack strip: frames 0 seeds .. 6 READY (7 withered). Game stages 0..days -> evenly spread."""
    fh = src.height
    sheet = Image.new('RGBA', (16 * (days + 1), fh), (0, 0, 0, 0))
    for s in range(days + 1):
        f = int(s * 6 / days + 0.5)
        frame = src.crop((f * 16, 0, f * 16 + 16, fh))
        if fn:
            frame = recolor(frame, fn)
        sheet.alpha_composite(frame, (s * 16, 0))
    sheet.save(os.path.join(CROPS_OUT, out_name + '.png'))


stage_sheet(strip('spring', 'parsnip'), 3, 'carrot', to_orange)                  # carrot: 3 days
stage_sheet(strip('summer', 'okra'), 4, 'corn', pods_to_gold)                    # corn: 4 days (16x32 frames)
stage_sheet(strip('autumn', 'cranberry'), 3, 'chili', berry_to_chili)            # chili: 3 days
stage_sheet(strip('summer', 'bell_pepper'), 4, 'tomato')                         # tomato: 4 days
print('done')
