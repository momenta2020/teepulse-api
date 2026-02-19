from fastapi import FastAPI, Query
from datetime import date
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

CACHE = {}  # (market, q) -> (ts, payload)
CACHE_TTL_SECONDS = 60 * 60  # 1 hour

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

def scrape_etsy_search(q: str, limit: int = 50):
    url = f"https://www.etsy.com/search?q={quote_plus(q)}"
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    items = []
    # Etsy markup changes often; we use robust heuristics: find listing links.
    for a in soup.select('a[href*="/listing/"]'):
        href = a.get("href")
        if not href:
            continue
        if "/listing/" not in href:
            continue
        # normalize
        listing_url = href.split("?")[0]
        listing_id = None
        try:
            # https://www.etsy.com/listing/123456789/title...
            parts = listing_url.split("/listing/")[1].split("/")
            listing_id = parts[0]
        except Exception:
            listing_id = None

        # title heuristic: aria-label or text nearby
        title = a.get("aria-label") or a.get_text(" ", strip=True)
        if not title or len(title) < 8:
            continue

        items.append({
            "id": f"etsy-{listing_id or len(items)+1}",
            "listing_id": listing_id,
            "title": title[:180],
            "url": listing_url,
        })
        if len(items) >= limit:
            break

    # de-dup by url
    seen = set()
    deduped = []
    for it in items:
        if it["url"] in seen:
            continue
        seen.add(it["url"])
        deduped.append(it)

    return deduped[:limit]

@app.get("/trend_real")
def trend_real(market: str = Query(..., pattern="^(US|UK)$"), q: str = "graphic tee"):
    key = (market, q)
    now = time.time()
    cached = CACHE.get(key)
    if cached and (now - cached[0]) < CACHE_TTL_SECONDS:
        return cached[1]

    items = scrape_etsy_search(q=q, limit=50)

    payload = {
        "market": market,
        "date": str(date.today()),
        "query": q,
        "items": items
    }
    CACHE[key] = (now, payload)
    return payload

app = FastAPI(title="TeePulse API")

