# tools/nasa.py
# ---------------------------------------------------------------------------
# NASA integration for Stage 2. The six survey worlds are REAL exoplanets and
# their specifications come LIVE from NASA:
#
#   * Specs  -> NASA Exoplanet Archive "TAP" service (ADQL query, no key needed)
#              https://exoplanetarchive.ipac.caltech.edu/TAP/sync
#   * Images -> NASA Image and Video Library (no key needed)
#              https://images-api.nasa.gov/search
#   * Backdrop -> Astronomy Picture of the Day (uses your api.nasa.gov key)
#              https://api.nasa.gov/planetary/apod
#
# Design rules that keep the classroom demo reliable:
#   - We only ADD real data on top of a fixed, curated list of six planets, so
#     the game design (mini-games, crew notes, the one habitable answer) is
#     stable no matter what the network does.
#   - Every network call has a timeout and a fallback. If NASA is unreachable we
#     use the last good data, then a bundled snapshot -- the game always works.
#   - The API key is read from the environment (.env). It is NEVER hardcoded,
#     logged, or sent to the browser.
#   - No new dependencies: we use Python's built-in urllib.
# ---------------------------------------------------------------------------

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# --- Where things live on disk ---------------------------------------------
_STATIC = Path(__file__).parent.parent / "static"
_CACHE_PATH = _STATIC / "data" / "planets_cache.json"      # last good LIVE specs
_FALLBACK_PATH = _STATIC / "data" / "planets_fallback.json"  # bundled snapshot
_IMG_DIR = _STATIC / "assets" / "planets"
_BACKDROP_PATH = _STATIC / "assets" / "backdrop" / "apod.jpg"

# --- NASA endpoints ---------------------------------------------------------
_TAP_URL = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
_IMAGES_URL = "https://images-api.nasa.gov/search"
_APOD_URL = "https://api.nasa.gov/planetary/apod"
_USER_AGENT = "StarTrekAwayMission/1.0 (educational teaching project)"
_TIMEOUT = 12  # seconds; keep the game responsive if NASA is slow

# The columns we pull from the Exoplanet Archive's "pscomppars" table (which has
# exactly one composite row per planet -- avoids duplicate rows).
_TAP_FIELDS = (
    "pl_name,hostname,pl_rade,pl_bmasse,pl_orbsmax,pl_orbper,pl_eqt,pl_insol,"
    "st_teff,st_spectype,sy_dist,disc_year,discoverymethod"
)

# 1 parsec in light-years (to show a friendlier distance to students).
_PC_TO_LY = 3.26156


