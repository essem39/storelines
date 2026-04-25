import urllib.request, xml.etree.ElementTree as ET, json

BASE = "http://export.admitad.com/ru/webmaster/websites/2922896/products/export_adv_products/?user=essem&code=5a533b1307&format=xml&fcid=6115&feed_id="

FEEDS = [
    ("14280", "25-40"),
    ("14281", "40-55"),
    ("14282", "55-70"),
    ("14283", "70-85"),
    ("14284", "85-100"),
    ("15830", "hot"),
]

def parse_feed(feed_id, price_range):
    url = BASE + feed_id
    print(f"Downloading feed {feed_id} ({price_range})...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    print(f"  {len(data)} bytes")
    root = ET.fromstring(data)
    cats = {c.get("id",""): c.text or "" for c in root.findall(".//category")}
    products = []
    for o in root.findall(".//offer"):
        def g(tag): return (o.findtext(tag) or "").strip()
        try:
            price = float(g("price") or 0)
            if price <= 0: continue
            oprice = float(g("oldprice") or 0)
            disc = round((oprice - price) / oprice * 100) if oprice > price else 0
            url = g("url")
            if not url: continue
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
        except: continue
    return products

all_products = []
seen_urls = set()
for feed_id, price_range in FEEDS:
    products = parse_feed(feed_id, price_range)
    for p in products:
        if p["u"] not in seen_urls:
            seen_urls.add(p["u"])
            all_products.append(p)
    print(f"  Added {len(products)} products (total: {len(all_products)})")

with open("data/products.json", "w", encoding="utf-8") as f:
    json.dump(all_products, f, ensure_ascii=False)
print(f"\nDone. Saved {len(all_products)} unique products.")