US = [
  {"id":"us-01","title":"Retro Sunset Mountain Graphic Tee","price":19.95,"currency":"USD","shop":"PrintPilotTees","rating":4.8,"reviews_count":1240,"tags":["retro","sunset","mountain","outdoors","graphictee","vintage"],"bestseller_badge":True},
  {"id":"us-02","title":"Funny Cat Meme Graphic T-Shirt","price":17.50,"currency":"USD","shop":"MemeMintStudio","rating":4.7,"reviews_count":860,"tags":["funny","cat","meme","humor","graphic","giftidea"],"bestseller_badge":False},
  {"id":"us-03","title":"Minimal Line Art Face Printed Tee","price":21.00,"currency":"USD","shop":"LineLoreApparel","rating":4.6,"reviews_count":540,"tags":["minimal","lineart","face","aesthetic","modern","print"],"bestseller_badge":False},
  {"id":"us-04","title":"Vintage 90s Neon Grid Graphic Tee","price":22.95,"currency":"USD","shop":"NeonNostalgiaCo","rating":4.9,"reviews_count":1520,"tags":["90s","neon","retro","synthwave","grid","vaporwave"],"bestseller_badge":True},
  {"id":"us-05","title":"Vintage Botanical Mushroom Graphic Tee","price":20.00,"currency":"USD","shop":"ForestPrintsLab","rating":4.8,"reviews_count":980,"tags":["mushroom","botanical","vintage","nature","cottagecore","fungi"],"bestseller_badge":True},
  {"id":"us-06","title":"Retro Gamer Pixel Art Graphic Tee","price":19.00,"currency":"USD","shop":"PixelPressTees","rating":4.8,"reviews_count":1120,"tags":["gamer","pixel","retro","arcade","8bit","nostalgia"],"bestseller_badge":True},
  {"id":"us-07","title":"Streetwear Koi Fish Japanese Graphic Tee","price":26.00,"currency":"USD","shop":"TokyoThreadline","rating":4.8,"reviews_count":605,"tags":["koi","japanese","streetwear","anime","wave","fish"],"bestseller_badge":False},
  {"id":"us-08","title":"Cute Frog Cottagecore Graphic Tee","price":18.50,"currency":"USD","shop":"CottageKawaiiTees","rating":4.8,"reviews_count":740,"tags":["frog","cute","cottagecore","whimsical","nature","kawaii"],"bestseller_badge":False},
  {"id":"us-09","title":"Astronaut Space Illustration Graphic Tee","price":18.99,"currency":"USD","shop":"CosmicCotton","rating":4.6,"reviews_count":410,"tags":["astronaut","space","galaxy","nasa","science","illustration"],"bestseller_badge":False},
  {"id":"us-10","title":"Skull Rose Tattoo Style Graphic Tee","price":24.00,"currency":"USD","shop":"InkThreadWorks","rating":4.7,"reviews_count":690,"tags":["skull","rose","tattoo","edgy","biker","streetwear"],"bestseller_badge":False},
  {"id":"us-11","title":"Retro Cowboy Western Graphic Tee","price":23.50,"currency":"USD","shop":"DesertDriftTees","rating":4.7,"reviews_count":770,"tags":["cowboy","western","retro","rodeo","country","boots"],"bestseller_badge":False},
  {"id":"us-12","title":"Positive Mental Health Quote Graphic Tee","price":16.99,"currency":"USD","shop":"CalmCottonClub","rating":4.7,"reviews_count":510,"tags":["mentalhealth","positive","quote","selfcare","kindness","text"],"bestseller_badge":False},
  {"id":"us-13","title":"Vintage Band Style Lightning Graphic Tee","price":21.95,"currency":"USD","shop":"AmpAndInk","rating":4.6,"reviews_count":330,"tags":["bandstyle","lightning","rock","concert","distressed","vintage"],"bestseller_badge":False},
  {"id":"us-14","title":"Minimal Typography 'Coffee First' Tee","price":15.99,"currency":"USD","shop":"TypeAndBrew","rating":4.6,"reviews_count":640,"tags":["coffee","typography","minimal","morning","cafe","textprint"],"bestseller_badge":False},
  {"id":"us-15","title":"Vintage USA Eagle Distressed Graphic Tee","price":25.00,"currency":"USD","shop":"PatriotPrintHouse","rating":4.5,"reviews_count":290,"tags":["eagle","distressed","usa","vintage","americana","flag"],"bestseller_badge":False},
]

