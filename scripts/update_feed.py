import urllib.request, xml.etree.ElementTree as ET, json, io
from concurrent.futures import ThreadPoolExecutor, as_completed

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

MAX_PER_FEED = 300  # limit to keep runtime under 10 min

def parse_feed(feed_id, price_range):
    url = BASE + feed_id
    print(f"[{feed_id}] Downloading...", flush=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    
    with urllib.request.urlopen(req, timeout=180) as r:
        data = r.read()
    print(f"[{feed_id}] {len(data)//1024}KB, parsing...", flush=True)

    cats = {}
    for event, elem in ET.iterparse(io.BytesIO(data), events=("end",)):
        if elem.tag == "category":
            cats[elem.get("id", "")] = elem.text or ""
        elem.clear()

    products = []
    current = {}
    for event, elem in ET.iterparse(io.BytesIO(data), events=("start", "end")):
        if len(products) >= MAX_PER_FEED:
            break
        if event == "start" and elem.tag == "offer":
            current = {}
        elif event == "end" and elem.tag == "offer":
            try:
                price = float(current.get("price") or 0)
                if price <= 0:
                    current = {}; elem.clear(); continue
                oprice = float(current.get("oldprice") or 0)
                disc = round((oprice - price) / oprice * 100) if oprice > price else 0
                url = current.get("url", "")
                if not url:
                    current = {}; elem.clear(); continue
                products.append({
                    "n": current.get("name") or current.get("model",""),
                    "u": url,
                    "i": current.get("picture",""),
                    "p": round(price, 2),
                    "op": round(oprice, 2),
                    "d": disc,
                    "c": cats.get(current.get("categoryId",""), ""),
                    "fc": current.get("vendor",""),
                    "r": round(float(current.get("rating") or 4.5), 1),
                    "rv": int(current.get("reviews") or current.get("sales") or 100),
                    "pr": price_range
                })
            except:
                pass
            current = {}
            elem.clear()
        elif event == "end" and current is not None:
            if elem.tag not in ("yml_catalog","shop","categories","offers","offer"):
                current[elem.tag] = elem.text or ""
            elem.clear()

    print(f"[{feed_id}] Parsed {len(products)} products", flush=True)
    return products

all_products = []
seen_urls = set()

with ThreadPoolExecutor(max_workers=3) as ex:
    futures = {ex.submit(parse_feed, fid, pr): (fid, pr) for fid, pr in FEEDS}
    for future in as_completed(futures):
        fid, pr = futures[future]
        try:
            products = future.result()
            added = 0
            for p in products:
                if p["u"] not in seen_urls:
                    seen_urls.add(p["u"])
                    all_products.append(p)
                    added += 1
            print(f"[{fid}] Added {added} unique (total: {len(all_products)})", flush=True)
        except Exception as e:
            print(f"[{fid}] ERROR: {e}", flush=True)

with open("data/products.json", "w", encoding="utf-8") as f:
    json.dump(all_products, f, ensure_ascii=False)
print(f"\nDone. Saved {len(all_products)} unique products.")
