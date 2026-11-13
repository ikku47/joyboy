"""joyboy maps: real street maps drawn from OpenStreetMap data, styled in code (no tile images, no map library).

    import maps
    lat, lon = maps.geocode("Kozhikode Beach, Kerala")        # place name -> coordinates (cached)
    m = maps.Map(lat, lon, radius_km=2)                       # fetches roads, water, parks, buildings (cached)
    img = m.render(2400, style)                               # BGR uint8 square image
    x, y = m.px(lat2, lon2, 2400)                             # a coordinate's pixel in that image

Data comes from the public Nominatim and Overpass services and is cached in <workspace>/maps, so each
place is downloaded once. Be gentle: one area per scene. Up to ~8 km shows streets; 8-150 km shows main roads only (regions). Maps made from this data
must show the credit "(c) OpenStreetMap contributors"; the quick.py map scene adds it.
"""
import os, json, time, hashlib, urllib.request, urllib.parse
import numpy as np, cv2

HOME = os.environ.get("JOYBOY_HOME", os.path.expanduser("~/joyboy")); CACHE = os.path.join(HOME, "maps")
UA = {"User-Agent": "joyboy-video-kit/1.0"}
ROADS = {"motorway": 7, "trunk": 7, "primary": 6, "secondary": 5, "tertiary": 4, "motorway_link": 4, "trunk_link": 4, "primary_link": 4,
         "residential": 2.2, "unclassified": 2.2, "living_street": 2.2, "pedestrian": 1.6, "service": 1.2, "footway": 0.7, "path": 0.7, "cycleway": 0.7, "track": 0.8}
STYLE = dict(bg=(24, 18, 16), land=(30, 23, 20), water=(92, 58, 28), park=(40, 52, 30), building=(46, 38, 34), road=(150, 138, 130), major=(236, 228, 222), rail=(90, 84, 110))

def _get(key, fetch):
    os.makedirs(CACHE, exist_ok=True); p = os.path.join(CACHE, hashlib.md5(key.encode()).hexdigest()[:16] + ".json")
    if os.path.exists(p): return json.load(open(p))
    d = fetch(); json.dump(d, open(p, "w")); return d

def geocode(place):
    """Place name -> (lat, lon). Pass (lat, lon) through unchanged."""
    if not isinstance(place, str): return float(place[0]), float(place[1])
    def f():
        time.sleep(1.0)
        r = urllib.request.Request("https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({"q": place, "format": "json", "limit": 1}), headers=UA)
        return json.loads(urllib.request.urlopen(r, timeout=40).read())
    d = _get("geo:" + place.lower().strip(), f)
    if not d: raise ValueError(f"place not found: {place}")
    return float(d[0]["lat"]), float(d[0]["lon"])

class Map:
    def __init__(self, lat, lon, radius_km=2.0, buildings=None):
        self.lat, self.lon, self.r = lat, lon, radius_km * 1000
        dlat = self.r / 111320; dlon = self.r / (111320 * np.cos(np.radians(lat))); bb = f"{lat - dlat:.5f},{lon - dlon:.5f},{lat + dlat:.5f},{lon + dlon:.5f}"
        b = radius_km <= 1.5 if buildings is None else buildings
        hw = "" if radius_km <= 3 else '~"motorway|trunk|primary|secondary|tertiary|residential|unclassified"' if radius_km <= 8 else '~"motorway|trunk|primary|secondary"' if radius_km <= 40 else '~"motorway|trunk|primary"'
        q = (f'[out:json][timeout:60];(way["highway"{hw}]({bb});way["natural"~"water|coastline"]({bb});way["waterway"~"river|canal"]({bb});'
             f'way["leisure"~"park|garden|pitch"]({bb});way["landuse"~"forest|grass|meadow|recreation_ground"]({bb});way["railway"="rail"]({bb});' + (f'way["building"]({bb});' if b else "") + ");out geom;")
        def f():
            err = None
            for attempt in range(2):                       # the public servers are sometimes busy: try mirrors, then once more
                for host in ("https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter", "https://overpass.private.coffee/api/interpreter"):
                    try:
                        r = urllib.request.Request(host, data=urllib.parse.urlencode({"data": q}).encode(), headers=UA)
                        return json.loads(urllib.request.urlopen(r, timeout=90).read())
                    except Exception as e: err = e; time.sleep(2)
            raise RuntimeError(f"map data could not be fetched ({err}); try again in a minute")
        self.data = _get("osm:" + q, f)
    def px(self, lat, lon, size):
        """(lat, lon) -> (x, y) pixel in a size x size render."""
        x = (lon - self.lon) * 111320 * np.cos(np.radians(self.lat)); y = (lat - self.lat) * 111320
        return (x / self.r * 0.5 + 0.5) * size, (0.5 - y / self.r * 0.5) * size
    def render(self, size=2400, style=None):
        st = dict(STYLE, **(style or {})); img = np.full((size, size, 3), st["land"], np.uint8); u = size / 2400; layers = {k: [] for k in ("park", "water", "wline", "building", "rail")}; roads = {}
        for e in self.data.get("elements", []):
            g = e.get("geometry"); t = e.get("tags", {})
            if not g: continue
            pts = np.array([self.px(p["lat"], p["lon"], size) for p in g], np.float32)
            closed = len(pts) > 3 and g[0] == g[-1]
            if "highway" in t: roads.setdefault(ROADS.get(t["highway"], 1.0), []).append(pts)
            elif t.get("natural") == "water" and closed: layers["water"].append(pts)
            elif t.get("natural") == "coastline" or "waterway" in t: layers["wline"].append(pts)
            elif "building" in t and closed: layers["building"].append(pts)
            elif "railway" in t: layers["rail"].append(pts)
            elif closed: layers["park"].append(pts)
        I = lambda L: [np.round(p * 8).astype(np.int32) for p in L]
        if layers["park"]: cv2.fillPoly(img, I(layers["park"]), st["park"], cv2.LINE_AA, 3)
        if layers["water"]: cv2.fillPoly(img, I(layers["water"]), st["water"], cv2.LINE_AA, 3)
        if layers["wline"]: cv2.polylines(img, I(layers["wline"]), False, st["water"], max(2, int(7 * u)), cv2.LINE_AA, 3)
        if layers["building"]: cv2.fillPoly(img, I(layers["building"]), st["building"], cv2.LINE_AA, 3)
        if layers["rail"]: cv2.polylines(img, I(layers["rail"]), False, st["rail"], max(1, int(2 * u)), cv2.LINE_AA, 3)
        scale = 1.3 / (self.r / 1000) ** 0.5    # thicker lines on tighter maps
        for w in sorted(roads):
            c = st["major"] if w >= 4 else st["road"] if w >= 2 else tuple(int(v * 0.6 + b * 0.4) for v, b in zip(st["road"], st["land"]))
            cv2.polylines(img, I(roads[w]), False, c, max(1, int(round(w * u * scale))), cv2.LINE_AA, 3)
        return img
