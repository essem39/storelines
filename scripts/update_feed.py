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

MAX_PER_FEED = 300

def get_eur_rate():
    """Fetch USD->EUR rate from ECB"""
    try:
        url = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            xml = resp.read().decode()
        import re
        m = re.search(r"currency=\'USD\' rate=\'([\d.]+)\'", xml)
        if not m:
            m = re.search(r'currency="USD" rate="([\d.]+)"', xml)
        if m:
            usd_per_eur = float(m.group(1))
            rate = round(1 / usd_per_eur, 4)
            print(f"ECB rate: 1 USD = {rate} EUR")
            return rate
    except Exception as e:
        print(f"ECB fetch failed: {e}, using fallback 0.92")
    return 0.92

def to_eur(usd, rate):
    if not usd or usd <= 0:
        return 0
    return round(usd * rate, 2)

def parse(feed_id, price_range, eur_rate):
    url = BASE + feed_id
    print(f"[{feed_id}] Fetching {price_range}...", flush=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

    products = []
    cats = {}
    cur = {}
    in_offer = False
    first_pic = None

    with urllib.request.urlopen(req, timeout=180) as resp:
        context = ET.iterparse(resp, events=("start", "end"))
        for event, elem in context:
            if len(products) >= MAX_PER_FEED:
                break
            if event == "start" and elem.tag == "offer":
                cur = {}
                first_pic = None
                in_offer = True
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
                            price_usd = float(cur.get("price") or 0)
                            if price_usd <= 0:
                                elem.clear()
                                continue
                            img = first_pic or ""
                            if not img:
                                elem.clear()
                                continue
                            u = cur.get("url", "")
                            if not u:
                                elem.clear()
                                continue
                            oprice_usd = float(cur.get("oldprice") or 0)
                            price_eur = to_eur(price_usd, eur_rate)
                            oprice_eur = to_eur(oprice_usd, eur_rate)
                            disc = round((oprice_eur - price_eur) / oprice_eur * 100) if oprice_eur > price_eur else 0
                            products.append({
                                "n": cur.get("name") or cur.get("model", ""),
                                "u": u,
                                "i": img,
                                "p": price_eur,
                                "op": oprice_eur,
                                "d": disc,
                                "c": cats.get(cur.get("categoryId", ""), ""),
                                "fc": cur.get("vendor", ""),
                                "r": 4.5,
                                "rv": 0,
                                "pr": price_range,
                                "cur": "EUR"
                            })
                        except Exception as e:
                            pass
                        elem.clear()
                else:
                    elem.clear()

    print(f"[{feed_id}] Got {len(products)} products", flush=True)
    return products

# Get EUR rate once
eur_rate = get_eur_rate()

all_products = []
seen = set()
for feed_id, pr in FEEDS:
    try:
        for p in parse(feed_id, pr, eur_rate):
            if p["u"] not in seen:
                seen.add(p["u"])
                all_products.append(p)
    except Exception as e:
        print(f"[{feed_id}] ERROR: {e}", flush=True)

with open("data/products.json", "w", encoding="utf-8") as f:
    json.dump({"eur_rate": eur_rate, "products": all_products}, f, ensure_ascii=False)
print(f"Done. {len(all_products)} products saved at rate {eur_rate}.")
