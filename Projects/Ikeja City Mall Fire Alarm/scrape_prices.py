#!/usr/bin/env python3
"""
Fire alarm price scraper - Ikeja City Mall RFP, items 1-11.

Run this on a machine with normal internet access. It queries Nigerian and UK
online stores for each RFP line item and writes a CSV plus a printed summary.

    pip install requests beautifulsoup4
    python3 scrape_prices.py                  # everything
    python3 scrape_prices.py --only jiji      # one source
    python3 scrape_prices.py --item 2 --item 9 # selected RFP items
    python3 scrape_prices.py --debug          # dump raw responses when a parse fails

Optional Firecrawl path, for sites that block plain requests (Cloudflare etc.):

    pip install firecrawl-py
    export FIRECRAWL_API_KEY=fc-...
    python3 scrape_prices.py --firecrawl

Output: prices.csv  (item, source, title, price_ngn, price_raw, url)

Nothing here needs a paid service. Firecrawl is a fallback, not a requirement.
"""

import argparse
import csv
import json
import re
import sys
import time
from urllib.parse import quote_plus

try:
    import requests
except ImportError:
    sys.exit("pip install requests beautifulsoup4")

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9",
}
PAUSE = 2.0          # seconds between requests - be a polite guest
TIMEOUT = 30

# --------------------------------------------------------------- RFP items --
# (rfp_item, description, qty, search terms tried in order)
ITEMS = [
    (1,  "Vigilon Plus 24 main panel, 1-4 loop", 1,
     ["gent vigilon plus control panel", "VIGPLUS-24", "gent vigplus 24"]),
    (2,  "S4-715 optical smoke detector + S4-700 base", 385,
     ["gent S4-715", "gent optical smoke detector addressable", "gent S4-700 base"]),
    (3,  "S4-720 heat detector", 60,
     ["gent S4-720", "gent addressable heat detector"]),
    (4,  "S4-34842 manual call point c/w cover", 35,
     ["gent S4-34842", "gent addressable manual call point"]),
    (5,  "S3-S-VAD-HPR-R sounder + high power VAD", 60,
     ["gent S3-S-VAD-HPR-R", "gent addressable sounder VAD"]),
    (6,  "Two-channel interface module", 20,
     ["gent S4-34412", "gent interface module addressable"]),
    (7,  "FR cable 1.5mm2 2-core, 100m drum", 30,
     ["FP200 gold 1.5mm 2 core 100m", "fire resistant cable 1.5mm 2 core 100m"]),
    (9,  "Vigilon Plus loop card", 4,
     ["gent VIG-LPC-EN", "gent vigilon loop card"]),
    (10, "Vigilon Compact Plus 1-2 loop panel", 1,
     ["gent compact plus panel", "COMPACT-PLUS vigilon"]),
    (11, "Vigilon network card", 1,
     ["gent VIG-NC network card", "gent vigilon network card"]),
]
# Items 8, 12 and 13 are lot/labour lines with no unit rate - deliberately omitted.

PRICE_RE = re.compile(r"(?:₦|NGN|N)\s?([\d][\d,\.]{2,})", re.I)
GBP_RE = re.compile(r"£\s?([\d][\d,\.]{1,})")


def to_number(raw):
    """'₦4,910,000' -> 4910000.0

    Nigerian listings mix separators freely: '4,910,000', '4.500.000', '51,000'.
    A separator is decimal only when it is the sole one and exactly one or two
    digits follow it; everything else is a thousands separator.
    """
    if raw is None:
        return None
    s = re.sub(r"[^\d.,]", "", str(raw))
    if not s:
        return None

    if "," in s and "." in s:
        # Both present: whichever comes last is the decimal point.
        if s.rfind(".") > s.rfind(","):
            s = s.replace(",", "")
        else:
            s = s.replace(".", "").replace(",", ".")
    else:
        for sep in (",", "."):
            if sep not in s:
                continue
            tail = s.rsplit(sep, 1)[1]
            if s.count(sep) == 1 and len(tail) in (1, 2):
                s = s.replace(sep, ".")      # genuine decimal
            else:
                s = s.replace(sep, "")       # thousands grouping
            break

    try:
        return float(s)
    except ValueError:
        return None


