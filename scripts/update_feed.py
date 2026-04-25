import urllib.request, xml.etree.ElementTree as ET, json, sys

FEED_URL = "http://export.admitad.com/ru/webmaster/websites/2922896/products/export_adv_products/?user=essem&code=5a533b1307&feed_id=14280&format=xml&fcid=6115"

print("Downloading feed...")
req = urllib.request.Request(FEED_URL, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=120) as r:
    data = r.read()
print(f"Downloaded {len(data)} bytes")

root = ET.fromstring(data)

cats = {}
for cat in root.findall(".//category"):
    cats[cat.get("id", "")] = cat.text or ""

products = []
for o in root.findall(".//offer"):
    def g(tag):
        return (o.findtext(tag) or "").strip()
    try:
        price = float(g("price") or 0)
        oprice = float(g("oldprice") or 0)
        if price <= 0:
            continue
        disc = round((oprice - price) / oprice * 100) if oprice > price else 0
        cat_id = g("categoryId")
        url = g("url")
        if not url:
            continue
        products.append({
            "n": g("name") or g("model"),
            "u": url,
            "i": g("picture"),
            "p": round(price, 2),
            "op": round(oprice, 2),
            "d": disc,
            "c": cats.get(cat_id, ""),
            "fc": g("vendor"),
            "r": round(float(g("rating") or 4.5), 1),
            "rv": int(g("reviews") or g("sales") or 100)
        })
    except Exception as e:
        continue

with open("data/products.json", "w", encoding="utf-8") as f:
    json.dump(products, f, ensure_ascii=False)
print(f"Saved {len(products)} products to data/products.json")
