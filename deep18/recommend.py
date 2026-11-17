import os
import re
from collections import defaultdict
import pandas as pd
from related import GROUPS

rec = pd.read_csv('product_recommendations.csv')
off = pd.read_csv('product_offers.csv').set_index('Product_ID')
bun = pd.read_csv('product_bundles.csv', encoding='utf-8-sig')
catalog = pd.read_csv('products_catalog.csv', encoding='utf-8-sig').set_index('Product_ID')
HIDDEN = ['P035']
names = rec.drop_duplicates('Product_ID').set_index('Product_ID')['Product']
top_sellers = off.sort_values('Lines', ascending=False).head(3)['Product'].tolist()


def suggestions(product_id):
    r = rec[(rec['Product_ID'] == product_id) & (rec['Confidence'] >= 0.2)].sort_values('Confidence', ascending=False)
    return [{'name': x['Suggested'], 'share': float(x['Confidence'])} for _, x in r.iterrows()]


def bundles(product_id):
    out = []
    for _, b in bun[bun['Product_ID'] == product_id].iterrows():
        out.append({
            'items': b['Bundle'].split(' + '),
            'share': float(b['Share_of_Product_Invoices']),
            'regular': float(b['Regular_Price']),
            'offer': float(b['Offer_Price']),
            'discount': float(b['Suggested_Discount']),
        })
    return out



def categories():
    return sorted(catalog.drop(HIDDEN, errors='ignore')['Category'].unique())


def products_in(category=None):
    c = catalog.drop(HIDDEN, errors='ignore')
    if category:
        c = c[c['Category'] == category]
    return c.sort_values('Product').index.tolist()


def info(product_id):
    c = catalog.loc[product_id]
    return {'category': c['Category'], 'price': float(c['Price'])}


IMG_DIR = 'images'
EXTS = ('.jpg', '.jpeg', '.png', '.webp')


def image(product_id):
    """Local file images/<Product_ID>.<ext> first, then optional Image_URL column in the catalogue, else None."""
    for e in EXTS:
        p = os.path.join(IMG_DIR, product_id + e)
        if os.path.exists(p):
            return p
    if 'Image_URL' in catalog.columns:
        u = catalog.loc[product_id, 'Image_URL']
        if isinstance(u, str) and u.startswith('http'):
            return u
    return None


CAT_EMOJI = {'Baby & Kids': '👶', 'Bakery': '🥐', 'Beverages': '🥤', 'Dairy': '🥛', 'Eggs & Poultry': '🍗', 'Frozen': '🧊',
             'Fruits & Vegetables': '🥬', 'Grains & Pasta': '🌾', 'Household': '🧴', 'Oils & Sauces': '🫙',
             'Personal Care': '🧼', 'Snacks': '🍿', 'Sugar & Spices': '🧂'}