# ---------------------------------------------------------------------------
# THE CURATED SIX. Real exoplanets, each chosen to teach one habitability idea.
# The NUMBERS come from NASA at runtime; only the game flavour is authored here.
# Exactly ONE has habitable=True (the correct final pick).
# ---------------------------------------------------------------------------
EXOPLANETS: list[dict] = [
    {
        "id": "trappist_e",
        "pl_name": "TRAPPIST-1 e",
        "habitable": True,  # the answer: Earth-sized, rocky, in the habitable zone
        "lesson": "It sits squarely in the habitable zone and is almost exactly "
        "Earth-sized and rocky. Its red-dwarf star means it is likely tidally "
        "locked, but it is one of the best real candidates for liquid water.",
        "minigame": {"template": "sequence", "config": {
            "prompt": "Confirm the biosphere scan: repeat the life-sign pattern in order.",
            "symbols": ["🌱", "💧", "🌡️", "🧲"],
            "pattern": ["💧", "🌱", "🌡️", "🧲"],
        }},
        "crewNotes": {
            "kirk": "Small, steady, room to breathe. This one feels like it could be home.",
            "spock": "Nearly Earth-radius and within the liquid-water zone; the most promising of the six.",
            "ship": "Radius 0.92 Earth radii. Equilibrium temperature 249.7 Kelvin. Within habitable zone.",
        },
    },
    {
        "id": "kepler_452b",
        "pl_name": "Kepler-452 b",
        "habitable": False,
        "lesson": "It orbits a Sun-like star at nearly Earth's distance, but at "
        "1.6x Earth's radius it may be a 'mini-Neptune' with a crushing, thick "
        "atmosphere rather than solid ground you could stand on.",
        "minigame": {"template": "sort", "config": {
            "prompt": "Sort the clues: does each point to solid rocky ground, or a thick gas envelope?",
            "bins": ["Rocky", "Gassy"],
            "items": [
                {"label": "Radius near 1.6x Earth", "bin": "Gassy"},
                {"label": "Low overall density", "bin": "Gassy"},
                {"label": "High surface gravity, firm crust", "bin": "Rocky"},
                {"label": "Defined solid surface", "bin": "Rocky"},
            ],
        }},
        "crewNotes": {
            "kirk": "Looks like Earth's bigger cousin from orbit — but bigger isn't always better.",
            "spock": "Its size makes a solid surface uncertain; it may lack the rocky ground colonists require.",
            "ship": "Radius 1.63 Earth radii. Insolation 1.1 times Earth. Composition uncertain.",
        },
    },
    {
        "id": "cnc_55e",
        "pl_name": "55 Cnc e",
        "habitable": False,
        "lesson": "It whips around its star in under a day, so close that its "
        "surface is hot enough to melt rock — a lava world, far too hot for "
        "liquid water or life as we know it.",
        "minigame": {"template": "calibrate", "config": {
            "prompt": "Lock the heat-shielded scanner through the glare — stop the marker in the green band.",
            "targetMin": 42, "targetMax": 60, "speed": 0.2,
        }},
        "crewNotes": {
            "kirk": "A world of fire. Nothing's setting up a colony on molten rock.",
            "spock": "Surface temperatures approach 2000 Kelvin; liquid water is impossible.",
            "ship": "Equilibrium temperature 1958 Kelvin. Orbital period 0.74 days. Molten surface probable.",
        },
    },
    {
        "id": "hd_209458b",
        "pl_name": "HD 209458 b",
        "habitable": False,
        "lesson": "A 'hot Jupiter' — a gas giant larger than Jupiter, orbiting so "
        "close that its atmosphere is boiling off into space. There is no solid "
        "surface at all to land on.",
        "minigame": {"template": "calibrate", "config": {
            "prompt": "Hold formation against the escaping-atmosphere turbulence — stop in the green band.",
            "targetMin": 44, "targetMax": 61, "speed": 0.17,
        }},
        "crewNotes": {
            "kirk": "You can't stand on a storm. There's no ground here at all.",
            "spock": "A gas giant with no solid surface; habitation is not possible.",
            "ship": "Radius 15.6 Earth radii. Classification: gas giant. Atmospheric escape detected.",
        },
    },
    {
        "id": "proxima_b",
        "pl_name": "Proxima Cen b",
        "habitable": False,
        "lesson": "The closest exoplanet to Earth, and in its star's habitable "
        "zone — but red dwarfs unleash violent flares and radiation that can "
        "strip a planet's atmosphere away over time.",
        "minigame": {"template": "sort", "config": {
            "prompt": "Sort the defences: which actually shield a colony from stellar-flare radiation?",
            "bins": ["Effective", "Ineffective"],
            "items": [
                {"label": "Strong planetary magnetic field", "bin": "Effective"},
                {"label": "Thick, replenished atmosphere", "bin": "Effective"},
                {"label": "Open surface habitat", "bin": "Ineffective"},
                {"label": "Clear glass dome", "bin": "Ineffective"},
            ],
        }},
        "crewNotes": {
            "kirk": "Close to home and tempting — but that little star has a temper.",
            "spock": "Within the habitable zone, yet frequent stellar flares threaten atmospheric retention.",
            "ship": "Host star M5.5 V. Distance 4.2 light-years. Flare activity: high.",
        },
    },
    {
        "id": "gj_1214b",
        "pl_name": "GJ 1214 b",
        "habitable": False,
        "lesson": "A 'mini-Neptune' likely wrapped in a thick, steamy atmosphere "
        "over a deep global ocean — far more gas and water than solid, habitable "
        "land, and under crushing pressure.",
        "minigame": {"template": "sequence", "config": {
            "prompt": "Tune the sensors through the thick haze: repeat the pattern in order.",
            "symbols": ["◇", "○", "△", "□"],
            "pattern": ["△", "○", "□", "◇"],
        }},
        "crewNotes": {
            "kirk": "All ocean and cloud, no shore. Nowhere to put down roots.",
            "spock": "A dense volatile envelope and extreme pressure make surface habitation impractical.",
            "ship": "Radius 2.73 Earth radii. Classification: mini-Neptune. Thick atmosphere probable.",
        },
    },
]

