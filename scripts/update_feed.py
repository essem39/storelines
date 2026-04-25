import urllib.request, xml.etree.ElementTree as ET, json, io

# One feed that works — price ranges handled in JS
FEEDS = [
    ("http://export.admitad.com/ru/webmaster/websites/2922896/products/export_adv_products/?user=essem&code=5a533b1307&feed_id=14280&format=xml&fcid=6115", "25-40"),
    ("http://export.admitad.com/ru/webmaster/websites/2922896/products/export_adv_products/?user=essem&code=5a533b1307&feed_id=14281&format=xml&fcid=6115", "40-55"),
    ("http://export.admitad.com/ru/webmaster/websites/2922896/products/export_adv_products/?user=essem&code=5a533b1307&feed_id=15830&format=xml&fcid=6115", "hot"),
]

MAX_PER_FEED = 250

def parse(url, price_range):
    print(f"Downloading {price_range}...", flush=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=180) as r:
        data = r.read()
    print(f"  {len(data)//1024}KB", flush=True)

    cats = {}
    for _, elem in ET.iterparse(io.BytesIO(data), events=("end",)):
        if elem.tag == "category":
            cats[elem.get("id","")] = elem.text or ""
        elem.clear()

    products = []
    cur = {}
    for event, elem in ET.iterparse(io.BytesIO(data), events=("start","end")):
        if len(products) >= MAX_PER_FEED:
            break
        if event == "start" and elem.tag == "offer":
            cur = {}
        elif event == "end" and elem.tag == "offer":
            try:
                price = float(cur.get("price") or 0)
                if price <= 0: cur={}; elem.clear(); continue
                oprice = float(cur.get("oldprice") or 0)
                disc = round((oprice-price)/oprice*100) if oprice>price else 0
                u = cur.get("url","")
                if not u: cur={}; elem.clear(); continue
                products.append({
                    "n": cur.get("name") or cur.get("model",""),
                    "u": u, "i": cur.get("picture",""),
                    "p": round(price,2), "op": round(oprice,2),
                    "d": disc, "c": cats.get(cur.get("categoryId",""),""),
                    "fc": cur.get("vendor",""),
                    "r": round(float(cur.get("rating") or 4.5),1),
                    "rv": int(cur.get("reviews") or cur.get("sales") or 100),
                    "pr": price_range
                })
            except: pass
            cur={}; elem.clear()
        elif event=="end" and cur is not None:
            if elem.tag not in ("yml_catalog","shop","categories","offers","offer"):
                cur[elem.tag] = elem.text or ""
            elem.clear()

    print(f"  {len(products)} products", flush=True)
    return products

all_products = []
seen = set()
for url, pr in FEEDS:
    try:
        for p in parse(url, pr):
            if p["u"] not in seen:
                seen.add(p["u"])
                all_products.append(p)
    except Exception as e:
        print(f"ERROR {pr}: {e}", flush=True)

print(f"Total: {len(all_products)}", flush=True)
with open("data/products.json","w",encoding="utf-8") as f:
    json.dump(all_products, f, ensure_ascii=False)
print("Done.")