def get(url, session, as_json=False, debug=False):
    try:
        r = session.get(url, headers=HEADERS, timeout=TIMEOUT)
    except requests.RequestException as e:
        print(f"    ! request failed: {e}")
        return None
    if r.status_code != 200:
        print(f"    ! HTTP {r.status_code} {url}")
        if debug:
            print(r.text[:500])
        return None
    if as_json:
        try:
            return r.json()
        except ValueError:
            if debug:
                print("    ! not JSON:", r.text[:300])
            return None
    return r.text


# ------------------------------------------------------------------- Jiji --
def scrape_jiji(term, session, debug=False):
    """Jiji exposes a JSON listing API; fall back to parsing the HTML page."""
    rows = []
    api = f"https://jiji.ng/api_web/v1/listing?query={quote_plus(term)}&webp=false"
    data = get(api, session, as_json=True, debug=debug)
    if data:
        adverts = []
        # The payload nests results differently across versions - dig for them.
        for key in ("adverts_list", "adverts", "results"):
            node = data.get(key)
            if isinstance(node, dict) and "adverts" in node:
                adverts = node["adverts"]
                break
            if isinstance(node, list):
                adverts = node
                break
        for a in adverts or []:
            if not isinstance(a, dict):
                continue
            price = a.get("price_obj", {}).get("value") or a.get("price")
            rows.append({
                "title": a.get("title", ""),
                "price_raw": a.get("price_title") or str(price or ""),
                "price_ngn": to_number(price),
                "url": "https://jiji.ng" + a.get("url", ""),
                "where": a.get("region_name") or a.get("region_item_text") or "",
            })
    if rows:
        return rows

    # HTML fallback
    if BeautifulSoup is None:
        return rows
    html = get(f"https://jiji.ng/search?query={quote_plus(term)}", session, debug=debug)
    if not html:
        return rows
    soup = BeautifulSoup(html, "html.parser")
    for card in soup.select("a[href*='/safety-equipment/'], div.b-list-advert__gallery__item"):
        text = card.get_text(" ", strip=True)
        m = PRICE_RE.search(text)
        if not m:
            continue
        href = card.get("href") or ""
        rows.append({
            "title": text[:110],
            "price_raw": m.group(0),
            "price_ngn": to_number(m.group(1)),
            "url": href if href.startswith("http") else "https://jiji.ng" + href,
            "where": "",
        })
    return rows


# ------------------------------------------------- WooCommerce (NG stores) --
WOO_SITES = [
    ("faxon", "https://faxontechnologies.com"),
    ("cloudsecurity", "https://cloudsecurity.com.ng"),
    ("safetyhub", "https://safetyhub.com.ng"),
    ("safetysouk", "https://safetysouk.com.ng"),
]


def scrape_woo(term, session, debug=False):
    """Most Nigerian fire-safety shops run WooCommerce, which exposes a clean
    Store API at /wp-json/wc/store/v1/products?search=... - no scraping needed."""
    rows = []
    for name, base in WOO_SITES:
        url = f"{base}/wp-json/wc/store/v1/products?search={quote_plus(term)}&per_page=10"
        data = get(url, session, as_json=True, debug=debug)
        if not data:
            # older Woo exposes v1-less path
            data = get(f"{base}/wp-json/wc/store/products?search={quote_plus(term)}",
                       session, as_json=True, debug=debug)
        if not isinstance(data, list):
            continue
        for p in data:
            prices = p.get("prices", {}) or {}
            minor = prices.get("currency_minor_unit", 2)
            raw = prices.get("price")
            val = to_number(raw)
            if val is not None and minor:
                val = val / (10 ** minor)
            rows.append({
                "title": p.get("name", ""),
                "price_raw": f"{prices.get('currency_symbol','')}{raw}",
                "price_ngn": val,
                "url": p.get("permalink", base),
                "where": name,
            })
        time.sleep(PAUSE)
    return rows


