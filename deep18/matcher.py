from typing import List
from PIL import ImageDraw
from pydantic import BaseModel
from google.genai import types
from recommend import names

MODELS = ['gemini-3.1-flash-lite', 'gemini-3.5-flash']
MIN_CONFIDENCE = 0.5
ALIASES = {'P035': 'P034'}

catalog = '\n'.join(f'{pid}: {n}' for pid, n in names.drop(list(ALIASES)).items())

PROMPT = f'''You are the product matcher of a supermarket assistant.

Catalog (ID: name):
{catalog}

Find the ONE main retail product the person is showing to the camera.
Rules:
- If there is no packaged retail product in the image, set found=false.
- Otherwise set product_id to the catalog item that is the NEAREST to the product: same kind of product first, then closest size and variant. Copy the ID exactly from the catalog. Use the brand and the Arabic or English text on the pack to decide. "Pasta 400g" covers every pasta shape (spaghetti, macaroni, penne). Chips are matched to "Chips Small" or "Chips Large" by pack size.
- Set match to "exact" if the catalog item is the same product type and size, "similar" if it is the same kind of product but a different brand, size or variant, and "none" if no catalog item is the same kind of product (then product_id must be "NONE").
- confidence is how sure you are about the whole answer (0 to 1). Lower it when the image is blurry.
- box_2d is [ymin, xmin, ymax, xmax] normalized to 0-1000, around the product only.
'''


class Result(BaseModel):
    found: bool
    product_id: str
    match: str
    confidence: float
    box_2d: List[int]


def call_model(client, model, image):
    resp = client.models.generate_content(
        model=model,
        contents=[image, PROMPT],
        config=types.GenerateContentConfig(response_mime_type='application/json', response_schema=Result, temperature=0),
    )
    return Result.model_validate_json(resp.text)


def ask_gemini(client, image):
    small = image.copy()
    small.thumbnail((768, 768))
    last = None
    for model in MODELS:
        try:
            return call_model(client, model, small)
        except Exception as e:
            last = e
    raise last


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


def decide(image, r):
    if not r.found:
        return 'none', image, None
    box = to_pixels(r.box_2d, image.size)
    pid = ALIASES.get(r.product_id, r.product_id)
    if pid not in names.index or r.match == 'none':
        return 'nomatch', draw(image, box, 'red'), None
    if r.confidence < MIN_CONFIDENCE:
        return 'unsure', draw(image, box, 'orange'), None
    return r.match, draw(image, box, 'lime'), pid