# first match wins, so keep the specific words before the general ones
KW_EMOJI = [
    ('formula', '🍼'), ('diaper', '👶'), ('wipes', '🧻'), ('baby snack', '🍪'),
    ('croissant', '🥐'), ('pita', '🫓'), ('baladi', '🫓'), ('bread', '🍞'), ('buns', '🍔'), ('cake', '🍰'), ('biscuit', '🍪'), ('rusk', '🍞'), ('pastry', '🥮'),
    ('apple juice', '🧃'), ('orange juice', '🧃'), ('instant coffee', '☕'), ('coffee', '☕'), ('energy', '⚡'), ('hibiscus', '🥤'), ('malt', '🥤'),
    ('soda', '🥤'), ('tea', '🍵'), ('water', '💧'),
    ('butter', '🧈'), ('cheddar', '🧀'), ('cheese', '🧀'), ('mozzarella', '🧀'), ('cream', '🥛'), ('ghee', '🧈'), ('yogurt', '🥣'), ('labneh', '🥣'), ('milk', '🥛'),
    ('nuggets', '🍗'), ('burger', '🍔'), ('sausage', '🌭'), ('chicken', '🍗'), ('eggs', '🥚'), ('beef', '🥩'), ('turkey', '🦃'),
    ('fries', '🍟'), ('okra', '🥬'), ('peas', '🫛'), ('pizza', '🍕'), ('spinach', '🥬'), ('ice cream', '🍨'),
    ('apples', '🍎'), ('bananas', '🍌'), ('carrots', '🥕'), ('cucumber', '🥒'), ('garlic', '🧄'), ('grapes', '🍇'), ('lemons', '🍋'), ('lettuce', '🥬'),
    ('onions', '🧅'), ('oranges', '🍊'), ('peppers', '🫑'), ('potatoes', '🥔'), ('strawberr', '🍓'), ('tomatoes', '🍅'),
    ('rice', '🍚'), ('bulgur', '🌾'), ('chickpeas', '🫘'), ('cornflakes', '🥣'), ('couscous', '🍚'), ('fava', '🫘'), ('flour', '🌾'), ('lentils', '🫘'),
    ('oats', '🥣'), ('pasta', '🍝'), ('spaghetti', '🍝'),
    ('air freshener', '🌸'), ('foil', '📦'), ('bleach', '🧴'), ('dish soap', '🧽'), ('softener', '🧴'), ('floor', '🧹'), ('laundry', '🧺'), ('paper towels', '🧻'),
    ('sponges', '🧽'), ('tissues', '🤧'), ('trash', '🗑️'),
    ('olive oil', '🫒'), ('oil', '🛢️'), ('hot sauce', '🌶️'), ('ketchup', '🍅'), ('mayonnaise', '🥚'), ('mustard', '🟡'), ('pickles', '🥒'), ('tahini', '🫙'),
    ('tomato', '🍅'), ('vinegar', '🍶'),
    ('body soap', '🧼'), ('deodorant', '🧴'), ('face wash', '🧴'), ('conditioner', '🧴'), ('hand wash', '🧼'), ('razor', '🪒'), ('pads', '🩹'), ('shampoo', '🧴'),
    ('toothbrush', '🪥'), ('toothpaste', '🪥'),
    ('candy', '🍬'), ('chips', '🥔'), ('chocolate', '🍫'), ('cookies', '🍪'), ('dates', '🌴'), ('nuts', '🥜'), ('popcorn', '🍿'), ('pretzels', '🥨'), ('wafer', '🍫'),
    ('pepper', '🌶️'), ('cinnamon', '🟤'), ('cocoa', '🍫'), ('cumin', '🌿'), ('honey', '🍯'), ('jam', '🍓'), ('salt', '🧂'), ('spice', '🌶️'), ('sugar', '🍬'), ('vanilla', '🌼'),
]


def emoji(product_id):
    name = catalog.loc[product_id, 'Product'].lower()
    for k, e in KW_EMOJI:
        if k in name:
            return e
    return CAT_EMOJI.get(catalog.loc[product_id, 'Category'], '🛒')


HOOK_DISCOUNT = 0.10
HOOK_PICKS = 3
_STOP = {'pack', 'pc', 'pk', 'jar', 'can', 'box', 'bag', 'tub', 'bags', 'the', 'and'}
_rel = defaultdict(lambda: defaultdict(int))
for _g in GROUPS:
    for _a in _g:
        for _b in _g:
            if _a != _b:
                _rel[_a][_b] += 1


def _tokens(name):
    return {w for w in re.findall(r'[a-z]+', name.lower()) if w not in _STOP and len(w) > 2}


def hook(product_id):
    me = catalog.loc[product_id]
    my_tokens = _tokens(me['Product'])
    top = float(off['Lines'].max())
    scored = []
    for pid, shared in _rel[product_id].items():
        if pid in HIDDEN or pid not in catalog.index:
            continue
        c = catalog.loc[pid]
        if my_tokens & _tokens(c['Product']):
            continue
        score = shared * 3 + float(off.loc[pid, 'Lines']) / top * 2
        scored.append((score, float(c['Price']), pid))
    scored.sort(reverse=True)
    out = []
    for _, price, pid in scored[:HOOK_PICKS]:
        out.append({
            'id': pid,
            'name': catalog.loc[pid, 'Product'],
            'price': price,
            'offer': round(price * (1 - HOOK_DISCOUNT), 2),
            'discount': HOOK_DISCOUNT,
        })
    return out


def category_view(product_id):
    cat = catalog.loc[product_id, 'Category']
    ids = [p for p in catalog[catalog['Category'] == cat].index if p not in HIDDEN]
    ranked = sorted(ids, key=lambda p: -float(off.loc[p, 'Lines']))
    rank = ranked.index(product_id) + 1
    alts = [{'name': catalog.loc[p, 'Product'], 'price': float(catalog.loc[p, 'Price'])} for p in ranked if p != product_id][:3]
    return {'category': cat, 'rank': rank, 'total': len(ranked), 'alts': alts}
