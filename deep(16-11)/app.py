import os
from typing import List
import streamlit as st
from PIL import Image, ImageDraw
from pydantic import BaseModel
from google import genai
from google.genai import types
from recommend import answer, names

st.set_page_config(page_title="RetailDeep", layout="centered")
st.title("🛒 RetailDeep Assistant")

MODEL = 'gemini-3.5-flash'
MIN_CONFIDENCE = 0.6
ALIASES = {'P035': 'P034'}

key = os.environ.get('GEMINI_API_KEY', '')
if not key and 'GEMINI_API_KEY' in st.secrets:
    key = st.secrets['GEMINI_API_KEY']
if not key:
    st.error('حط الـ API key في إعدادات Secrets باسم GEMINI_API_KEY')
    st.stop()

client = genai.Client(api_key=key)

catalog = '\n'.join(f'{pid}: {n}' for pid, n in names.drop(list(ALIASES)).items())

PROMPT = f'''You are the product recognizer of a supermarket assistant.

Catalog (ID: name):
{catalog}

Find the ONE main retail product the person is showing to the camera.
Rules:
- If there is no packaged retail product in the image, set found=false.
- If a product is there but its type is not in the catalog, set found=true and product_id="UNKNOWN".
- Otherwise product_id must be copied exactly from the catalog: the closest match by product type and size. Use the brand and the Arabic or English text on the pack. "Pasta 400g" covers every pasta shape (spaghetti, macaroni, penne).
- Never guess. If the image is blurry or you are not sure, lower the confidence.
- box_2d is [ymin, xmin, ymax, xmax] normalized to 0-1000, around the product only.
- seen is 3 to 6 words describing what you see.
'''


class Result(BaseModel):
    found: bool
    product_id: str
    confidence: float
    box_2d: List[int]
    seen: str


def ask_gemini(image):
    small = image.copy()
    small.thumbnail((1024, 1024))
    resp = client.models.generate_content(
        model=MODEL,
        contents=[small, PROMPT],
        config=types.GenerateContentConfig(
            response_mime_type='application/json',
            response_schema=Result,
            temperature=0,
        ),
    )
    return Result.model_validate_json(resp.text)


def to_pixels(box, size):
    if len(box) != 4:
        return None
    w, h = size
    ymin, xmin, ymax, xmax = box
    x1, x2 = sorted((max(0, xmin) / 1000 * w, min(1000, xmax) / 1000 * w))
    y1, y2 = sorted((max(0, ymin) / 1000 * h, min(1000, ymax) / 1000 * h))
    if x2 - x1 < 5 or y2 - y1 < 5:
        return None
    return x1, y1, x2, y2


def draw(image, box, color):
    shown = image.copy()
    if box:
        ImageDraw.Draw(shown).rectangle(box, outline=color, width=5)
    return shown


tab1, tab2 = st.tabs(["📷 الكاميرا", "📁 رفع صورة"])
with tab1:
    cam_img = st.camera_input("صور المنتج")
with tab2:
    up_img = st.file_uploader("ارفع صورة المنتج", type=["jpg", "jpeg", "png", "webp"])

img_file = cam_img if cam_img is not None else up_img

if img_file is not None:
    image = Image.open(img_file).convert('RGB')
    with st.spinner("جاري التعرف على المنتج..."):
        try:
            r = ask_gemini(image)
        except Exception as e:
            st.error(f"مشكلة في الاتصال بـ Gemini: {e}")
            st.stop()

    if not r.found:
        st.image(image, caption="المنتج")
        st.warning("مفيش منتج في الصورة")
    else:
        box = to_pixels(r.box_2d, image.size)
        pid = ALIASES.get(r.product_id, r.product_id)
        if pid not in names.index or r.confidence < MIN_CONFIDENCE:
            st.image(draw(image, box, 'red'), caption="المنتج")
            st.error(f"منتج مش معروف (Gemini شايف: {r.seen})")
        else:
            st.image(draw(image, box, 'lime'), caption="المنتج")
            st.success(f"{names[pid]}  ←  Gemini شايف: {r.seen}  ({r.confidence:.0%})")
            st.info(answer(pid))