# --------------------------------------------------------- UK reference ----
UK_SITES = [
    ("securitywarehouse", "https://www.securitywarehouse.co.uk/catalog/index.php?main_page=advanced_search_result&search_in_description=1&keyword={q}"),
    ("firetradesupplies", "https://www.firetradesupplies.com/search?q={q}"),
    ("acornfiresecurity", "https://www.acornfiresecurity.com/search?q={q}"),
]


def scrape_uk(term, session, debug=False):
    """UK trade prices in GBP - a sanity ceiling for the Nigerian numbers."""
    rows = []
    if BeautifulSoup is None:
        return rows
    for name, tpl in UK_SITES:
        html = get(tpl.format(q=quote_plus(term)), session, debug=debug)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        text_blocks = soup.select("div.product, li.product, div.productListing, "
                                  "div.grid-product, article")
        for blk in text_blocks[:10]:
            t = blk.get_text(" ", strip=True)
            m = GBP_RE.search(t)
            if not m:
                continue
            link = blk.find("a", href=True)
            rows.append({
                "title": t[:110],
                "price_raw": m.group(0),
                "price_gbp": to_number(m.group(1)),
                "url": link["href"] if link else "",
                "where": name,
            })
        time.sleep(PAUSE)
    return rows


# ----------------------------------------------------------- Firecrawl -----
FC_BASE = "https://api.firecrawl.dev/v2"


class Firecrawl:
    """Thin REST client - no SDK dependency, just requests.

    Used when the target sites block plain HTTP (Cloudflare, bot walls) or
    when you would rather let Firecrawl handle rendering. Firecrawl's servers
    do the fetching, so this also works from networks that cannot reach the
    stores directly.
    """

    def __init__(self, api_key, debug=False):
        self.key = api_key
        self.debug = debug
        self.s = requests.Session()

    def _post(self, path, payload):
        try:
            r = self.s.post(f"{FC_BASE}{path}",
                            headers={"Authorization": f"Bearer {self.key}",
                                     "Content-Type": "application/json"},
                            json=payload, timeout=90)
        except requests.RequestException as e:
            print(f"    ! firecrawl unreachable: {e}")
            return None
        if r.status_code == 401:
            print("    ! firecrawl 401 - check FIRECRAWL_API_KEY")
            return None
        if r.status_code == 429:
            print("    ! firecrawl rate limited - pausing 20s")
            time.sleep(20)
            return None
        if r.status_code >= 400:
            print(f"    ! firecrawl HTTP {r.status_code}")
            if self.debug:
                print(r.text[:400])
            return None
        try:
            return r.json()
        except ValueError:
            return None

    def search(self, query, limit=10):
        """Discover pages and get their content in one call."""
        data = self._post("/search", {
            "query": query,
            "limit": limit,
            "scrapeOptions": {"formats": ["markdown"]},
        })
        if not data:
            return []
        out = data.get("data")
        if isinstance(out, dict):                 # {web: [...]} shape
            out = out.get("web") or out.get("results") or []
        return out or []

    def scrape(self, url):
        data = self._post("/scrape", {"url": url, "formats": ["markdown"]})
        if not data:
            return None
        d = data.get("data") or data
        return d.get("markdown") if isinstance(d, dict) else None


def prices_from_markdown(md, title_hint="", url="", where=""):
    """Pull Naira and GBP figures out of a markdown blob.

    Takes a little context either side of each hit so the row is readable,
    and drops absurd values that are almost always phone numbers or IDs.
    """
    rows = []
    if not md:
        return rows
    for rx, field in ((PRICE_RE, "price_ngn"), (GBP_RE, "price_gbp")):
        for m in rx.finditer(md):
            val = to_number(m.group(1))
            if val is None:
                continue
            if field == "price_ngn" and not (1_000 <= val <= 500_000_000):
                continue                      # phone numbers, TINs, years
            if field == "price_gbp" and not (1 <= val <= 200_000):
                continue
            start = max(0, m.start() - 90)
            ctx = " ".join(md[start:m.end() + 40].split())
            rows.append({
                "title": (title_hint or ctx)[:110],
                "price_raw": m.group(0),
                field: val,
                "url": url,
                "where": where,
            })
    return rows


