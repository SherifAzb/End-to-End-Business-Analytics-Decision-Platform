# RetailDeep v2 (Streamlit + Gemini)

Three ways to pick a product, one result page (suggestions, bundles, offers):
1. Pick from the catalogue (category filter + searchable list). No API call, no quota.
2. Camera: Gemini finds the nearest catalogue product and draws a box.
3. Upload a photo: same as camera.

Run locally:
    pip install -r requirements.txt
    put your key in gemini_key.txt (or GEMINI_API_KEY env var / Streamlit Secrets)
    streamlit run app.py

Files
- app.py: UI (3 modes, RTL, cards)
- matcher.py: Gemini call (flash-lite first, flash as fallback), nearest-product decision
- recommend.py: suggestions, bundles, offers, catalogue helpers
- products_catalog.csv: product, category, brand, latest price (build_catalog.py)
- product_bundles.csv: bundles (build_bundles.py)
- product_recommendations.csv, product_offers.csv: from the basket EDA

Notes
- Spaghetti 500g is treated as Pasta 400g (hidden from the list; camera maps to Pasta 400g).
- build_*.py need data.csv and only rerun if the data changes.
- Never commit gemini_key.txt.
