import urllib.request, xml.etree.ElementTree as ET, json

FEED_URL = "http://export.admitad.com/ru/webmaster/websites/2922896/products/export_adv_products/?user=essem&code=5a533b1307&feed_id=18978&format=xml"

XIAOMI_BRANDS = ["xiaomi", "redmi", "poco", "mi band", "mijia"]

def parse():
    print("Fetching Xiaomi feed...", flush=True)
    req = urllib.request.Request(FEED_URL, headers={"User-Agent": "Mozilla/5.0"})
    products = []
    cats = {}
    cur = {}
    in_offer = False
    first_pic = None

    with urllib.request.urlopen(req, timeout=120) as resp:
        for event, elem in ET.iterparse(resp, events=("start", "end")):
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
                    elif tag not in ("picture", "offer", "yml_catalog", "shop", "categories", "offers"):
                        cur[tag] = text
                    if tag == "offer":
                        in_offer = False
                        try:
                            price = float(cur.get("price") or 0)
                            if price < 1: elem.clear(); continue
                            img = first_pic or ""
                            if not img: elem.clear(); continue
                            u = cur.get("url", "")
                            if not u: elem.clear(); continue
                            name = cur.get("name", "") + " " + cur.get("model", "")
                            name = name.strip()
                            vendor = cur.get("vendor", "").lower()
                            name_lower = name.lower()
                            if not any(b in vendor or b in name_lower for b in XIAOMI_BRANDS):
                                elem.clear(); continue
                            cat = cats.get(cur.get("categoryId", ""), "")
                            oprice = float(cur.get("oldprice") or 0)
                            disc = round((oprice - price) / oprice * 100) if oprice > price else 0
                            products.append({
                                "n": name,
                                "u": u,
                                "i": img,
                                "p": round(price, 2),
                                "op": round(oprice, 2),
                                "d": disc,
                                "c": cat,
                                "fc": cur.get("vendor", ""),
                                "r": 4.5, "rv": 0
                            })
                        except: pass
                        elem.clear()
                else:
                    elem.clear()

    print(f"Got {len(products)} Xiaomi products", flush=True)
    return products

products = parse()

with open("data/products.json", "w", encoding="utf-8") as f:
    json.dump({"total": len(products), "products": products}, f, ensure_ascii=False)

print(f"Done. {len(products)} products saved.")
