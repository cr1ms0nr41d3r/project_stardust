# tools/knowledge.py
# ---------------------------------------------------------------------------
# The KNOWLEDGE loader for Stage 2. When the player asks the crew about a
# planet, we hand the LLM a short block of facts about THAT planet so the
# answer is in-context. The planet data comes from tools/nasa.py, which builds
# the six worlds from REAL, LIVE NASA Exoplanet Archive data -- the SAME source
# the browser gets from GET /planets, so there is one source of truth.
#
# IMPORTANT: we deliberately STRIP the `habitable` flag before building the
# context. The crew help the player reason about habitability, but must never
# blurt out which world is the correct answer -- that's the puzzle. (The crew
# can also query NASA live via the `lookup_exoplanet` tool -- see tools/nasa.py.)
# ---------------------------------------------------------------------------

from tools.nasa import build_planets


def load_planets() -> dict[str, dict]:
    """Return {planet_id: planet_dict} from the live NASA-backed builder."""
    return {p["id"]: p for p in build_planets()}


def build_planet_context(planet_id: str | None, character: str | None = None) -> str:
    """Return a short fact block about one planet for the LLM system prompt.

    Returns "" when no planet is supplied (so general Stage 2 chat still works).
    The `habitable` flag is removed so the crew never reveal the answer. If a
    `character` is given, that crew member's private note is included too.
    """
    if not planet_id:
        return ""

    planet = load_planets().get(planet_id)
    if planet is None:
        return ""

    lines = [
        "\n\n--- CURRENT SURVEY TARGET (real data from the NASA Exoplanet "
        "Archive; use it to answer, but NEVER state which planet is 'the most "
        "habitable' or 'the correct choice' -- let the player reason it out. You "
        "may call the lookup_exoplanet tool for more detail on any world) ---",
        f"Name: {planet['name']}",
        f"Known fact: {planet['fact']}",
        "Sensor readings (NASA Exoplanet Archive):",
    ]
    for key, value in planet.get("science", {}).items():
        lines.append(f"  - {key.replace('_', ' ')}: {value}")

    # A private, in-character note for THIS crew member, if we have one.
    note = (planet.get("crewNotes") or {}).get(character or "")
    if note:
        lines.append(f"Your own read on this world: {note}")

    return "\n".join(lines)