def scrape_via_firecrawl(term, fc):
    """Search Jiji and the Nigerian stores through Firecrawl, then the UK
    reference sites, returning the same row shape as the direct scrapers."""
    rows = []
    for site, tag in (("jiji.ng", "jiji"),
                      ("faxontechnologies.com OR cloudsecurity.com.ng "
                       "OR safetyhub.com.ng", "ng-store"),
                      ("securitywarehouse.co.uk OR firetradesupplies.com",
                       "uk-ref")):
        hits = fc.search(f"{term} site:{site}" if " OR " not in site
                         else f"{term} price", limit=8)
        for h in hits:
            if not isinstance(h, dict):
                continue
            md = h.get("markdown") or h.get("description") or ""
            found = prices_from_markdown(
                md, title_hint=h.get("title", ""),
                url=h.get("url", ""), where=tag)
            rows += [dict(r, source=tag) for r in found[:4]]
        time.sleep(1.0)
    return rows


# ---------------------------------------------------------------- driver ---
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=["jiji", "woo", "uk"],
                    help="restrict to one source")
    ap.add_argument("--item", type=int, action="append",
                    help="RFP item number; repeatable")
    ap.add_argument("--firecrawl", action="store_true",
                    help="use Firecrawl for pages that block plain requests")
    ap.add_argument("--debug", action="store_true")
    ap.add_argument("-o", "--out", default="prices.csv")
    args = ap.parse_args()

    import os
    fc = None
    if args.firecrawl:
        fc_key = os.environ.get("FIRECRAWL_API_KEY")
        if not fc_key:
            sys.exit("--firecrawl needs FIRECRAWL_API_KEY in the environment.\n"
                     "  export FIRECRAWL_API_KEY=fc-...\n"
                     "Never hardcode the key in this file - it is version controlled.")
        fc = Firecrawl(fc_key, debug=args.debug)
        print("Using Firecrawl (server-side fetching)")

    session = requests.Session()
    wanted = set(args.item) if args.item else None
    results = []

    for num, desc, qty, terms in ITEMS:
        if wanted and num not in wanted:
            continue
        print(f"\n=== RFP item {num}: {desc}  (qty {qty}) ===")
        for term in terms:
            print(f"  searching: {term!r}")
            batch = []
            if fc:
                # Firecrawl does the fetching server-side, so this path also
                # works from a network that cannot reach the stores directly.
                batch += scrape_via_firecrawl(term, fc)
            else:
                if args.only in (None, "jiji"):
                    batch += [dict(r, source="jiji")
                              for r in scrape_jiji(term, session, args.debug)]
                    time.sleep(PAUSE)
                if args.only in (None, "woo"):
                    batch += [dict(r, source="ng-store")
                              for r in scrape_woo(term, session, args.debug)]
                if args.only in (None, "uk"):
                    batch += [dict(r, source="uk-ref")
                              for r in scrape_uk(term, session, args.debug)]

            for r in batch:
                r["rfp_item"] = num
                r["rfp_desc"] = desc
                r["qty"] = qty
                results.append(r)
                price = r.get("price_ngn") or r.get("price_gbp")
                cur = "NGN" if r.get("price_ngn") else "GBP"
                if price:
                    print(f"    {cur} {price:>12,.2f}  {r['title'][:62]}")
            if batch:
                break        # first term that returns anything wins

    if not results:
        print("\nNothing captured. Re-run with --debug to see what came back.")
        return

    fields = ["rfp_item", "rfp_desc", "qty", "source", "where",
              "title", "price_ngn", "price_gbp", "price_raw", "url"]
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(results)
    print(f"\nWrote {len(results)} rows to {args.out}")

    print("\n--- median Naira price per RFP item ---")
    for num, desc, qty, _ in ITEMS:
        vals = sorted(r["price_ngn"] for r in results
                      if r["rfp_item"] == num and r.get("price_ngn"))
        if not vals:
            continue
        mid = vals[len(vals) // 2] if len(vals) % 2 else \
            (vals[len(vals) // 2 - 1] + vals[len(vals) // 2]) / 2
        print(f"  item {num:<3} n={len(vals):<3} low {vals[0]:>12,.0f}  "
              f"median {mid:>12,.0f}  high {vals[-1]:>12,.0f}")


if __name__ == "__main__":
    main()