_BY_PL_NAME = {d["pl_name"]: d for d in EXOPLANETS}

# In-memory caches for this server process.
_planets_cache: list[dict] | None = None
_backdrop_cache: dict | None = None


# ---------------------------------------------------------------------------
# Small HTTP helpers (stdlib only).
# ---------------------------------------------------------------------------
def _get_json(url: str) -> dict | list:
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _download(url: str, dest: Path) -> bool:
    """Best-effort download to a file. Returns True on success."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            data = resp.read()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return True
    except Exception:
        return False


def _read_json_file(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


# ---------------------------------------------------------------------------
# NASA Exoplanet Archive (TAP) — the real specifications.
# ---------------------------------------------------------------------------
def _tap_query(where: str) -> list[dict]:
    """Run one ADQL query against pscomppars and return the rows."""
    adql = f"select {_TAP_FIELDS} from pscomppars where {where}"
    url = _TAP_URL + "?" + urllib.parse.urlencode({"query": adql, "format": "json"})
    data = _get_json(url)
    return data if isinstance(data, list) else []


def _fetch_specs(names: list[str]) -> dict[str, dict]:
    """Fetch specs for all planets in ONE batched query -> {pl_name: row}."""
    quoted = ",".join("'" + n.replace("'", "''") + "'" for n in names)
    rows = _tap_query(f"pl_name in ({quoted})")
    return {row["pl_name"]: row for row in rows if row.get("pl_name")}


# ---------------------------------------------------------------------------
# Turn a raw NASA row into the game's planet schema.
# ---------------------------------------------------------------------------
def _num(value, digits=2):
    if value is None:
        return None
    try:
        return round(float(value), digits)
    except (TypeError, ValueError):
        return value


def _science_from_row(row: dict) -> dict:
    """Readable, student-friendly spec fields (skips anything NASA left blank)."""
    dist_ly = _num(float(row["sy_dist"]) * _PC_TO_LY, 1) if row.get("sy_dist") else None
    pairs = {
        "radius (Earth = 1)": _num(row.get("pl_rade")),
        "mass (Earth = 1)": _num(row.get("pl_bmasse")),
        "orbital distance (AU)": _num(row.get("pl_orbsmax"), 3),
        "orbital period (days)": _num(row.get("pl_orbper")),
        "equilibrium temp (K)": _num(row.get("pl_eqt"), 0),
        "starlight vs Earth": _num(row.get("pl_insol")),
        "host star type": row.get("st_spectype"),
        "star temp (K)": _num(row.get("st_teff"), 0),
        "distance (light-years)": dist_ly,
    }
    return {k: v for k, v in pairs.items() if v is not None and v != ""}


def _fact_from(defn: dict, row: dict) -> str:
    """A habitability fact: real numbers + the authored teaching line."""
    host = row.get("hostname", "its star")
    spec = row.get("st_spectype")
    star = f"{host} ({spec} star)" if spec else host
    bits = [f"{defn['pl_name']} orbits {star}"]
    if row.get("pl_orbsmax") is not None:
        bits.append(f"at {_num(row['pl_orbsmax'], 3)} AU")
    lead = " ".join(bits) + "."
    detail = []
    if row.get("pl_rade") is not None:
        detail.append(f"radius {_num(row['pl_rade'])}x Earth")
    if row.get("pl_eqt") is not None:
        detail.append(f"equilibrium temperature {_num(row['pl_eqt'], 0)} K")
    if row.get("pl_insol") is not None:
        detail.append(f"{_num(row['pl_insol'])}x Earth's sunlight")
    detail_str = ("It has " + ", ".join(detail) + ". ") if detail else ""
    return f"{lead} {detail_str}{defn['lesson']}"


def _assemble(defn: dict, row: dict | None) -> dict:
    """Merge one curated definition with its (live or fallback) NASA row."""
    planet = {
        "id": defn["id"],
        "name": defn["pl_name"],
        "sprite": f"planet_{defn['id']}",
        "habitable": defn["habitable"],
        "minigame": defn["minigame"],
        "crewNotes": defn["crewNotes"],
        "source": "NASA Exoplanet Archive",
    }
    if row:
        planet["science"] = _science_from_row(row)
        planet["fact"] = _fact_from(defn, row)
        planet["disc_year"] = row.get("disc_year")
    else:
        # No data anywhere -> still playable, just without numbers.
        planet["science"] = {}
        planet["fact"] = f"{defn['pl_name']}: {defn['lesson']}"
        planet["disc_year"] = None
    return planet


# ---------------------------------------------------------------------------
# Best-effort imagery (only attempted when the network is confirmed up).
# ---------------------------------------------------------------------------
def _ensure_planet_image(name: str, planet_id: str) -> None:
    dest = _IMG_DIR / f"{planet_id}.png"
    if dest.exists():
        return
    try:
        url = _IMAGES_URL + "?" + urllib.parse.urlencode({"q": name, "media_type": "image"})
        data = _get_json(url)
        items = data.get("collection", {}).get("items", [])
        for item in items:
            links = item.get("links") or []
            if links and links[0].get("href"):
                _download(links[0]["href"], dest)
                return
    except Exception:
        pass  # keep the placeholder; the game never breaks over art


def _ensure_backdrop() -> dict:
    """Fetch today's Astronomy Picture of the Day (uses the api.nasa.gov key)."""
    global _backdrop_cache
    if _backdrop_cache is not None:
        return _backdrop_cache
    result = {"backdrop": None, "apod_title": None}
    try:
        key = os.environ.get("NASA_API_KEY") or "DEMO_KEY"
        url = _APOD_URL + "?" + urllib.parse.urlencode({"api_key": key})
        data = _get_json(url)
        if data.get("media_type") == "image" and data.get("url"):
            if _BACKDROP_PATH.exists() or _download(data["url"], _BACKDROP_PATH):
                result = {
                    "backdrop": "/static/assets/backdrop/apod.jpg",
                    "apod_title": data.get("title"),
                }
    except Exception:
        pass
    _backdrop_cache = result
    return result


