import urllib.request, xml.etree.ElementTree as ET, json, re

BASE = "http://export.admitad.com/ru/webmaster/websites/2922896/products/export_adv_products/?user=essem&code=5a533b1307&format=xml&fcid=25179&feed_id="

FEEDS = [
    "18900", "18901", "18902", "18903", "18904",
    "18906", "18907", "18908", "21233", "21242",
    "21453", "26232", "26233", "26234", "26235", "26236"
]

MAX_PER_FEED = 200
MIN_PRICE = 3.0

SKIP_CATS = [
    "Electrical Equipment", "Electronic Components", "Connectors",
    "Fasteners", "Screws", "Access Control", "Switches", "Relays",
    "Gearboxes", "Protective", "Soldering", "Sensors", "Modules",
    "детали", "Детали", "запчасти", "Переключател", "Разъем",
    "Коробки", "Ключи", "Держател", "Контроль", "Винты",
    "Industrial", "Tools & Equipment", "Measurement"
]

def is_junk(name, cat):
    if re.search(r"[а-яёА-ЯЁ]", name): return True
    for s in SKIP_CATS:
        if s.lower() in (cat or "").lower(): return True
    return False

def parse(feed_id):
    url = BASE + feed_id
    print(f"[{feed_id}] Fetching...", flush=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    products = []
    cats = {}
    cur = {}
    in_offer = False
    first_pic = None
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            context = ET.iterparse(resp, events=("start", "end"))
            for event, elem in context:
                if len(products) >= MAX_PER_FEED: break
                if event == "start" and elem.tag == "offer":
                    cur = {}; first_pic = None; in_offer = True
                elif event == "end":
                    if elem.tag == "category":
                        cats[elem.get("id", "")] = elem.text or ""
                    elif in_offer:
                        tag = elem.tag
                        text = (elem.text or "").strip()
                        if tag == "picture" and first_pic is None:
                            first_pic = text
                        elif tag not in ("picture","offer","yml_catalog","shop","categories","offers"):
                            cur[tag] = text
                        if tag == "offer":
                            in_offer = False
                            try:
                                price = float(cur.get("price") or 0)
                                if price < MIN_PRICE: elem.clear(); continue
                                img = first_pic or ""
                                if not img: elem.clear(); continue
                                u = cur.get("url", "").replace("aliexpress.ru", "aliexpress.com")
                                if not u: elem.clear(); continue
                                name = cur.get("name") or cur.get("model", "")
                                cat = cats.get(cur.get("categoryId", ""), "")
                                if is_junk(name, cat): elem.clear(); continue
                                oprice = float(cur.get("oldprice") or 0)
                                disc = round((oprice - price) / oprice * 100) if oprice > price else 0
                                products.append({
                                    "n": name, "u": u, "i": img,
                                    "p": round(price, 2),
                                    "op": round(oprice, 2),
                                    "d": disc,
                                    "c": cat,
                                    "fc": cur.get("vendor",""),
                                    "r": 4.5, "rv": 0
                                })
                            except: pass
                            elem.clear()
                    else:
                        elem.clear()
    except Exception as e:
        print(f"[{feed_id}] ERROR: {e}", flush=True)
    print(f"[{feed_id}] Got {len(products)} products", flush=True)
    return products

all_products = []
seen = set()
for feed_id in FEEDS:
    for p in parse(feed_id):
        if p["u"] not in seen:
            seen.add(p["u"])
            all_products.append(p)

with open("data/products.json", "w", encoding="utf-8") as f:
    json.dump({"total": len(all_products), "products": all_products}, f, ensure_ascii=False)
print(f"Done. {len(all_products)} products saved.")
