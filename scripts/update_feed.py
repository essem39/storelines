import urllib.request, xml.etree.ElementTree as ET, json, io

BASE = "http://export.admitad.com/ru/webmaster/websites/2922896/products/export_adv_products/?user=essem&code=5a533b1307&format=xml&fcid=6115&feed_id="

FEEDS = [
    ("14280", "25-40"),
    ("14281", "40-55"),
    ("14282", "55-70"),
    ("14283", "70-85"),
    ("14284", "85-100"),
    ("14285", "100+"),
    ("15830", "hot"),
]

def parse_feed_stream(feed_id, price_range):
    url = BASE + feed_id
    print(f"Downloading feed {feed_id} ({price_range})...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    products = []
    cats = {}

    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    print(f"  {len(data)} bytes, parsing...")

    # First pass: collect categories
    for event, elem in ET.iterparse(io.BytesIO(data), events=("end",)):
        if elem.tag == "category":
            cats[elem.get("id", "")] = elem.text or ""
            elem.clear()

    # Second pass: collect offers
    current = {}
    for event, elem in ET.iterparse(io.BytesIO(data), events=("start", "end")):
        if event == "start" and elem.tag == "offer":
            current = {"attrib": elem.attrib}
        elif event == "end" and elem.tag == "offer":
            g = lambda tag: (current.get(tag) or "").strip()
            try:
                price = float(g("price") or 0)
                if price <= 0:
                    current = {}
                    elem.clear()
                    continue
                oprice = float(g("oldprice") or 0)
                disc = round((oprice - price) / oprice * 100) if oprice > price else 0
                url = g("url")
                if not url:
                    current = {}
                    elem.clear()
                    continue
                products.append({
                    "n": g("name") or g("model"),
                    "u": url,
                    "i": g("picture"),
                    "p": round(price, 2),
                    "op": round(oprice, 2),
                    "d": disc,
                    "c": cats.get(g("categoryId"), ""),
                    "fc": g("vendor"),
                    "r": round(float(g("rating") or 4.5), 1),
                    "rv": int(g("reviews") or g("sales") or 100),
                    "pr": price_range
                })
            except:
                pass
            current = {}
            elem.clear()
        elif event == "end" and current:
            if elem.tag not in ("offer", "yml_catalog", "shop", "categories", "offers"):
                current[elem.tag] = elem.text or ""
            elem.clear()

    return products

all_products = []
seen_urls = set()
for feed_id, price_range in FEEDS:
    try:
        products = parse_feed_stream(feed_id, price_range)
        added = 0
        for p in products:
            if p["u"] not in seen_urls:
                seen_urls.add(p["u"])
                all_products.append(p)
                added += 1
        print(f"  Added {added} unique (total: {len(all_products)})")
    except Exception as e:
        print(f"  ERROR on feed {feed_id}: {e}")

with open("data/products.json", "w", encoding="utf-8") as f:
    json.dump(all_products, f, ensure_ascii=False)
print(f"\nDone. Saved {len(all_products)} unique products.")
