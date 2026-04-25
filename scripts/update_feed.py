import urllib.request, xml.etree.ElementTree as ET, json

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

MAX_PER_FEED = 200
MIN_RATING = 4.0

def parse(feed_id, price_range):
    url = BASE + feed_id
    print(f"[{feed_id}] Streaming {price_range}...", flush=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept-Encoding": "gzip"})
    
    products = []
    cats = {}
    cur = {}
    in_offer = False
    count = 0

    with urllib.request.urlopen(req, timeout=180) as resp:
        # Stream directly into iterparse — no full buffer
        context = ET.iterparse(resp, events=("start", "end"))
        for event, elem in context:
            if len(products) >= MAX_PER_FEED:
                break
            if event == "start" and elem.tag == "offer":
                cur = {}
                in_offer = True
            elif event == "end":
                if elem.tag == "category":
                    cats[elem.get("id","")]  = elem.text or ""
                elif in_offer and elem.tag not in ("offer","yml_catalog","shop","categories","offers"):
                    cur[elem.tag] = (elem.text or "").strip()
                elif elem.tag == "offer":
                    in_offer = False
                    try:
                        price = float(cur.get("price") or 0)
                        if price <= 0: elem.clear(); continue
                        rating = float(cur.get("rating") or 0)
                        if rating > 0 and rating < MIN_RATING: elem.clear(); continue
                        oprice = float(cur.get("oldprice") or 0)
                        disc = round((oprice-price)/oprice*100) if oprice>price else 0
                        u = cur.get("url","")
                        if not u: elem.clear(); continue
                        products.append({
                            "n": cur.get("name") or cur.get("model",""),
                            "u": u,
                            "i": cur.get("picture",""),
                            "p": round(price,2),
                            "op": round(oprice,2),
                            "d": disc,
                            "c": cats.get(cur.get("categoryId",""),""),
                            "fc": cur.get("vendor",""),
                            "r": round(float(cur.get("rating") or 4.5),1),
                            "rv": int(cur.get("reviews") or cur.get("sales") or 100),
                            "pr": price_range
                        })
                    except: pass
                    elem.clear()
                else:
                    elem.clear()

    print(f"[{feed_id}] Got {len(products)} products", flush=True)
    return products

all_products = []
seen = set()
for feed_id, pr in FEEDS:
    try:
        for p in parse(feed_id, pr):
            if p["u"] not in seen:
                seen.add(p["u"])
                all_products.append(p)
    except Exception as e:
        print(f"[{feed_id}] ERROR: {e}", flush=True)

with open("data/products.json","w",encoding="utf-8") as f:
    json.dump(all_products, f, ensure_ascii=False)
print(f"Done. {len(all_products)} products saved.")