UK = [
  {"id":"uk-01","title":"Retro British Seaside Sunset Graphic Tee","price":17.95,"currency":"GBP","shop":"SeasidePrintCo","rating":4.8,"reviews_count":520,"tags":["retro","seaside","sunset","coastal","vintage","uk"],"bestseller_badge":True},
  {"id":"uk-02","title":"Funny Tea Lover Quote Graphic Tee","price":14.50,"currency":"GBP","shop":"BrewedTypeStudio","rating":4.7,"reviews_count":610,"tags":["tea","funny","quote","britishhumor","text","giftidea"],"bestseller_badge":False},
  {"id":"uk-03","title":"Vintage London Skyline Graphic T-Shirt","price":18.99,"currency":"GBP","shop":"CityInkLondon","rating":4.6,"reviews_count":405,"tags":["london","skyline","vintage","travel","uk","graphictee"],"bestseller_badge":False},
  {"id":"uk-04","title":"90s Neon Rave Grid Graphic Tee","price":19.50,"currency":"GBP","shop":"RaveRevival","rating":4.9,"reviews_count":830,"tags":["90s","neon","rave","retro","synthwave","vaporwave"],"bestseller_badge":True},
  {"id":"uk-05","title":"Botanical Mushroom Vintage Print Tee","price":16.00,"currency":"GBP","shop":"WoodlandPressUK","rating":4.8,"reviews_count":720,"tags":["mushroom","botanical","vintage","nature","cottagecore","fungi"],"bestseller_badge":True},
  {"id":"uk-06","title":"Retro Gamer Pixel Art Graphic Tee","price":16.50,"currency":"GBP","shop":"PixelPintPrints","rating":4.8,"reviews_count":680,"tags":["gamer","pixel","retro","arcade","8bit","nostalgia"],"bestseller_badge":True},
  {"id":"uk-07","title":"Cute Frog Cottagecore Graphic Tee","price":15.50,"currency":"GBP","shop":"CottageCritters","rating":4.8,"reviews_count":510,"tags":["frog","cute","cottagecore","whimsical","kawaii","nature"],"bestseller_badge":False},
  {"id":"uk-08","title":"Astronaut Space Illustration Graphic Tee","price":15.99,"currency":"GBP","shop":"OrbitCottonUK","rating":4.6,"reviews_count":310,"tags":["astronaut","space","galaxy","science","illustration","stars"],"bestseller_badge":False},
  {"id":"uk-09","title":"Streetwear Koi Fish Japanese Graphic Tee","price":21.00,"currency":"GBP","shop":"KoiKulture","rating":4.8,"reviews_count":340,"tags":["koi","japanese","streetwear","wave","fish","graphic"],"bestseller_badge":False},
  {"id":"uk-10","title":"Minimal Typography 'Tea First' Tee","price":12.99,"currency":"GBP","shop":"TypeAndTea","rating":4.6,"reviews_count":440,"tags":["tea","typography","minimal","morning","cafe","textprint"],"bestseller_badge":False},
  {"id":"uk-11","title":"Self Care Positive Quote Graphic Tee","price":13.99,"currency":"GBP","shop":"KindWordsClub","rating":4.7,"reviews_count":390,"tags":["selfcare","positive","quote","kindness","text","wellbeing"],"bestseller_badge":False},
  {"id":"uk-12","title":"Retro Football Fan Graphic Tee","price":17.00,"currency":"GBP","shop":"TerraceTees","rating":4.7,"reviews_count":455,"tags":["football","retro","fan","terrace","sport","uk"],"bestseller_badge":False},
  {"id":"uk-13","title":"Minimal Line Art Face Printed Tee","price":18.00,"currency":"GBP","shop":"MinimalMews","rating":4.6,"reviews_count":260,"tags":["minimal","lineart","face","aesthetic","modern","print"],"bestseller_badge":False},
  {"id":"uk-14","title":"Vintage Band Style Lightning Graphic Tee","price":18.50,"currency":"GBP","shop":"AmpersandApparel","rating":4.6,"reviews_count":210,"tags":["bandstyle","lightning","rock","distressed","vintage","gig"],"bestseller_badge":False},
  {"id":"uk-15","title":"Vintage Skull Rose Tattoo Style Graphic Tee","price":20.00,"currency":"GBP","shop":"InkRoseUK","rating":4.7,"reviews_count":275,"tags":["skull","rose","tattoo","edgy","streetwear","print"],"bestseller_badge":False},
]

def expand(items, n=50):
    out = []
    i = 0
    while len(out) < n:
        base = items[i % len(items)].copy()
        base["id"] = f'{base["id"]}-{len(out)+1:02d}'
        base["rank"] = len(out) + 1
        base["trending_score"] = (100 - base["rank"]) + (10 if base.get("bestseller_badge") else 0) + (base.get("reviews_count", 0) % 7)
        out.append(base)
        i += 1
    return out

@app.get("/trend")
def trend(market: str = Query(..., pattern="^(US|UK)$")):
    items = expand(US if market == "US" else UK, 50)
    return {"market": market, "date": str(date.today()), "items": items}

@app.get("/health")
def health():
    return {"ok": True}
