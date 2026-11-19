"""The two practice cases from the session, as plain Python tool functions.

Case #000 "Who drank the last coffee?" is the warm-up game (CASE_CARDS.md) turned into code.
Case #001 "The Vanished Birthday Cake" is copied from detective_lab/case.py (no witnesses, no plot twist),
so this kit works on its own.

Plain functions with type hints and docstrings work in every framework: the docstring is the tool's
description and the type hints are its inputs.
"""

# =============================================================== Case #000
COFFEE_BRIEF = """Case #000: Who drank the last coffee?
It is Monday morning. The office coffee pot is empty, and nobody will admit to drinking the last cup.
Find out who took it, and show your evidence."""

MUG_OWNERS = {"world's best dev mug": "Alex, the workshop facilitator", "red mug": "Sam the intern"}


def coffee_log() -> str:
    """When the coffee machine last made a cup. Input: none."""
    return "Last cup made at 09:10. The pot is now empty."


def desk_cam(time: str) -> str:
    """What the camera at the coffee machine saw at one moment. Input: a time like "09:10"."""
    if time.strip() == "09:10":
        return "One person at the machine, holding a 'World's Best Dev' mug."
    return "Nobody at the machine."


def who_owns(item: str) -> str:
    """Who an object belongs to. Input: an item, like "red mug"."""
    key = item.strip().lower().replace("’", "'").replace("“", "").replace("”", "").strip("'\" ")
    for name, owner in MUG_OWNERS.items():
        if name in key or key in name:
            return f"That item belongs to {owner}."
    return "No owner found."


COFFEE_TOOLS = [coffee_log, desk_cam, who_owns]

# =============================================================== Case #001
CAKE_BRIEF = """Case #001: The Vanished Birthday Cake.
It is Friday afternoon. Priya's birthday cake was in the 3rd-floor kitchen fridge at 14:30.
At 15:15, Sam opened the fridge. The cake was gone.
The party is at 16:00. Find out who took the cake, and show your evidence."""

SUSPECTS = {
    "Sam": "Intern. Always hungry. Found the fridge empty at 15:15.",
    "Chef Marco": "Canteen chef. Said the cake looked 'far too sweet'.",
    "Lee": "Finance team. Says they are on a diet. Booked in a budget meeting all afternoon.",
    "Robo-Clean 3000": "Cleaning robot. Goes everywhere. Sees everything. Says little.",
}
BADGE_LOG = {
    "kitchen": ["12:10 Chef Marco", "14:47 Lee", "15:15 Sam"],
    "meeting_room_b": ["14:28 Lee (in)", "14:31 Priya (in)", "14:40 Lee (out)", "15:05 Lee (in)", "15:30 Priya (out)"],
    "reception": ["14:38 Sam (in)", "15:10 Sam (out)"],
    "rooftop": ["14:55 Lee (in)", "15:02 Lee (out)"],
}
CCTV = {
    "14:30": "Kitchen corridor: empty. Canteen: Chef Marco serving lunch.",
    "14:45": "Canteen: Chef Marco cleaning the grill. Reception: Sam waiting for the pizza delivery.",
    "14:50": "Kitchen corridor: a person in a BLUE JACKET carries a large white box towards the lift. "
             "The box hides their face.",
    "14:55": "Lift display: going UP to floor R (the rooftop).",
    "15:00": "Canteen: Chef Marco closing the kitchen. Reception: Sam paying for six pizzas.",
    "15:15": "Kitchen: Sam opens the fridge, looks shocked, and drops the milk.",
}
CALENDAR = {
    "Lee": "14:30-15:30 Budget meeting (Meeting Room B)",
    "Sam": "14:30-15:15 Collect party pizzas at reception",
    "Chef Marco": "11:30-15:00 Lunch service (Canteen)",
    "Priya": "14:30-15:30 Budget meeting (Meeting Room B). 16:00 'Team catch-up' (Rooftop)",
    "Robo-Clean 3000": "14:00-16:00 Charging (Storeroom)",
}
FINGERPRINTS = {
    "fridge handle": "Chef Marco, Lee, Sam",
    "kitchen door": "Chef Marco, Lee, Priya, Sam",
    "lift button r": "Lee",
    "cake box": "Cannot test: the cake box is missing too.",
}


def list_suspects() -> str:
    """List every suspect with a short note about them."""
    return "\n".join(f"- {name}: {note}" for name, note in SUSPECTS.items())


def read_badge_log(door: str) -> str:
    """See who swiped their badge at a door, and when. door is one of: kitchen, meeting_room_b, reception, rooftop."""
    key = door.strip().lower().replace(" ", "_")
    if key not in BADGE_LOG:
        return f"No badge reader called '{door}'. Doors with readers: {', '.join(BADGE_LOG)}."
    return f"Badge swipes at {key}: " + "; ".join(BADGE_LOG[key])


def check_cctv(time: str) -> str:
    """See what the office cameras recorded at one moment. Write the time as HH:MM, like 14:50.
    Footage exists for 14:30, 14:45, 14:50, 14:55, 15:00 and 15:15."""
    t = time.strip().replace(".", ":")
    if len(t) == 4 and t[1] == ":":
        t = "0" + t
    if t not in CCTV:
        return f"No footage at '{time}'. Footage exists for: {', '.join(CCTV)}."
    return f"CCTV {t}: {CCTV[t]}"


def check_calendar(person: str) -> str:
    """Read one person's calendar for Friday afternoon: where they SAID they would be. Use a name, like Lee."""
    for name, entry in CALENDAR.items():
        if person.strip().lower() in name.lower():
            return f"{name}'s calendar: {entry}"
    return f"No calendar for '{person}'. People: {', '.join(CALENDAR)}."


def check_fingerprints(item: str) -> str:
    """Whose fingerprints are on an item: fridge handle, kitchen door, lift button r, or cake box."""
    key = item.strip().lower()
    if key not in FINGERPRINTS:
        return f"No prints taken from '{item}'. Items tested: {', '.join(FINGERPRINTS)}."
    return f"Fingerprints on {key}: {FINGERPRINTS[key]}"


CAKE_TOOLS = [list_suspects, read_badge_log, check_cctv, check_calendar, check_fingerprints]
