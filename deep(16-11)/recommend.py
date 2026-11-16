import pandas as pd

rec = pd.read_csv('product_recommendations.csv')
off = pd.read_csv('product_offers.csv').set_index('Product_ID')
names = rec.drop_duplicates('Product_ID').set_index('Product_ID')['Product']


def suggest(product_id):
    r = rec[(rec['Product_ID'] == product_id) & (rec['Confidence'] >= 0.2)]
    out = []
    for _, x in r.iterrows():
        out.append(f"{x['Suggested']}  ({x['Confidence']:.0%} من الفواتير اللي فيها {x['Product']} بيكون فيها كمان {x['Suggested']})")
    return out


def offer(product_id):
    o = off.loc[product_id]
    return f"المنتج ده اتباع بخصم في {o['Discount_Share']:.0%} من الحالات، ومتوسط الخصم {o['Avg_Discount']:.0%}"


def answer(product_id):
    sug = suggest(product_id)
    lines = [f"المنتج: {names[product_id]}", "", "ممكن تشتري معاه:"]
    lines += ['- ' + s for s in sug] if sug else ['- مفيش منتج بيتشرى معاه بشكل واضح']
    lines += ["", offer(product_id)]
    return '\n'.join(lines)