# ---------------------------------------------------------------------------
# Public API.
# ---------------------------------------------------------------------------
def build_planets(force: bool = False) -> list[dict]:
    """Return the six planets, enriched with real NASA specs.

    Tries live NASA data; on any failure falls back to the last cached specs,
    then the bundled snapshot -- so this always returns six playable planets.
    """
    global _planets_cache
    if _planets_cache is not None and not force:
        return _planets_cache

    names = [d["pl_name"] for d in EXOPLANETS]
    specs: dict[str, dict] = {}
    live_ok = False
    try:
        specs = _fetch_specs(names)
        live_ok = bool(specs)
        if live_ok:
            _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
            _CACHE_PATH.write_text(json.dumps(specs, indent=2), encoding="utf-8")
    except Exception:
        specs = {}

    if not specs:  # network failed -> last good cache, then bundled snapshot
        specs = _read_json_file(_CACHE_PATH) or _read_json_file(_FALLBACK_PATH) or {}

    planets = [_assemble(d, specs.get(d["pl_name"])) for d in EXOPLANETS]

    # Only reach out for images when we know the network is up (bounds latency).
    if live_ok:
        for d in EXOPLANETS:
            _ensure_planet_image(d["pl_name"], d["id"])

    _planets_cache = planets
    return planets


def get_backdrop() -> dict:
    """{'backdrop': url|None, 'apod_title': str|None} for the Stage 2 backdrop."""
    return _ensure_backdrop()


def lookup_exoplanet(args: dict) -> dict:
    """TOOL HANDLER: let a crew member query the NASA archive live during chat.

    Returns the same {action, args, result} shape as the other ship tools, so it
    plugs straight into the existing agent loop in tools/gemini.py.
    """
    name = (args.get("name") or args.get("planet") or "").strip()
    if not name:
        return {"action": "nasa_lookup", "args": {}, "result": "No planet name was provided to look up."}
    try:
        rows = _tap_query("pl_name = '" + name.replace("'", "''") + "'")
        if not rows:
            return {
                "action": "nasa_lookup",
                "args": {"name": name},
                "result": f"The NASA Exoplanet Archive has no confirmed planet named '{name}'.",
            }
        sci = _science_from_row(rows[0])
        readout = "; ".join(f"{k}: {v}" for k, v in sci.items())
        return {
            "action": "nasa_lookup",
            "args": {"name": name},
            "result": f"NASA Exoplanet Archive data for {name} — {readout}.",
        }
    except Exception:
        return {
            "action": "nasa_lookup",
            "args": {"name": name},
            "result": "The NASA Exoplanet Archive is not reachable right now; rely on the sensor readings already on file.",
        }
