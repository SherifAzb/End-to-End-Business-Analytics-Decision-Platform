import io
import os
from html import escape
import streamlit as st
from PIL import Image
from google import genai
from google.genai import types
from matcher import ask_gemini, decide
from recommend import names, suggestions, bundles, top_sellers, categories, products_in, info, image, emoji, hook, category_view

st.set_page_config(page_title="RetailDeep", page_icon="🛒", layout="centered")

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
.rd{direction:rtl;text-align:right;font-family:'Cairo','Segoe UI',Tahoma,sans-serif;line-height:1.7}
.rd bdi{unicode-bidi:isolate}
.rd .ttl{text-align:center;font-size:1.9rem;font-weight:700;margin:4px 0 14px}
.rd .hero{border:1px solid rgba(128,128,128,.3);border-radius:16px;padding:18px 22px;background:linear-gradient(135deg,rgba(46,160,67,.22),rgba(46,160,67,.05));margin:14px 0}
.rd .hero .lb{font-size:.85rem;opacity:.7}
.rd .hero .nm{font-size:1.9rem;font-weight:700}
.rd .sec{font-size:1.2rem;font-weight:700;margin:26px 0 10px}
.rd .row{display:flex;align-items:center;gap:14px;padding:10px 16px;border:1px solid rgba(128,128,128,.25);border-radius:12px;margin-bottom:8px}
.rd .row .nm{flex:0 0 38%;font-weight:600}
.rd .bar{flex:1;height:8px;border-radius:99px;background:rgba(128,128,128,.25);overflow:hidden}
.rd .bar i{display:block;height:100%;background:#2ea043;border-radius:99px}
.rd .pct{flex:0 0 48px;text-align:left;font-weight:700}
.rd .card{border:1px solid rgba(128,128,128,.25);border-radius:14px;padding:16px 18px;margin-bottom:10px}
.rd .chips{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.rd .chip{padding:5px 14px;border-radius:99px;background:rgba(128,128,128,.2);font-weight:600}
.rd .plus{opacity:.55;font-weight:700}
.rd .price{display:flex;flex-wrap:wrap;align-items:baseline;gap:14px;margin-top:14px}
.rd .old{text-decoration:line-through;opacity:.6}
.rd .new{font-size:1.6rem;font-weight:700;color:#2ea043}
.rd .save{background:rgba(46,160,67,.2);color:#2ea043;padding:2px 12px;border-radius:99px;font-weight:700;font-size:.85rem}
.rd .note{opacity:.7;font-size:.85rem;margin-top:8px}
.rd .msg{border-radius:12px;padding:14px 18px;margin:14px 0;border:1px solid rgba(128,128,128,.3);background:rgba(128,128,128,.12)}
.rd .msg.warn{border-color:rgba(240,165,0,.5);background:rgba(240,165,0,.12)}
.rd .hook{border:2px dashed #f0a500;border-radius:16px;padding:16px 20px;margin:8px 0;background:linear-gradient(135deg,rgba(240,165,0,.18),rgba(240,165,0,.04))}
.rd .hook .hd{font-size:1.25rem;font-weight:700}
.rd .hook .sb{opacity:.8;margin-top:2px}
.rd .hook .you{display:inline-block;background:#f0a500;color:#000;padding:1px 12px;border-radius:99px;font-weight:700;font-size:.85rem;margin-bottom:6px}
div[data-testid="stWidgetLabel"] p{text-align:right;width:100%;direction:rtl}
.rd .msg.err{border-color:rgba(230,60,60,.5);background:rgba(230,60,60,.12)}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def html(body):
    st.markdown('<div class="rd">' + body + '</div>', unsafe_allow_html=True)


def ltr(text):
    return f'<bdi dir="ltr">{escape(str(text))}</bdi>'


def pct(x):
    return ltr(f'{x:.0%}')


def money(x):
    return f'{ltr(f"{x:,.0f}")} ج'


def notice(text, kind=''):
    html(f'<div class="msg {kind}">{text}</div>')


html('<div class="ttl">🛒 RetailDeep Assistant</div>')

key = os.environ.get('GEMINI_API_KEY', '')
if not key:
    try:
        key = st.secrets['GEMINI_API_KEY']
    except Exception:
        key = ''
if not key and os.path.exists('gemini_key.txt'):
    key = open('gemini_key.txt', encoding='utf-8-sig').read().strip()
if not key:
    notice('حط الـ API key في Secrets أو متغير GEMINI_API_KEY أو ملف gemini_key.txt', 'err')
    st.stop()


@st.cache_resource
def get_client(k):
    return genai.Client(api_key=k, http_options=types.HttpOptions(timeout=20000))


client = get_client(key)


@st.cache_data(ttl=3600, show_spinner=False)
def identify(data):
    return ask_gemini(client, Image.open(io.BytesIO(data)).convert('RGB'))

def show_product(pid):
    meta = info(pid)
    img = image(pid)
    if img:
        _, mid, _ = st.columns([1, 2, 1])
        mid.image(img, use_container_width=True)
    else:
        html(f'<div style="text-align:center;font-size:7rem;line-height:1.2;margin:8px 0">{emoji(pid)}</div>')
    html(f'<div class="hero"><div class="lb">{ltr(meta["category"])} · السعر {money(meta["price"])}</div><div class="nm">{ltr(names[pid])}</div></div>')

    html('<div class="sec">🛍️ غالباً بيشتروا معاه</div>')
    sug = suggestions(pid)
    if sug:
        rows = ''.join(f'<div class="row"><div class="nm">{ltr(s["name"])}</div><div class="bar"><i style="width:{s["share"]*100:.0f}%"></i></div><div class="pct">{pct(s["share"])}</div></div>' for s in sug)
        html(rows + f'<div class="note">النسبة من الفواتير اللي فيها {ltr(names[pid])} وكمان المنتج ده</div>')
    else:
        chips = '<span class="plus">·</span>'.join(f'<span class="chip">{ltr(n)}</span>' for n in top_sellers)
        html('<div class="msg">مفيش منتج بيتشرى معاه بشكل واضح</div>' + f'<div class="note">الأكتر طلباً عندنا:</div><div class="chips">{chips}</div>')

    html('<div class="sec">🎁 الباقات المقترحة</div>')
    bnd = bundles(pid)
    if bnd:
        for b in bnd:
            chips = '<span class="plus">+</span>'.join(f'<span class="chip">{ltr(n)}</span>' for n in b['items'])
            saved = b['regular'] - b['offer']
            html(
                f'<div class="card"><div class="chips">{chips}</div>'
                f'<div class="price"><span class="old">{money(b["regular"])}</span><span class="new">{money(b["offer"])}</span>'
                f'<span class="save">وفّر {money(saved)} ({pct(b["discount"])})</span></div>'
                f'<div class="note">بيتشتروا مع بعض في {pct(b["share"])} من فواتير {ltr(names[pid])}</div></div>'
            )
        html('<div class="note">السعر بعد الخصم تقدير مبني على متوسط الخصم اللي اتعمل فعلاً على المنتجات دي</div>')
    else:
        h = hook(pid)
        if h:
            html(
                '<div class="hook"><span class="you">🎯 خاص بيك إنت</span>'
                f'<div class="hd">اختار منتج واحد من دول وخده بخصم مع {ltr(names[pid])}</div>'
                '<div class="sb">العرض شغال طول ما المنتجين في نفس الطلب</div></div>'
            )
            ids = [x['id'] for x in h]
            by_id = {x['id']: x for x in h}
            pick = st.radio('اختار منتجك', ids, horizontal=True, key=f'hook_{pid}', label_visibility='collapsed',
                            format_func=lambda i: f"{by_id[i]['name']}  ·  {by_id[i]['price']:,.0f} ← {by_id[i]['offer']:,.0f} ج")
            x = by_id[pick]
            base = info(pid)['price']
            saved = x['price'] - x['offer']
            html(
                f'<div class="card"><div class="chips"><span class="chip">{ltr(names[pid])}</span><span class="plus">+</span><span class="chip">{ltr(x["name"])}</span></div>'
                f'<div class="price"><span class="old">{money(base + x["price"])}</span><span class="new">{money(base + x["offer"])}</span>'
                f'<span class="save">وفّر {money(saved)} ({pct(x["discount"])})</span></div>'
                f'<div class="note">الخصم على {ltr(x["name"])} لما تاخده مع {ltr(names[pid])}</div></div>'
            )
        else:
            html('<div class="msg">مفيش باقة واضحة للمنتج ده</div>')

    cv = category_view(pid)
    html('<div class="sec">📊 المنتج ده في فئته</div>')
    rows = ''.join(f'<div class="row"><div class="nm">{ltr(x["name"])}</div><div class="pct" style="flex:0 0 auto">{money(x["price"])}</div></div>' for x in cv['alts'])
    html(
        f'<div class="card">رقم <b>{ltr(cv["rank"])}</b> في الأكتر طلباً من {ltr(cv["total"])} منتج في {ltr(cv["category"])}</div>'
        '<div class="note" style="margin:6px 0">بدائل في نفس الفئة:</div>' + rows
    )


MODES = ['🛒 اختار من القايمة', '📷 كاميرا', '📁 رفع صورة']
mode = st.radio('طريقة الاختيار', MODES, horizontal=True, label_visibility='collapsed')


def recognize(img_file):
    image = Image.open(img_file).convert('RGB')
    with st.spinner("جاري التعرف على المنتج..."):
        try:
            r = identify(img_file.getvalue())
        except Exception as e:
            notice(f'حصلت مشكلة في الاتصال، جرّب تاني بعد شوية.<br><small>{ltr(e)}</small>', 'err')
            st.stop()
    status, shown, pid = decide(image, r)
    st.image(shown, use_container_width=True)
    if status == 'none':
        notice('مفيش منتج في الصورة', 'warn')
    elif status == 'nomatch':
        notice('المنتج ده مش موجود عندنا', 'warn')
    elif status == 'unsure':
        notice('الصورة مش واضحة، جرّب تصوّر المنتج من قرب وإضاءة أحسن', 'warn')
    else:
        show_product(pid)


if mode == MODES[0]:
    cat = st.selectbox('الفئة', ['كل الفئات'] + categories())
    pids = products_in(None if cat == 'كل الفئات' else cat)
    pid = st.selectbox('اختار المنتج (تقدر تكتب للبحث)', pids, index=None, format_func=lambda p: names[p], placeholder='اكتب اسم المنتج أو اختاره')
    if pid:
        show_product(pid)
elif mode == MODES[1]:
    img_file = st.camera_input("صوّر المنتج")
    if img_file is not None:
        recognize(img_file)
else:
    img_file = st.file_uploader("ارفع صورة المنتج", type=["jpg", "jpeg", "png", "webp"])
    if img_file is not None:
        recognize(img_file)
