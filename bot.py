"""
Spice and Dice - A pepper farming & casino Discord bot
Grow peppers, cultivate strains, gamble your gold, dodge the feds!
"""

import sys
import io

# Fix Windows console encoding for emoji output
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import discord
from discord import app_commands
from discord.ext import commands, tasks
import json
import os
import time
import random
import math
import asyncio
from pathlib import Path

# ─── Config ───────────────────────────────────────────────────────────────────

_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

TOKEN = os.getenv("DISCORD_TOKEN", "")
DATA_DIR = Path(__file__).parent / "data"
ASSETS_DIR = Path(__file__).parent / "assets"
DATA_DIR.mkdir(exist_ok=True)

# ─── Pepper Types ─────────────────────────────────────────────────────────────

PEPPERS = {
    "green": {
        "name": "Green Pep",
        "emoji": "🫑",
        "seed_cost": 10,
        "sell_price": 25,
        "grow_time": 60 * 5,         # 5 min
        "description": "A crunchy lil' garden pepper. Fresh off the vine!",
        "rarity": "Common",
    },
    "red": {
        "name": "Red Pep",
        "emoji": "🌶️",
        "seed_cost": 25,
        "sell_price": 60,
        "grow_time": 60 * 10,        # 10 min
        "description": "Spicy!! This one's got some kick to it.",
        "rarity": "Uncommon",
    },
    "yellow": {
        "name": "Yellow Pep",
        "emoji": "💛",
        "seed_cost": 50,
        "sell_price": 130,
        "grow_time": 60 * 20,        # 20 min
        "description": "Sweet and tangy. The townsfolk love these in salads.",
        "rarity": "Rare",
    },
    "golden": {
        "name": "Golden Pep",
        "emoji": "✨",
        "seed_cost": 200,
        "sell_price": 500,
        "grow_time": 60 * 60,        # 60 min
        "description": "A legendary pepper that glows in the moonlight... worth a fortune!",
        "rarity": "Legendary",
    },
    "pumpkin": {
        "name": "Pumpkin",
        "emoji": "🎃",
        "seed_cost": 40,
        "sell_price": 100,
        "grow_time": 60 * 15,        # 15 min
        "description": "Big ol' orange beauty. Great for pies and profit!",
        "rarity": "Common",
    },
    "corn": {
        "name": "Sweet Corn",
        "emoji": "🌽",
        "seed_cost": 15,
        "sell_price": 35,
        "grow_time": 60 * 8,         # 8 min
        "description": "Simple, reliable, and always sells. A farmer's best friend.",
        "rarity": "Common",
    },
    "tomato": {
        "name": "Tomato",
        "emoji": "🍅",
        "seed_cost": 20,
        "sell_price": 50,
        "grow_time": 60 * 10,        # 10 min
        "description": "Juicy and ripe! The townspeople can't get enough of these.",
        "rarity": "Uncommon",
    },
}

# ─── Cannabis Strains ─────────────────────────────────────────────────────────

STRAINS = {
    "chill_leaf": {
        "name": "Chill Leaf",
        "emoji": "🌿",
        "seed_cost": 75,
        "sell_price": 200,
        "grow_time": 60 * 20,        # 20 min
        "description": "Mellow indica vibes. Easy to grow, smooth to sell.",
        "rarity": "Common Strain",
        "raid_chance": 0.05,
    },
    "purple_haze": {
        "name": "Purple Haze",
        "emoji": "💜",
        "seed_cost": 150,
        "sell_price": 450,
        "grow_time": 60 * 45,        # 45 min
        "description": "Sticky purple buds with a sweet aroma. High demand on the streets.",
        "rarity": "Rare Strain",
        "raid_chance": 0.10,
    },
    "golden_kush": {
        "name": "Golden Kush",
        "emoji": "👑",
        "seed_cost": 400,
        "sell_price": 1200,
        "grow_time": 60 * 90,        # 90 min (max)
        "description": "The legendary strain. One whiff and the whole block knows. Insane profit, insane risk.",
        "rarity": "Legendary Strain",
        "raid_chance": 0.18,
    },
}

# ─── Raid Protection Items ────────────────────────────────────────────────────

PROTECTION_ITEMS = {
    "guard_dog": {
        "name": "Guard Dog",
        "emoji": "🐕",
        "cost": 300,
        "raid_reduction": 0.30,     # Reduces raid chance by 30%
        "duration": 60 * 60 * 6,    # 6 hours
        "description": "A loyal pup that barks at strangers. Reduces raid chance by 30%.",
    },
    "security_cam": {
        "name": "Security Camera",
        "emoji": "📷",
        "cost": 500,
        "raid_reduction": 0.50,     # 50% reduction
        "duration": 60 * 60 * 12,   # 12 hours
        "description": "Keeps an eye on the perimeter. Reduces raid chance by 50%.",
    },
    "bribe": {
        "name": "Bribe the Sheriff",
        "emoji": "💵",
        "cost": 1000,
        "raid_reduction": 0.90,     # 90% reduction
        "duration": 60 * 60 * 4,    # 4 hours
        "description": "Slip the sheriff a fat envelope. Almost immune to raids for 4 hours.",
    },
}

MAX_PLOTS = 6
MAX_GROW_PLOTS = 4  # Cannabis plots
STARTING_GOLD = 100

# ─── Weather System ──────────────────────────────────────────────────────────

WEATHER_TYPES = {
    "sunny": {
        "name": "Sunny", "emoji": "☀️",
        "grow_modifier": 1.0, "sell_modifier": 1.0,
        "description": "Clear skies and warm sun. A perfect day for farmin'!",
        "flavor": "The sun's beatin' down nice and warm!",
        "weight": 35,
    },
    "rainy": {
        "name": "Rainy", "emoji": "🌧️",
        "grow_modifier": 0.75, "sell_modifier": 1.0,
        "description": "Rain waters the crops! Growth speed +25%.",
        "flavor": "Pitter-patter on the leaves~ Crops are drinkin' it up!",
        "weight": 25,
    },
    "stormy": {
        "name": "Stormy", "emoji": "⛈️",
        "grow_modifier": 0.6, "sell_modifier": 0.85,
        "description": "Storms speed growth +40%, but sell prices drop 15%.",
        "flavor": "Thunder across the valley... crops grow wild in this weather!",
        "weight": 10,
    },
    "windy": {
        "name": "Windy", "emoji": "💨",
        "grow_modifier": 1.1, "sell_modifier": 1.15,
        "description": "Wind slows growth 10%, but sell prices rise 15%!",
        "flavor": "Hold onto your hat! The wind's howlin'!",
        "weight": 15,
    },
    "heatwave": {
        "name": "Heat Wave", "emoji": "🔥",
        "grow_modifier": 0.85, "sell_modifier": 1.25,
        "description": "Faster growth +15% AND sell prices up 25%! Lucky day!",
        "flavor": "It's HOT! Crops practically jump outta the ground!",
        "weight": 8,
    },
    "foggy": {
        "name": "Foggy", "emoji": "🌫️",
        "grow_modifier": 1.2, "sell_modifier": 1.0,
        "description": "Thick fog slows growth 20%. Good cover for... operations.",
        "flavor": "Can barely see the farm... spooky, but good for hidin' things.",
        "raid_bonus": -0.03,  # Fog LOWERS raid chance slightly
        "weight": 7,
    },
}

WEATHER_CYCLE_SECONDS = 60 * 120

# ─── Rare Events ─────────────────────────────────────────────────────────────

RARE_EVENTS = {
    "golden_rain": {
        "name": "Golden Rain", "emoji": "🌟", "chance": 0.03,
        "description": "Shimmering golden droplets fall from the sky!",
        "effect": "A bonus golden pepper added to inventory.",
        "flavor": "The sky turns golden... droplets of pure magic fall on your crops!",
    },
    "pepper_fairy": {
        "name": "Pepper Fairy Visit", "emoji": "🧚", "chance": 0.05,
        "description": "A tiny fairy sprinkles magic dust on your crops!",
        "effect": "One random growing pepper instantly finishes.",
        "flavor": "A tiny glowing fairy waves her wand and *poof!* — one pepper is fully grown!",
    },
    "merchant_caravan": {
        "name": "Merchant Caravan", "emoji": "🐫", "chance": 0.04,
        "description": "A traveling merchant passes through!",
        "effect": "Bonus 50-200g gold.",
        "flavor": "A merchant tosses you a pouch of gold. 'For the best farmer in the valley!'",
    },
    "crop_surge": {
        "name": "Crop Surge", "emoji": "⚡", "chance": 0.04,
        "description": "Mysterious energy surges through the soil!",
        "effect": "All growing crops get 30% time shaved off.",
        "flavor": "The ground trembles... a wave of green energy pulses through your fields!",
    },
    "rainbow": {
        "name": "Rainbow Blessing", "emoji": "🌈", "chance": 0.02,
        "description": "A double rainbow appears over your farm!",
        "effect": "Next harvest sale is worth double gold.",
        "flavor": "A brilliant double rainbow arcs over your farm! You feel incredibly lucky!",
    },
    "crow_attack": {
        "name": "Crow Attack", "emoji": "🐦‍⬛", "chance": 0.03,
        "description": "Pesky crows swoop in!",
        "effect": "One random growing crop loses 20% progress.",
        "flavor": "CAW CAW! Crows dive-bomb your field before the scarecrow chases 'em off!",
    },
    "wishing_star": {
        "name": "Wishing Star", "emoji": "💫", "chance": 0.01,
        "description": "A shooting star streaks across the sky!",
        "effect": "500g gold and a free Golden Pep.",
        "flavor": "A star shoots across the sky... 500g appears in your pocket and a golden seed in your field!",
    },
}

# ─── Blackjack Card Helpers ──────────────────────────────────────────────────

SUITS = ["♠️", "♥️", "♦️", "♣️"]
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

def make_deck():
    return [(r, s) for s in SUITS for r in RANKS]

def card_value(card):
    r = card[0]
    if r in ("J", "Q", "K"):
        return 10
    if r == "A":
        return 11
    return int(r)

def hand_value(hand):
    total = sum(card_value(c) for c in hand)
    aces = sum(1 for c in hand if c[0] == "A")
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total

def format_card(card):
    return f"`{card[0]}{card[1]}`"

def format_hand(hand):
    return " ".join(format_card(c) for c in hand)

# ─── Roulette Helpers ────────────────────────────────────────────────────────

ROULETTE_REDS = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
ROULETTE_BLACKS = {2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35}

def roulette_color(num):
    if num == 0:
        return "green"
    return "red" if num in ROULETTE_REDS else "black"

def roulette_emoji(num):
    c = roulette_color(num)
    if c == "green":
        return "🟢"
    elif c == "red":
        return "🔴"
    return "⚫"

# ─── Flavor Text ─────────────────────────────────────────────────────────────

GREETINGS = [
    "Yo, what's good! Ready to hustle some spice?",
    "Welcome back, grower! The fields are callin'.",
    "Mornin' farmer! The soil's lookin' prime today.",
    "Hey there, partner! Let's get this bread... and these peppers.",
    "The valley's quiet... perfect for farmin' and gamblin'!",
    "Another day, another harvest. Let's roll!",
    "The scarecrow says hi! ...Okay, I said hi. Let's get growin'!",
    "Spice and Dice, baby! What's the play today?",
]

HARVEST_MESSAGES = [
    "You plucked {count}x {name} right off the vine! Nice haul!",
    "Fresh {name}! {count} beauties, ready for the market!",
    "{count}x {name} harvested! The farm's really producin'!",
    "What a crop! {count}x {name} added to your stash!",
]

PLANT_MESSAGES = [
    "Seeds in the ground! Now we wait~",
    "Planted! Give 'em time and they'll grow up strong.",
    "Into the soil they go! Patience, friend.",
    "Seeds are set! Got a good feelin' about this batch.",
]

SELL_MESSAGES = [
    "Sold! Ka-ching! +{gold}g!",
    "The buyer's eyes lit up! +{gold}g!",
    "Good business! +{gold}g in the register!",
    "Sold to the highest bidder! +{gold}g!",
]

RAID_MESSAGES = [
    "🚔 **RAID!** The feds kicked down the door! They seized {lost} bud(s) from your grow room!",
    "🚨 **BUSTED!** Cops swarmed the farm! {lost} bud(s) confiscated!",
    "👮 **FARM RAID!** You hear sirens... too late to hide {lost} bud(s)!",
    "🔴 **THE HEAT!** Sheriff's department raided your operation! {lost} bud(s) gone!",
]

RAID_DODGE_MESSAGES = [
    "🚔 Cops rolled by... but your {protection} kept 'em moving! Close call!",
    "👮 The sheriff glanced your way, but {protection} saved you. Phew!",
    "🚨 Sirens in the distance... {protection} did its job. You're safe... for now.",
]

BROKE_MESSAGES = [
    "Pockets are light for that one, friend.",
    "Not enough gold! Sell somethin' first.",
    "Few coins short... hustle harder!",
    "Can't afford that... sell some harvest first!",
]

NO_PLOTS_MESSAGES = [
    "All plots are full! Wait for harvest~",
    "No empty plots! Farm's bustlin'!",
    "Every plot is spoken for! Patience!",
]

# ─── Data Persistence ─────────────────────────────────────────────────────────

GLOBAL_DATA_PATH = DATA_DIR / "_global.json"

def load_global() -> dict:
    if GLOBAL_DATA_PATH.exists():
        with open(GLOBAL_DATA_PATH, "r") as f:
            return json.load(f)
    return {"weather": "sunny", "weather_changed_at": time.time()}

def save_global(data: dict):
    with open(GLOBAL_DATA_PATH, "w") as f:
        json.dump(data, f, indent=2)

def get_data_path(user_id: int) -> Path:
    return DATA_DIR / f"{user_id}.json"

def load_user(user_id: int) -> dict:
    path = get_data_path(user_id)
    if path.exists():
        with open(path, "r") as f:
            data = json.load(f)
        # Migrate
        data.setdefault("gold", STARTING_GOLD)
        data.setdefault("inventory", {"green": 0, "red": 0, "yellow": 0, "golden": 0, "pumpkin": 0, "corn": 0, "tomato": 0})
        data.setdefault("bud_inventory", {"chill_leaf": 0, "purple_haze": 0, "golden_kush": 0})
        data.setdefault("plots", [])
        data.setdefault("grow_plots", [])
        data.setdefault("protections", [])
        data.setdefault("total_harvested", 0)
        data.setdefault("total_sold", 0)
        data.setdefault("total_earned", 0)
        data.setdefault("buds_harvested", 0)
        data.setdefault("buds_sold", 0)
        data.setdefault("buds_lost_to_raids", 0)
        data.setdefault("raids_dodged", 0)
        data.setdefault("casino_wins", 0)
        data.setdefault("casino_losses", 0)
        data.setdefault("casino_profit", 0)
        data.setdefault("rare_events_seen", [])
        data.setdefault("rainbow_active", False)
        data.setdefault("display_name", "Farmer")
        return data
    data = {
        "gold": STARTING_GOLD,
        "inventory": {"green": 0, "red": 0, "yellow": 0, "golden": 0, "pumpkin": 0, "corn": 0, "tomato": 0},
        "bud_inventory": {"chill_leaf": 0, "purple_haze": 0, "golden_kush": 0},
        "plots": [],
        "grow_plots": [],
        "protections": [],
        "total_harvested": 0, "total_sold": 0, "total_earned": 0,
        "buds_harvested": 0, "buds_sold": 0, "buds_lost_to_raids": 0,
        "raids_dodged": 0,
        "casino_wins": 0, "casino_losses": 0, "casino_profit": 0,
        "rare_events_seen": [],
        "rainbow_active": False,
        "display_name": "Farmer",
    }
    save_user(user_id, data)
    return data

def save_user(user_id: int, data: dict):
    with open(get_data_path(user_id), "w") as f:
        json.dump(data, f, indent=2)

def get_all_users() -> list:
    users = []
    for f in DATA_DIR.glob("*.json"):
        if f.name.startswith("_"):
            continue
        try:
            uid = int(f.stem)
            with open(f, "r") as fh:
                users.append((uid, json.load(fh)))
        except (ValueError, json.JSONDecodeError):
            continue
    return users

# ─── Poker Game State (in-memory) ────────────────────────────────────────────

# Active poker tables: channel_id -> PokerTable
poker_tables = {}

class PokerTable:
    def __init__(self, channel_id, buy_in):
        self.channel_id = channel_id
        self.buy_in = buy_in
        self.players = {}       # user_id -> {"hand": [], "bet": int, "folded": bool, "name": str}
        self.deck = []
        self.community = []
        self.pot = 0
        self.phase = "waiting"  # waiting, preflop, flop, turn, river, showdown
        self.current_turn = 0
        self.turn_order = []
        self.message = None     # Discord message to edit
        self.min_raise = buy_in // 5
        self.started = False

    def add_player(self, user_id, name):
        if user_id in self.players:
            return False
        self.players[user_id] = {
            "hand": [], "bet": 0, "folded": False, "name": name,
            "total_bet": 0,
        }
        return True

    def start_game(self):
        self.deck = make_deck()
        random.shuffle(self.deck)
        self.community = []
        self.pot = len(self.players) * self.buy_in
        self.turn_order = list(self.players.keys())
        random.shuffle(self.turn_order)
        for uid in self.players:
            self.players[uid]["hand"] = [self.deck.pop(), self.deck.pop()]
            self.players[uid]["folded"] = False
            self.players[uid]["bet"] = 0
            self.players[uid]["total_bet"] = self.buy_in
        self.phase = "preflop"
        self.current_turn = 0
        self.started = True

    def deal_community(self):
        if self.phase == "preflop":
            self.community = [self.deck.pop() for _ in range(3)]
            self.phase = "flop"
        elif self.phase == "flop":
            self.community.append(self.deck.pop())
            self.phase = "turn"
        elif self.phase == "turn":
            self.community.append(self.deck.pop())
            self.phase = "river"
        # Reset bets for new round
        for uid in self.players:
            self.players[uid]["bet"] = 0
        self.current_turn = 0

    def active_players(self):
        return [uid for uid in self.turn_order if not self.players[uid]["folded"]]

    def current_player_id(self):
        active = self.active_players()
        if not active:
            return None
        return active[self.current_turn % len(active)]

    def advance_turn(self):
        active = self.active_players()
        if len(active) <= 1:
            self.phase = "showdown"
            return
        self.current_turn += 1
        if self.current_turn >= len(active):
            # Everyone has acted — advance phase
            if self.phase == "river":
                self.phase = "showdown"
            else:
                self.deal_community()

    def evaluate_hand(self, uid):
        """Simple hand evaluator — returns (score, description)."""
        hand = self.players[uid]["hand"] + self.community
        ranks = [card_value(c) for c in hand]
        rank_counts = {}
        for r in ranks:
            rank_counts[r] = rank_counts.get(r, 0) + 1

        pairs = sum(1 for c in rank_counts.values() if c == 2)
        trips = sum(1 for c in rank_counts.values() if c == 3)
        quads = sum(1 for c in rank_counts.values() if c == 4)

        if quads:
            return (7, "Four of a Kind")
        if trips and pairs:
            return (6, "Full House")
        # Simple flush check
        suit_counts = {}
        for c in hand:
            suit_counts[c[1]] = suit_counts.get(c[1], 0) + 1
        has_flush = any(v >= 5 for v in suit_counts.values())
        # Simple straight check
        unique_ranks = sorted(set(ranks))
        has_straight = False
        for i in range(len(unique_ranks) - 4):
            if unique_ranks[i+4] - unique_ranks[i] == 4:
                has_straight = True
        if has_flush and has_straight:
            return (8, "Straight Flush")
        if has_flush:
            return (5, "Flush")
        if has_straight:
            return (4, "Straight")
        if trips:
            return (3, "Three of a Kind")
        if pairs >= 2:
            return (2, "Two Pair")
        if pairs == 1:
            return (1, "Pair")
        return (0, "High Card: " + str(max(ranks)))


# ─── Weather Logic ───────────────────────────────────────────────────────────

def get_current_weather() -> dict:
    g = load_global()
    now = time.time()
    if now - g.get("weather_changed_at", 0) >= WEATHER_CYCLE_SECONDS:
        types = list(WEATHER_TYPES.keys())
        weights = [WEATHER_TYPES[t]["weight"] for t in types]
        g["weather"] = random.choices(types, weights=weights, k=1)[0]
        g["weather_changed_at"] = now
        save_global(g)
    w = WEATHER_TYPES[g.get("weather", "sunny")].copy()
    w["key"] = g.get("weather", "sunny")
    w["time_remaining"] = max(0, WEATHER_CYCLE_SECONDS - (now - g.get("weather_changed_at", 0)))
    return w

def get_weather_time_str(weather: dict) -> str:
    r = weather["time_remaining"]
    return f"{r/3600:.1f}h" if r > 3600 else f"{r/60:.0f}m" if r > 60 else f"{r:.0f}s"


# ─── Raid Logic ──────────────────────────────────────────────────────────────

def get_raid_reduction(data: dict) -> float:
    """Get total raid chance reduction from active protections."""
    now = time.time()
    total = 0.0
    active = []
    for p in data.get("protections", []):
        if now < p["expires_at"]:
            total += p["reduction"]
            active.append(p)
    data["protections"] = active
    return min(total, 0.95)  # Cap at 95% reduction

def get_active_protection_name(data: dict) -> str:
    now = time.time()
    names = []
    for p in data.get("protections", []):
        if now < p["expires_at"]:
            item = PROTECTION_ITEMS.get(p["type"])
            if item:
                names.append(f"{item['emoji']} {item['name']}")
    return ", ".join(names) if names else None

def check_raid(data: dict) -> dict | None:
    """Check if a raid happens. Returns raid info or None."""
    growing_buds = [p for p in data.get("grow_plots", [])]
    if not growing_buds:
        return None

    # Calculate max raid chance from what's growing
    max_raid = max(STRAINS[p["strain"]]["raid_chance"] for p in growing_buds)
    reduction = get_raid_reduction(data)
    final_chance = max_raid * (1.0 - reduction)

    if random.random() < final_chance:
        if reduction > 0.5 and random.random() < 0.5:
            # Protection saved you sometimes even when raid triggers at low chance
            prot_name = get_active_protection_name(data)
            if prot_name:
                data["raids_dodged"] = data.get("raids_dodged", 0) + 1
                return {"dodged": True, "protection": prot_name}

        # Raid happens! Lose a random growing bud
        if growing_buds:
            victim_idx = random.randint(0, len(data["grow_plots"]) - 1)
            lost_strain = data["grow_plots"].pop(victim_idx)
            data["buds_lost_to_raids"] = data.get("buds_lost_to_raids", 0) + 1
            return {
                "dodged": False,
                "lost_strain": lost_strain["strain"],
                "lost_name": STRAINS[lost_strain["strain"]]["name"],
            }
    return None


# ─── Rare Events Logic ──────────────────────────────────────────────────────

def roll_rare_event(data: dict) -> dict | None:
    for ek, ev in RARE_EVENTS.items():
        if random.random() < ev["chance"]:
            return apply_rare_event(ek, ev, data)
    return None

def apply_rare_event(ek, ev, data):
    result = {"key": ek, "name": ev["name"], "emoji": ev["emoji"], "flavor": ev["flavor"], "effect_msg": ""}
    data.setdefault("rare_events_seen", [])
    data["rare_events_seen"].append({"event": ek, "time": time.time()})
    data["rare_events_seen"] = data["rare_events_seen"][-20:]

    if ek == "golden_rain":
        data["inventory"]["golden"] = data["inventory"].get("golden", 0) + 1
        result["effect_msg"] = "✨ +1 Golden Pep!"
    elif ek == "pepper_fairy":
        growing = [i for i, p in enumerate(data["plots"])
                   if time.time() - p["planted_at"] < PEPPERS[p["pepper"]]["grow_time"]]
        if growing:
            idx = random.choice(growing)
            pt = data["plots"][idx]["pepper"]
            data["plots"][idx]["planted_at"] = time.time() - PEPPERS[pt]["grow_time"] - 1
            result["effect_msg"] = f"🧚 {PEPPERS[pt]['name']} is now fully grown!"
        else:
            data["gold"] += 25
            result["effect_msg"] = "🧚 No crops to boost... +25g fairy dust!"
    elif ek == "merchant_caravan":
        bonus = random.randint(50, 200)
        data["gold"] += bonus
        result["effect_msg"] = f"💰 +**{bonus}g** from the merchant!"
    elif ek == "crop_surge":
        surged = 0
        now = time.time()
        for plot in data["plots"] + data.get("grow_plots", []):
            key = "pepper" if "pepper" in plot else "strain"
            table = PEPPERS if key == "pepper" else STRAINS
            gt = table[plot[key]]["grow_time"]
            rem = gt - (now - plot["planted_at"])
            if rem > 0:
                plot["planted_at"] -= rem * 0.30
                surged += 1
        result["effect_msg"] = f"⚡ {surged} crop(s) surged 30%!" if surged else "⚡ No growing crops to surge."
    elif ek == "rainbow":
        data["rainbow_active"] = True
        result["effect_msg"] = "🌈 Next sale = **DOUBLE** gold!"
    elif ek == "crow_attack":
        all_growing = [(i, "plots") for i, p in enumerate(data["plots"])
                       if time.time() - p["planted_at"] < PEPPERS[p["pepper"]]["grow_time"]]
        if all_growing:
            idx, src = random.choice(all_growing)
            pt = data["plots"][idx]["pepper"]
            data["plots"][idx]["planted_at"] += PEPPERS[pt]["grow_time"] * 0.20
            result["effect_msg"] = f"🐦‍⬛ Crow pecked your {PEPPERS[pt]['name']}! Lost progress..."
        else:
            result["effect_msg"] = "🐦‍⬛ Crows circled but fields were empty!"
    elif ek == "wishing_star":
        data["gold"] += 500
        if len(data["plots"]) < MAX_PLOTS:
            data["plots"].append({"pepper": "golden", "planted_at": time.time()})
            result["effect_msg"] = "💫 +500g AND Golden Pep seed planted!"
        else:
            data["inventory"]["golden"] = data["inventory"].get("golden", 0) + 1
            result["effect_msg"] = "💫 +500g AND Golden Pep in your basket!"
    return result


# ─── Game Logic Helpers ───────────────────────────────────────────────────────

def check_harvests(data: dict) -> dict:
    weather = get_current_weather()
    gm = weather["grow_modifier"]
    now = time.time()
    harvested = {}
    remaining = []
    for plot in data["plots"]:
        pt = plot["pepper"]
        if now - plot["planted_at"] >= PEPPERS[pt]["grow_time"] * gm:
            harvested[pt] = harvested.get(pt, 0) + 1
            data["inventory"][pt] = data["inventory"].get(pt, 0) + 1
            data["total_harvested"] = data.get("total_harvested", 0) + 1
        else:
            remaining.append(plot)
    data["plots"] = remaining
    return harvested

def check_bud_harvests(data: dict) -> dict:
    weather = get_current_weather()
    gm = weather["grow_modifier"]
    now = time.time()
    harvested = {}
    remaining = []
    for plot in data.get("grow_plots", []):
        st = plot["strain"]
        if now - plot["planted_at"] >= STRAINS[st]["grow_time"] * gm:
            harvested[st] = harvested.get(st, 0) + 1
            data["bud_inventory"][st] = data["bud_inventory"].get(st, 0) + 1
            data["buds_harvested"] = data.get("buds_harvested", 0) + 1
        else:
            remaining.append(plot)
    data["grow_plots"] = remaining
    return harvested

def get_plot_status(plot: dict, is_bud=False) -> str:
    weather = get_current_weather()
    gm = weather["grow_modifier"]
    now = time.time()
    if is_bud:
        key = plot["strain"]
        info = STRAINS[key]
    else:
        key = plot["pepper"]
        info = PEPPERS[key]
    elapsed = now - plot["planted_at"]
    egt = info["grow_time"] * gm
    progress = min(elapsed / egt, 1.0)

    if progress >= 1.0:
        return f"{info['emoji']} **READY!**"

    bar_len = 10
    filled = int(progress * bar_len)
    bar = "█" * filled + "░" * (bar_len - filled)
    rem = egt - elapsed
    ts = f"{rem/3600:.1f}h" if rem > 3600 else f"{rem/60:.0f}m" if rem > 60 else f"{rem:.0f}s"
    stage = "🌱" if progress < 0.25 else "🌿" if progress < 0.5 else "🪴" if progress < 0.75 else "🌳"
    return f"{stage} {info['name']} [{bar}] {int(progress*100)}% — {ts}"

def format_gold(amount: int) -> str:
    return f"**{amount:,}**g"

def get_effective_sell_price(pepper_type: str) -> int:
    w = get_current_weather()
    return int(PEPPERS[pepper_type]["sell_price"] * w["sell_modifier"])

def get_effective_bud_price(strain_type: str) -> int:
    w = get_current_weather()
    return int(STRAINS[strain_type]["sell_price"] * w["sell_modifier"])

def format_time(seconds: int) -> str:
    h = seconds / 3600
    if h >= 1:
        return f"{h:.1f}h" if h != int(h) else f"{int(h)}h"
    return f"{seconds // 60}m"

# ─── Bot Setup ────────────────────────────────────────────────────────────────

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# ─── Dashboard View ──────────────────────────────────────────────────────────

class DashboardView(discord.ui.View):
    def __init__(self, uid):
        super().__init__(timeout=180)
        self.uid = uid

    async def _check(self, i):
        if i.user.id != self.uid:
            await i.response.send_message("Use `/pep` for your own dashboard!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🌾 Farm", style=discord.ButtonStyle.green, row=0)
    async def farm_btn(self, i, b):
        if not await self._check(i): return
        d = load_user(self.uid)
        h = check_harvests(d)
        ev = roll_rare_event(d)
        save_user(self.uid, d)
        await i.response.edit_message(embed=build_farm_embed(d, h, i.user, rare_event=ev), view=FarmView(self.uid))

    @discord.ui.button(label="🪴 Grow Op", style=discord.ButtonStyle.green, row=0)
    async def grow_btn(self, i, b):
        if not await self._check(i): return
        d = load_user(self.uid)
        bh = check_bud_harvests(d)
        raid = check_raid(d)
        save_user(self.uid, d)
        await i.response.edit_message(embed=build_grow_embed(d, bh, i.user, raid_result=raid), view=GrowView(self.uid))

    @discord.ui.button(label="🏪 Store", style=discord.ButtonStyle.blurple, row=0)
    async def store_btn(self, i, b):
        if not await self._check(i): return
        d = load_user(self.uid)
        check_harvests(d); save_user(self.uid, d)
        await i.response.edit_message(embed=build_store_embed(d, i.user), view=StoreView(self.uid))

    @discord.ui.button(label="📦 Sell", style=discord.ButtonStyle.danger, row=1)
    async def inv_btn(self, i, b):
        if not await self._check(i): return
        d = load_user(self.uid)
        check_harvests(d); check_bud_harvests(d); save_user(self.uid, d)
        await i.response.edit_message(embed=build_inventory_embed(d, i.user), view=InventoryView(self.uid))

    @discord.ui.button(label="🎰 Casino", style=discord.ButtonStyle.blurple, row=1)
    async def casino_btn(self, i, b):
        if not await self._check(i): return
        d = load_user(self.uid)
        await i.response.edit_message(embed=build_casino_embed(d, i.user), view=CasinoView(self.uid))

    @discord.ui.button(label="📋 Menu", style=discord.ButtonStyle.grey, row=1)
    async def menu_btn_dash(self, i, b):
        if not await self._check(i): return
        d = load_user(self.uid)
        await i.response.edit_message(embed=build_menu_embed(d, i.user), view=MenuView(self.uid))

    @discord.ui.button(label="❌ Close", style=discord.ButtonStyle.danger, row=2)
    async def close_btn(self, i, b):
        if not await self._check(i): return
        await i.message.delete()

# ─── Farm View ───────────────────────────────────────────────────────────────

class FarmView(discord.ui.View):
    def __init__(self, uid):
        super().__init__(timeout=180)
        self.uid = uid

    async def _check(self, i):
        if i.user.id != self.uid:
            await i.response.send_message("Not your farm!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🫑 Green", style=discord.ButtonStyle.green, row=0)
    async def p_green(self, i, b): await self._plant(i, "green")
    @discord.ui.button(label="🌶️ Red", style=discord.ButtonStyle.red, row=0)
    async def p_red(self, i, b): await self._plant(i, "red")
    @discord.ui.button(label="💛 Yellow", style=discord.ButtonStyle.grey, row=0)
    async def p_yellow(self, i, b): await self._plant(i, "yellow")
    @discord.ui.button(label="✨ Golden", style=discord.ButtonStyle.blurple, row=0)
    async def p_golden(self, i, b): await self._plant(i, "golden")

    @discord.ui.button(label="🎃 Pumpkin", style=discord.ButtonStyle.grey, row=1)
    async def p_pumpkin(self, i, b): await self._plant(i, "pumpkin")
    @discord.ui.button(label="🌽 Corn", style=discord.ButtonStyle.green, row=1)
    async def p_corn(self, i, b): await self._plant(i, "corn")
    @discord.ui.button(label="🍅 Tomato", style=discord.ButtonStyle.red, row=1)
    async def p_tomato(self, i, b): await self._plant(i, "tomato")

    @discord.ui.button(label="🔄 Refresh", style=discord.ButtonStyle.grey, row=2)
    async def refresh(self, i, b):
        if not await self._check(i): return
        d = load_user(self.uid); h = check_harvests(d); ev = roll_rare_event(d); save_user(self.uid, d)
        await i.response.edit_message(embed=build_farm_embed(d, h, i.user, rare_event=ev), view=self)

    @discord.ui.button(label="◀ Back", style=discord.ButtonStyle.grey, row=2)
    async def back(self, i, b):
        if not await self._check(i): return
        d = load_user(self.uid); check_harvests(d); save_user(self.uid, d)
        await i.response.edit_message(embed=build_dashboard_embed(d, i.user), view=DashboardView(self.uid))

    @discord.ui.button(label="❌ Close", style=discord.ButtonStyle.danger, row=2)
    async def close_btn(self, i, b):
        if not await self._check(i): return
        await i.message.delete()

    async def _plant(self, i, pt):
        if not await self._check(i): return
        d = load_user(self.uid); check_harvests(d)
        info = PEPPERS[pt]
        if len(d["plots"]) >= MAX_PLOTS:
            msg = random.choice(NO_PLOTS_MESSAGES)
        elif d["gold"] < info["seed_cost"]:
            msg = random.choice(BROKE_MESSAGES)
        else:
            d["gold"] -= info["seed_cost"]
            d["plots"].append({"pepper": pt, "planted_at": time.time()})
            msg = f"{info['emoji']} {random.choice(PLANT_MESSAGES)}\n-{info['seed_cost']}g"
        save_user(self.uid, d)
        await i.response.edit_message(embed=build_farm_embed(d, {}, i.user, extra_msg=msg), view=self)

# ─── Grow Op View ────────────────────────────────────────────────────────────

class GrowView(discord.ui.View):
    def __init__(self, uid):
        super().__init__(timeout=180)
        self.uid = uid

    async def _check(self, i):
        if i.user.id != self.uid:
            await i.response.send_message("Not your grow op!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🌿 Chill Leaf", style=discord.ButtonStyle.green, row=0)
    async def p_chill(self, i, b): await self._plant(i, "chill_leaf")
    @discord.ui.button(label="💜 Purple Haze", style=discord.ButtonStyle.blurple, row=0)
    async def p_purp(self, i, b): await self._plant(i, "purple_haze")
    @discord.ui.button(label="👑 Golden Kush", style=discord.ButtonStyle.grey, row=0)
    async def p_gold(self, i, b): await self._plant(i, "golden_kush")

    @discord.ui.button(label="🔄 Refresh", style=discord.ButtonStyle.grey, row=1)
    async def refresh(self, i, b):
        if not await self._check(i): return
        d = load_user(self.uid); bh = check_bud_harvests(d); raid = check_raid(d); save_user(self.uid, d)
        await i.response.edit_message(embed=build_grow_embed(d, bh, i.user, raid_result=raid), view=self)

    @discord.ui.button(label="◀ Back", style=discord.ButtonStyle.grey, row=1)
    async def back(self, i, b):
        if not await self._check(i): return
        d = load_user(self.uid); check_bud_harvests(d); save_user(self.uid, d)
        await i.response.edit_message(embed=build_dashboard_embed(d, i.user), view=DashboardView(self.uid))

    @discord.ui.button(label="❌ Close", style=discord.ButtonStyle.danger, row=1)
    async def close_btn(self, i, b):
        if not await self._check(i): return
        await i.message.delete()

    async def _plant(self, i, st):
        if not await self._check(i): return
        d = load_user(self.uid); check_bud_harvests(d)
        info = STRAINS[st]
        if len(d.get("grow_plots", [])) >= MAX_GROW_PLOTS:
            msg = "🚫 All grow plots full! Wait for harvest."
        elif d["gold"] < info["seed_cost"]:
            msg = random.choice(BROKE_MESSAGES)
        else:
            d["gold"] -= info["seed_cost"]
            d.setdefault("grow_plots", []).append({"strain": st, "planted_at": time.time()})
            msg = f"{info['emoji']} {random.choice(PLANT_MESSAGES)}\n-{info['seed_cost']}g for {info['name']} seeds."
            msg += f"\n⚠️ Raid chance: **{int(info['raid_chance']*100)}%** base"
            red = get_raid_reduction(d)
            if red > 0:
                msg += f" (reduced to **{int(info['raid_chance']*(1-red)*100)}%**)"
        save_user(self.uid, d)
        await i.response.edit_message(embed=build_grow_embed(d, {}, i.user, extra_msg=msg), view=self)

# ─── Store View ──────────────────────────────────────────────────────────────

class StoreView(discord.ui.View):
    def __init__(self, uid):
        super().__init__(timeout=180)
        self.uid = uid

    async def _check(self, i):
        if i.user.id != self.uid:
            await i.response.send_message("Not your store!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🐕 Guard Dog (300g)", style=discord.ButtonStyle.green, row=0)
    async def buy_dog(self, i, b): await self._buy_prot(i, "guard_dog")
    @discord.ui.button(label="📷 Camera (500g)", style=discord.ButtonStyle.blurple, row=0)
    async def buy_cam(self, i, b): await self._buy_prot(i, "security_cam")
    @discord.ui.button(label="💵 Bribe (1000g)", style=discord.ButtonStyle.danger, row=0)
    async def buy_bribe(self, i, b): await self._buy_prot(i, "bribe")

    @discord.ui.button(label="◀ Back", style=discord.ButtonStyle.grey, row=1)
    async def back(self, i, b):
        if not await self._check(i): return
        d = load_user(self.uid); check_harvests(d); save_user(self.uid, d)
        await i.response.edit_message(embed=build_dashboard_embed(d, i.user), view=DashboardView(self.uid))

    @discord.ui.button(label="❌ Close", style=discord.ButtonStyle.danger, row=1)
    async def close_btn(self, i, b):
        if not await self._check(i): return
        await i.message.delete()

    async def _buy_prot(self, i, item_key):
        if not await self._check(i): return
        d = load_user(self.uid)
        item = PROTECTION_ITEMS[item_key]
        if d["gold"] < item["cost"]:
            msg = random.choice(BROKE_MESSAGES)
        else:
            d["gold"] -= item["cost"]
            d.setdefault("protections", []).append({
                "type": item_key,
                "reduction": item["raid_reduction"],
                "expires_at": time.time() + item["duration"],
            })
            dur_h = item["duration"] / 3600
            msg = f"{item['emoji']} Bought **{item['name']}**! Raid chance -{int(item['raid_reduction']*100)}% for {dur_h:.0f}h.\n-{item['cost']}g"
        save_user(self.uid, d)
        await i.response.edit_message(embed=build_store_embed(d, i.user, extra_msg=msg), view=self)

# ─── Inventory/Sell View ─────────────────────────────────────────────────────

class InventoryView(discord.ui.View):
    def __init__(self, uid):
        super().__init__(timeout=180)
        self.uid = uid

    async def _check(self, i):
        if i.user.id != self.uid:
            await i.response.send_message("Not your stash!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🌶️ Sell All Peppers", style=discord.ButtonStyle.green, row=0)
    async def sell_peps(self, i, b):
        if not await self._check(i): return
        d = load_user(self.uid); check_harvests(d)
        rainbow = d.get("rainbow_active", False)
        total_g = 0; total_c = 0
        for pt, cnt in d["inventory"].items():
            if cnt > 0:
                g = cnt * get_effective_sell_price(pt)
                if rainbow: g *= 2
                total_g += g; total_c += cnt
                d["total_sold"] += cnt; d["inventory"][pt] = 0
        d["gold"] += total_g; d["total_earned"] += total_g
        if rainbow and total_c > 0: d["rainbow_active"] = False
        save_user(self.uid, d)
        msg = f"🤑 Sold {total_c} peppers for {format_gold(total_g)}!" if total_c else "No peppers to sell!"
        if rainbow and total_c: msg += "\n🌈 **RAINBOW 2x BONUS!**"
        await i.response.edit_message(embed=build_inventory_embed(d, i.user, extra_msg=msg), view=self)

    @discord.ui.button(label="🌿 Sell All Buds", style=discord.ButtonStyle.blurple, row=0)
    async def sell_buds(self, i, b):
        if not await self._check(i): return
        d = load_user(self.uid); check_bud_harvests(d)
        rainbow = d.get("rainbow_active", False)
        total_g = 0; total_c = 0
        for st, cnt in d.get("bud_inventory", {}).items():
            if cnt > 0:
                g = cnt * get_effective_bud_price(st)
                if rainbow: g *= 2
                total_g += g; total_c += cnt
                d["buds_sold"] = d.get("buds_sold", 0) + cnt
                d["bud_inventory"][st] = 0
        d["gold"] += total_g; d["total_earned"] += total_g
        if rainbow and total_c: d["rainbow_active"] = False
        save_user(self.uid, d)
        msg = f"💨 Sold {total_c} buds for {format_gold(total_g)}!" if total_c else "No buds to sell!"
        if rainbow and total_c: msg += "\n🌈 **RAINBOW 2x BONUS!**"
        await i.response.edit_message(embed=build_inventory_embed(d, i.user, extra_msg=msg), view=self)

    @discord.ui.button(label="💰 Sell EVERYTHING", style=discord.ButtonStyle.danger, row=0)
    async def sell_all(self, i, b):
        if not await self._check(i): return
        d = load_user(self.uid); check_harvests(d); check_bud_harvests(d)
        rainbow = d.get("rainbow_active", False)
        total_g = 0; total_c = 0
        for pt, cnt in d["inventory"].items():
            if cnt > 0:
                g = cnt * get_effective_sell_price(pt)
                if rainbow: g *= 2
                total_g += g; total_c += cnt; d["total_sold"] += cnt; d["inventory"][pt] = 0
        for st, cnt in d.get("bud_inventory", {}).items():
            if cnt > 0:
                g = cnt * get_effective_bud_price(st)
                if rainbow: g *= 2
                total_g += g; total_c += cnt; d["buds_sold"] = d.get("buds_sold",0) + cnt; d["bud_inventory"][st] = 0
        d["gold"] += total_g; d["total_earned"] += total_g
        if rainbow and total_c: d["rainbow_active"] = False
        save_user(self.uid, d)
        msg = f"🤑 Sold EVERYTHING! {total_c} items for {format_gold(total_g)}!" if total_c else "Nothing to sell!"
        if rainbow and total_c: msg += "\n🌈 **RAINBOW 2x BONUS!**"
        await i.response.edit_message(embed=build_inventory_embed(d, i.user, extra_msg=msg), view=self)

    @discord.ui.button(label="◀ Back", style=discord.ButtonStyle.grey, row=1)
    async def back(self, i, b):
        if not await self._check(i): return
        d = load_user(self.uid); save_user(self.uid, d)
        await i.response.edit_message(embed=build_dashboard_embed(d, i.user), view=DashboardView(self.uid))

    @discord.ui.button(label="❌ Close", style=discord.ButtonStyle.danger, row=1)
    async def close_btn(self, i, b):
        if not await self._check(i): return
        await i.message.delete()

# ─── Casino View ─────────────────────────────────────────────────────────────

class CasinoView(discord.ui.View):
    def __init__(self, uid):
        super().__init__(timeout=180)
        self.uid = uid

    async def _check(self, i):
        if i.user.id != self.uid:
            await i.response.send_message("Get your own table!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🃏 Blackjack", style=discord.ButtonStyle.green, row=0)
    async def blackjack(self, i, b):
        if not await self._check(i): return
        d = load_user(self.uid)
        await i.response.edit_message(embed=build_blackjack_bet_embed(d, i.user), view=BlackjackBetView(self.uid))

    @discord.ui.button(label="🎡 Roulette", style=discord.ButtonStyle.danger, row=0)
    async def roulette(self, i, b):
        if not await self._check(i): return
        d = load_user(self.uid)
        await i.response.edit_message(embed=build_roulette_embed(d, i.user), view=RouletteBetView(self.uid))

    @discord.ui.button(label="🃏 Poker (Multiplayer)", style=discord.ButtonStyle.blurple, row=0)
    async def poker(self, i, b):
        if not await self._check(i): return
        d = load_user(self.uid)
        await i.response.edit_message(embed=build_poker_lobby_embed(d, i.user), view=PokerLobbyView(self.uid))

    @discord.ui.button(label="◀ Back", style=discord.ButtonStyle.grey, row=1)
    async def back(self, i, b):
        if not await self._check(i): return
        d = load_user(self.uid)
        await i.response.edit_message(embed=build_dashboard_embed(d, i.user), view=DashboardView(self.uid))

    @discord.ui.button(label="❌ Close", style=discord.ButtonStyle.danger, row=1)
    async def close_btn(self, i, b):
        if not await self._check(i): return
        await i.message.delete()

# ─── Blackjack ───────────────────────────────────────────────────────────────

class BlackjackBetView(discord.ui.View):
    def __init__(self, uid):
        super().__init__(timeout=60)
        self.uid = uid

    async def _check(self, i):
        if i.user.id != self.uid:
            await i.response.send_message("Not your game!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Bet 25g", style=discord.ButtonStyle.green)
    async def bet25(self, i, b): await self._start(i, 25)
    @discord.ui.button(label="Bet 50g", style=discord.ButtonStyle.blurple)
    async def bet50(self, i, b): await self._start(i, 50)
    @discord.ui.button(label="Bet 100g", style=discord.ButtonStyle.danger)
    async def bet100(self, i, b): await self._start(i, 100)
    @discord.ui.button(label="Bet 250g", style=discord.ButtonStyle.danger)
    async def bet250(self, i, b): await self._start(i, 250)

    @discord.ui.button(label="◀ Back", style=discord.ButtonStyle.grey, row=1)
    async def back(self, i, b):
        if not await self._check(i): return
        d = load_user(self.uid)
        await i.response.edit_message(embed=build_casino_embed(d, i.user), view=CasinoView(self.uid))

    async def _start(self, i, bet):
        if not await self._check(i): return
        d = load_user(self.uid)
        if d["gold"] < bet:
            await i.response.edit_message(embed=build_blackjack_bet_embed(d, i.user, "Not enough gold!"), view=self)
            return
        d["gold"] -= bet
        deck = make_deck(); random.shuffle(deck)
        player = [deck.pop(), deck.pop()]
        dealer = [deck.pop(), deck.pop()]
        pv = hand_value(player)
        save_user(self.uid, d)

        if pv == 21:
            winnings = int(bet * 2.5)
            d["gold"] += winnings; d["casino_wins"] += 1; d["casino_profit"] += winnings - bet
            save_user(self.uid, d)
            embed = discord.Embed(title="🃏 BLACKJACK!", color=0xFFD600)
            embed.description = f"**NATURAL 21!** 🎉\nYour hand: {format_hand(player)} = **21**\nDealer: {format_hand(dealer)} = **{hand_value(dealer)}**\n\n💰 You win {format_gold(winnings)}!"
            await i.response.edit_message(embed=embed, view=BlackjackDoneView(self.uid))
            return

        # Store game state in view
        view = BlackjackPlayView(self.uid, bet, player, dealer, deck)
        embed = build_blackjack_play_embed(player, dealer, bet, d["gold"])
        await i.response.edit_message(embed=embed, view=view)


class BlackjackPlayView(discord.ui.View):
    def __init__(self, uid, bet, player, dealer, deck):
        super().__init__(timeout=60)
        self.uid = uid
        self.bet = bet
        self.player = player
        self.dealer = dealer
        self.deck = deck

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.green)
    async def hit(self, i, b):
        if i.user.id != self.uid:
            await i.response.send_message("Not your game!", ephemeral=True)
            return
        self.player.append(self.deck.pop())
        pv = hand_value(self.player)
        d = load_user(self.uid)
        if pv > 21:
            d["casino_losses"] += 1; d["casino_profit"] -= self.bet; save_user(self.uid, d)
            embed = discord.Embed(title="🃏 BUST!", color=0xF44336)
            embed.description = f"Your hand: {format_hand(self.player)} = **{pv}**\n💥 Over 21! You lose **{self.bet}g**."
            await i.response.edit_message(embed=embed, view=BlackjackDoneView(self.uid))
        elif pv == 21:
            await self._stand_logic(i)
        else:
            embed = build_blackjack_play_embed(self.player, self.dealer, self.bet, d["gold"])
            await i.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.danger)
    async def stand(self, i, b):
        if i.user.id != self.uid:
            await i.response.send_message("Not your game!", ephemeral=True)
            return
        await self._stand_logic(i)

    async def _stand_logic(self, i):
        while hand_value(self.dealer) < 17:
            self.dealer.append(self.deck.pop())
        pv = hand_value(self.player); dv = hand_value(self.dealer)
        d = load_user(self.uid)
        if dv > 21 or pv > dv:
            winnings = self.bet * 2
            d["gold"] += winnings; d["casino_wins"] += 1; d["casino_profit"] += self.bet
            result = f"🎉 **YOU WIN!** +{format_gold(winnings)}"
            color = 0x4CAF50
        elif pv == dv:
            d["gold"] += self.bet  # Push
            result = f"🤝 **PUSH!** Bet returned."
            color = 0xFFEB3B
        else:
            d["casino_losses"] += 1; d["casino_profit"] -= self.bet
            result = f"💀 **Dealer wins.** You lose **{self.bet}g**."
            color = 0xF44336
        save_user(self.uid, d)
        embed = discord.Embed(title="🃏 Blackjack — Result", color=color)
        embed.description = (
            f"Your hand: {format_hand(self.player)} = **{pv}**\n"
            f"Dealer: {format_hand(self.dealer)} = **{dv}**\n\n{result}"
        )
        embed.set_footer(text=f"💰 Gold: {d['gold']:,}g")
        await i.response.edit_message(embed=embed, view=BlackjackDoneView(self.uid))


class BlackjackDoneView(discord.ui.View):
    def __init__(self, uid):
        super().__init__(timeout=60)
        self.uid = uid

    @discord.ui.button(label="🔄 Play Again", style=discord.ButtonStyle.green)
    async def again(self, i, b):
        if i.user.id != self.uid:
            await i.response.send_message("Not your game!", ephemeral=True); return
        d = load_user(self.uid)
        await i.response.edit_message(embed=build_blackjack_bet_embed(d, i.user), view=BlackjackBetView(self.uid))

    @discord.ui.button(label="◀ Casino", style=discord.ButtonStyle.grey)
    async def back(self, i, b):
        if i.user.id != self.uid:
            await i.response.send_message("Not your game!", ephemeral=True); return
        d = load_user(self.uid)
        await i.response.edit_message(embed=build_casino_embed(d, i.user), view=CasinoView(self.uid))

# ─── Roulette ────────────────────────────────────────────────────────────────

class RouletteBetView(discord.ui.View):
    def __init__(self, uid):
        super().__init__(timeout=60)
        self.uid = uid

    async def _check(self, i):
        if i.user.id != self.uid:
            await i.response.send_message("Not your table!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🔴 Red (2x)", style=discord.ButtonStyle.danger, row=0)
    async def bet_red(self, i, b): await self._bet(i, "red")
    @discord.ui.button(label="⚫ Black (2x)", style=discord.ButtonStyle.grey, row=0)
    async def bet_black(self, i, b): await self._bet(i, "black")
    @discord.ui.button(label="🟢 Green 0 (35x)", style=discord.ButtonStyle.green, row=0)
    async def bet_green(self, i, b): await self._bet(i, "green")

    @discord.ui.button(label="Bet 25g", style=discord.ButtonStyle.grey, row=1)
    async def s25(self, i, b): await self._set_amount(i, 25)
    @discord.ui.button(label="Bet 50g", style=discord.ButtonStyle.grey, row=1)
    async def s50(self, i, b): await self._set_amount(i, 50)
    @discord.ui.button(label="Bet 100g", style=discord.ButtonStyle.grey, row=1)
    async def s100(self, i, b): await self._set_amount(i, 100)

    @discord.ui.button(label="◀ Casino", style=discord.ButtonStyle.grey, row=2)
    async def back(self, i, b):
        if not await self._check(i): return
        d = load_user(self.uid)
        await i.response.edit_message(embed=build_casino_embed(d, i.user), view=CasinoView(self.uid))

    async def _set_amount(self, i, amt):
        if not await self._check(i): return
        d = load_user(self.uid)
        await i.response.edit_message(
            embed=build_roulette_embed(d, i.user, f"Bet set to **{amt}g**. Now pick a color!"),
            view=RouletteColorView(self.uid, amt)
        )

    async def _bet(self, i, color):
        if not await self._check(i): return
        await self._spin(i, 50, color)  # Default 50g

    async def _spin(self, i, bet, color):
        d = load_user(self.uid)
        if d["gold"] < bet:
            await i.response.edit_message(embed=build_roulette_embed(d, i.user, "Not enough gold!"), view=self)
            return
        d["gold"] -= bet
        num = random.randint(0, 36)
        result_color = roulette_color(num)
        emoji = roulette_emoji(num)

        if color == result_color:
            mult = 35 if color == "green" else 2
            winnings = bet * mult
            d["gold"] += winnings; d["casino_wins"] += 1; d["casino_profit"] += winnings - bet
            msg = f"{emoji} **{num}** ({result_color})!\n🎉 **YOU WIN!** +{format_gold(winnings)}"
            clr = 0x4CAF50
        else:
            d["casino_losses"] += 1; d["casino_profit"] -= bet
            msg = f"{emoji} **{num}** ({result_color}).\n💀 You lose **{bet}g**."
            clr = 0xF44336

        save_user(self.uid, d)
        embed = discord.Embed(title="🎡 Roulette — Spin!", color=clr)
        embed.description = f"You bet **{bet}g** on **{color}**.\n\nThe wheel spins... 🎡\n\n{msg}"
        embed.set_footer(text=f"💰 Gold: {d['gold']:,}g")
        await i.response.edit_message(embed=embed, view=RouletteDoneView(self.uid))


class RouletteColorView(discord.ui.View):
    def __init__(self, uid, bet):
        super().__init__(timeout=60)
        self.uid = uid
        self.bet = bet

    @discord.ui.button(label="🔴 Red (2x)", style=discord.ButtonStyle.danger)
    async def red(self, i, b): await self._spin(i, "red")
    @discord.ui.button(label="⚫ Black (2x)", style=discord.ButtonStyle.grey)
    async def black(self, i, b): await self._spin(i, "black")
    @discord.ui.button(label="🟢 Green 0 (35x)", style=discord.ButtonStyle.green)
    async def green(self, i, b): await self._spin(i, "green")

    async def _spin(self, i, color):
        if i.user.id != self.uid:
            await i.response.send_message("Not your table!", ephemeral=True); return
        d = load_user(self.uid)
        if d["gold"] < self.bet:
            await i.response.edit_message(
                embed=build_roulette_embed(d, i.user, "Not enough gold!"),
                view=RouletteBetView(self.uid)
            ); return
        d["gold"] -= self.bet
        num = random.randint(0, 36)
        rc = roulette_color(num)
        em = roulette_emoji(num)
        if color == rc:
            mult = 35 if color == "green" else 2
            w = self.bet * mult
            d["gold"] += w; d["casino_wins"] += 1; d["casino_profit"] += w - self.bet
            msg = f"{em} **{num}** ({rc})!\n🎉 **YOU WIN!** +{format_gold(w)}"
            clr = 0x4CAF50
        else:
            d["casino_losses"] += 1; d["casino_profit"] -= self.bet
            msg = f"{em} **{num}** ({rc}).\n💀 You lose **{self.bet}g**."
            clr = 0xF44336
        save_user(self.uid, d)
        embed = discord.Embed(title="🎡 Roulette — Spin!", color=clr)
        embed.description = f"Bet **{self.bet}g** on **{color}**.\n\n🎡 The wheel spins...\n\n{msg}"
        embed.set_footer(text=f"💰 Gold: {d['gold']:,}g")
        await i.response.edit_message(embed=embed, view=RouletteDoneView(self.uid))


class RouletteDoneView(discord.ui.View):
    def __init__(self, uid):
        super().__init__(timeout=60)
        self.uid = uid
    @discord.ui.button(label="🔄 Spin Again", style=discord.ButtonStyle.green)
    async def again(self, i, b):
        if i.user.id != self.uid: await i.response.send_message("Not your table!", ephemeral=True); return
        d = load_user(self.uid)
        await i.response.edit_message(embed=build_roulette_embed(d, i.user), view=RouletteBetView(self.uid))
    @discord.ui.button(label="◀ Casino", style=discord.ButtonStyle.grey)
    async def back(self, i, b):
        if i.user.id != self.uid: await i.response.send_message("Not your table!", ephemeral=True); return
        d = load_user(self.uid)
        await i.response.edit_message(embed=build_casino_embed(d, i.user), view=CasinoView(self.uid))

# ─── Poker (Multiplayer) ────────────────────────────────────────────────────

class PokerLobbyView(discord.ui.View):
    def __init__(self, host_uid):
        super().__init__(timeout=300)
        self.host_uid = host_uid

    @discord.ui.button(label="🃏 Host 100g Table", style=discord.ButtonStyle.green)
    async def host100(self, i, b): await self._host(i, 100)
    @discord.ui.button(label="🃏 Host 250g Table", style=discord.ButtonStyle.blurple)
    async def host250(self, i, b): await self._host(i, 250)
    @discord.ui.button(label="🃏 Host 500g Table", style=discord.ButtonStyle.danger)
    async def host500(self, i, b): await self._host(i, 500)

    @discord.ui.button(label="◀ Casino", style=discord.ButtonStyle.grey, row=1)
    async def back(self, i, b):
        if i.user.id != self.host_uid:
            await i.response.send_message("Use /pep!", ephemeral=True); return
        d = load_user(self.host_uid)
        await i.response.edit_message(embed=build_casino_embed(d, i.user), view=CasinoView(self.host_uid))

    async def _host(self, i, buy_in):
        if i.user.id != self.host_uid:
            await i.response.send_message("Use /pep!", ephemeral=True); return
        d = load_user(self.host_uid)
        if d["gold"] < buy_in:
            await i.response.edit_message(embed=build_poker_lobby_embed(d, i.user, "Not enough gold!"), view=self)
            return
        cid = i.channel_id
        if cid in poker_tables:
            await i.response.edit_message(embed=build_poker_lobby_embed(d, i.user, "A table is already open in this channel!"), view=self)
            return
        d["gold"] -= buy_in; save_user(self.host_uid, d)
        table = PokerTable(cid, buy_in)
        table.add_player(self.host_uid, i.user.display_name)
        poker_tables[cid] = table
        embed = build_poker_waiting_embed(table, i.user)
        view = PokerWaitingView(table)
        await i.response.edit_message(embed=embed, view=view)


class PokerWaitingView(discord.ui.View):
    def __init__(self, table):
        super().__init__(timeout=300)
        self.table = table

    @discord.ui.button(label="🃏 Join Table", style=discord.ButtonStyle.green)
    async def join(self, i, b):
        if i.user.id in self.table.players:
            await i.response.send_message("You're already at the table!", ephemeral=True); return
        d = load_user(i.user.id)
        if d["gold"] < self.table.buy_in:
            await i.response.send_message(f"Need {self.table.buy_in}g to join!", ephemeral=True); return
        d["gold"] -= self.table.buy_in; d["display_name"] = i.user.display_name; save_user(i.user.id, d)
        self.table.add_player(i.user.id, i.user.display_name)
        embed = build_poker_waiting_embed(self.table, i.user)
        await i.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="▶️ Start Game", style=discord.ButtonStyle.danger)
    async def start(self, i, b):
        if len(self.table.players) < 2:
            await i.response.send_message("Need at least 2 players!", ephemeral=True); return
        host = list(self.table.players.keys())[0]
        if i.user.id != host:
            await i.response.send_message("Only the host can start!", ephemeral=True); return
        self.table.start_game()
        # Send each player their hand via DM
        for uid, pdata in self.table.players.items():
            try:
                user = await bot.fetch_user(uid)
                await user.send(f"🃏 **Poker Hand:** {format_hand(pdata['hand'])}\nBuy-in: {self.table.buy_in}g | Pot: {self.table.pot}g")
            except Exception:
                pass
        embed = build_poker_game_embed(self.table)
        view = PokerGameView(self.table)
        await i.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.grey)
    async def cancel(self, i, b):
        host = list(self.table.players.keys())[0]
        if i.user.id != host:
            await i.response.send_message("Only the host can cancel!", ephemeral=True); return
        # Refund everyone
        for uid in self.table.players:
            d = load_user(uid); d["gold"] += self.table.buy_in; save_user(uid, d)
        cid = self.table.channel_id
        if cid in poker_tables: del poker_tables[cid]
        embed = discord.Embed(title="🃏 Poker — Cancelled", description="Table closed. All buy-ins refunded.", color=0x9E9E9E)
        await i.response.edit_message(embed=embed, view=None)


class PokerGameView(discord.ui.View):
    def __init__(self, table):
        super().__init__(timeout=300)
        self.table = table

    @discord.ui.button(label="✅ Check/Call", style=discord.ButtonStyle.green)
    async def check(self, i, b):
        cp = self.table.current_player_id()
        if i.user.id != cp:
            await i.response.send_message("Not your turn!", ephemeral=True); return
        self.table.advance_turn()
        if self.table.phase == "showdown":
            await self._showdown(i)
        else:
            embed = build_poker_game_embed(self.table)
            await i.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="📈 Raise", style=discord.ButtonStyle.blurple)
    async def raise_bet(self, i, b):
        cp = self.table.current_player_id()
        if i.user.id != cp:
            await i.response.send_message("Not your turn!", ephemeral=True); return
        raise_amt = self.table.min_raise
        self.table.pot += raise_amt
        self.table.players[cp]["total_bet"] += raise_amt
        d = load_user(cp)
        if d["gold"] >= raise_amt:
            d["gold"] -= raise_amt; save_user(cp, d)
        self.table.advance_turn()
        if self.table.phase == "showdown":
            await self._showdown(i)
        else:
            embed = build_poker_game_embed(self.table)
            await i.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🏳️ Fold", style=discord.ButtonStyle.danger)
    async def fold(self, i, b):
        if i.user.id not in self.table.players:
            await i.response.send_message("You're not in this game!", ephemeral=True); return
        self.table.players[i.user.id]["folded"] = True
        active = self.table.active_players()
        if len(active) <= 1:
            self.table.phase = "showdown"
            await self._showdown(i)
        else:
            self.table.advance_turn()
            embed = build_poker_game_embed(self.table)
            await i.response.edit_message(embed=embed, view=self)

    async def _showdown(self, i):
        active = self.table.active_players()
        if len(active) == 1:
            winner_id = active[0]
            winner_name = self.table.players[winner_id]["name"]
            result_msg = f"🏆 **{winner_name}** wins by default! Everyone else folded."
        else:
            # Deal remaining community cards
            while len(self.table.community) < 5:
                self.table.community.append(self.table.deck.pop())
            best_score = -1; winner_id = None; winner_hand = ""
            results = []
            for uid in active:
                score, desc = self.table.evaluate_hand(uid)
                name = self.table.players[uid]["name"]
                results.append(f"{name}: {format_hand(self.table.players[uid]['hand'])} — **{desc}**")
                if score > best_score:
                    best_score = score; winner_id = uid; winner_hand = desc
            result_msg = "**Showdown!**\n" + "\n".join(results)
            result_msg += f"\n\n🏆 **{self.table.players[winner_id]['name']}** wins with **{winner_hand}**!"

        # Pay winner
        pot = self.table.pot
        if winner_id:
            d = load_user(winner_id)
            d["gold"] += pot; d["casino_wins"] += 1; d["casino_profit"] += pot - self.table.buy_in
            save_user(winner_id, d)
        # Mark losses
        for uid in self.table.players:
            if uid != winner_id:
                d = load_user(uid); d["casino_losses"] += 1
                d["casino_profit"] -= self.table.players[uid]["total_bet"]
                save_user(uid, d)

        embed = discord.Embed(title="🃏 Poker — Showdown!", color=0xFFD600)
        if self.table.community:
            embed.add_field(name="Community Cards", value=format_hand(self.table.community), inline=False)
        embed.description = f"{result_msg}\n\n💰 Pot: **{pot}g** → {self.table.players[winner_id]['name']}"

        cid = self.table.channel_id
        if cid in poker_tables: del poker_tables[cid]
        await i.response.edit_message(embed=embed, view=None)

# ─── Menu View ───────────────────────────────────────────────────────────────

class MenuView(discord.ui.View):
    def __init__(self, uid):
        super().__init__(timeout=180)
        self.uid = uid

    async def _check(self, i):
        if i.user.id != self.uid:
            await i.response.send_message("Use /pep!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🏆 Leaderboard", style=discord.ButtonStyle.green, row=0)
    async def lb(self, i, b):
        if not await self._check(i): return
        await i.response.edit_message(embed=build_leaderboard_embed(i.user), view=InfoBackView(self.uid))

    @discord.ui.button(label="🌤️ Weather Guide", style=discord.ButtonStyle.blurple, row=0)
    async def wg(self, i, b):
        if not await self._check(i): return
        await i.response.edit_message(embed=build_weather_guide_embed(), view=InfoBackView(self.uid))

    @discord.ui.button(label="⭐ Rare Events", style=discord.ButtonStyle.grey, row=0)
    async def re(self, i, b):
        if not await self._check(i): return
        d = load_user(self.uid)
        await i.response.edit_message(embed=build_rare_events_embed(d), view=InfoBackView(self.uid))

    @discord.ui.button(label="◀ Back", style=discord.ButtonStyle.grey, row=1)
    async def back(self, i, b):
        if not await self._check(i): return
        d = load_user(self.uid); check_harvests(d); save_user(self.uid, d)
        await i.response.edit_message(embed=build_dashboard_embed(d, i.user), view=DashboardView(self.uid))

    @discord.ui.button(label="❌ Close", style=discord.ButtonStyle.danger, row=1)
    async def close_btn(self, i, b):
        if not await self._check(i): return
        await i.message.delete()


class InfoBackView(discord.ui.View):
    def __init__(self, uid):
        super().__init__(timeout=180)
        self.uid = uid
    @discord.ui.button(label="◀ Back to Menu", style=discord.ButtonStyle.grey)
    async def back(self, i, b):
        if i.user.id != self.uid: await i.response.send_message("Use /pep!", ephemeral=True); return
        d = load_user(self.uid)
        await i.response.edit_message(embed=build_menu_embed(d, i.user), view=MenuView(self.uid))
    @discord.ui.button(label="❌ Close", style=discord.ButtonStyle.danger)
    async def close_btn(self, i, b):
        if i.user.id != self.uid: await i.response.send_message("Use /pep!", ephemeral=True); return
        await i.message.delete()


# ─── Embed Builders ──────────────────────────────────────────────────────────

def _section(embed, title, content, inline=False):
    """Add a cleanly separated section to an embed."""
    line = "┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈"
    embed.add_field(name=f"{line}\n{title}", value=f"{content}\n{line}", inline=inline)


def build_dashboard_embed(data, user):
    w = get_current_weather()
    embed = discord.Embed(
        title="🎲  S P I C E   &   D I C E  🌶️",
        description=f"*\"{random.choice(GREETINGS)}\"*\n─────────────────",
        color=0x7CB342,
    )

    # Weather box
    weather_content = (
        f"{w['emoji']} **{w['name']}** — {w['description']}\n"
        f"⏳ Changes in: **{get_weather_time_str(w)}**"
    )
    _section(embed, "☀️ Weather", weather_content)

    # Stats box
    plots_used = len(data["plots"])
    grow_used = len(data.get("grow_plots", []))
    total_inv = sum(data["inventory"].values()) + sum(data.get("bud_inventory", {}).values())
    stats = (
        f"💰 Gold: {format_gold(data['gold'])}\n"
        f"🌾 Pepper Plots: **{plots_used}/{MAX_PLOTS}**\n"
        f"🪴 Grow Plots: **{grow_used}/{MAX_GROW_PLOTS}**\n"
        f"📦 Items in stash: **{total_inv}**"
    )
    if data.get("rainbow_active"):
        stats += "\n🌈 **Rainbow 2x Bonus ACTIVE!**"
    prot = get_active_protection_name(data)
    if prot:
        stats += f"\n🛡️ Protection: {prot}"
    _section(embed, "📊 Overview", stats)

    # Fields box
    field_lines = []
    for i2, plot in enumerate(data["plots"]):
        field_lines.append(f"`P{i2+1}` {get_plot_status(plot)}")
    for i2, plot in enumerate(data.get("grow_plots", [])):
        field_lines.append(f"`G{i2+1}` {get_plot_status(plot, is_bud=True)} ⚠️")
    if field_lines:
        _section(embed, "🌱 Fields", "\n".join(field_lines[:8]))

    # Casino stats box
    cw = data.get("casino_wins", 0); cl = data.get("casino_losses", 0); cp = data.get("casino_profit", 0)
    if cw or cl:
        casino_content = f"🏆 W: **{cw}** | ❌ L: **{cl}** | 💵 Profit: {format_gold(cp)}"
        _section(embed, "🎰 Casino Record", casino_content)

    embed.set_footer(text=f"💰 {data['gold']:,}g")
    embed.set_author(name=f"{user.display_name}'s Spice & Dice", icon_url=user.display_avatar.url)
    return embed


def build_farm_embed(data, harvested, user, extra_msg="", rare_event=None):
    w = get_current_weather()
    embed = discord.Embed(title="🌾  P E P P E R   F A R M  🌾",
                          description=f"{w['emoji']} Weather: **{w['name']}**\n─────────────────", color=0x558B2F)
    if rare_event:
        _section(embed, f"{rare_event['emoji']} {rare_event['name']}!",
                   f"*{rare_event['flavor']}*\n{rare_event['effect_msg']}")
    if harvested:
        hl = [f"{PEPPERS[pt]['emoji']} {random.choice(HARVEST_MESSAGES).format(count=c, name=PEPPERS[pt]['name'])}"
              for pt, c in harvested.items()]
        _section(embed, "🎉 Harvested!", "\n".join(hl))
    if extra_msg:
        _section(embed, "📝 Update", extra_msg)
    fl = []
    for i2, plot in enumerate(data["plots"]):
        fl.append(f"`Plot {i2+1}` {get_plot_status(plot)}")
    for i2 in range(MAX_PLOTS - len(data["plots"])):
        fl.append(f"`Plot {len(data['plots'])+i2+1}` 🟫 *Empty*")
    _section(embed, "🌱 Fields", "\n".join(fl))
    gm = w["grow_modifier"]
    sl = [f"{info['emoji']} {info['name']}: **{info['seed_cost']}g** ({format_time(int(info['grow_time']*gm))})"
          for pt, info in PEPPERS.items()]
    _section(embed, "🌱 Seeds", "\n".join(sl))
    embed.set_footer(text=f"💰 {data['gold']:,}g | Plots: {len(data['plots'])}/{MAX_PLOTS}")
    embed.set_author(name=f"{user.display_name}'s Farm", icon_url=user.display_avatar.url)
    return embed


def build_grow_embed(data, bud_harvested, user, extra_msg="", raid_result=None):
    w = get_current_weather()
    embed = discord.Embed(title="🪴  G R O W   O P  🪴",
                          description=f"{w['emoji']} Weather: **{w['name']}** | *Keep it low-key...*\n─────────────────", color=0x2E7D32)
    if raid_result:
        if raid_result.get("dodged"):
            msg = random.choice(RAID_DODGE_MESSAGES).format(protection=raid_result["protection"])
            _section(embed, "🛡️ Close Call!", msg)
        else:
            msg = random.choice(RAID_MESSAGES).format(lost=1)
            msg += f"\n{STRAINS[raid_result['lost_strain']]['emoji']} Lost: **{raid_result['lost_name']}**"
            _section(embed, "🚨 RAIDED!", msg)
    if bud_harvested:
        hl = [f"{STRAINS[st]['emoji']} {c}x **{STRAINS[st]['name']}** harvested!"
              for st, c in bud_harvested.items()]
        _section(embed, "🎉 Harvested!", "\n".join(hl))
    if extra_msg:
        _section(embed, "📝 Update", extra_msg)

    # Grow plots
    gl = []
    for i2, plot in enumerate(data.get("grow_plots", [])):
        gl.append(f"`Grow {i2+1}` {get_plot_status(plot, is_bud=True)}")
    for i2 in range(MAX_GROW_PLOTS - len(data.get("grow_plots", []))):
        gl.append(f"`Grow {len(data.get('grow_plots',[]))+i2+1}` 🟫 *Empty*")
    _section(embed, "🪴 Grow Plots", "\n".join(gl))

    # Strain catalog
    gm = w["grow_modifier"]
    for st, info in STRAINS.items():
        red = get_raid_reduction(data)
        eff_raid = info["raid_chance"] * (1 - red)
        v = (f"💰 Seed: **{info['seed_cost']}g** | Sells: **{get_effective_bud_price(st)}g**\n"
             f"⏱️ Grow: **{format_time(int(info['grow_time']*gm))}** | "
             f"🚔 Raid: **{int(eff_raid*100)}%**\n*{info['description']}*")
        embed.add_field(name=f"{info['emoji']} {info['name']} ({info['rarity']})", value=v, inline=True)

    # Protection status
    prot = get_active_protection_name(data)
    if prot:
        _section(embed, "🛡️ Active Protection", prot)
    else:
        _section(embed, "⚠️ No Protection!", "*Buy protection at the Store to lower raid chance!*")

    embed.set_footer(text=f"💰 {data['gold']:,}g | Grow Plots: {len(data.get('grow_plots',[]))}/{MAX_GROW_PLOTS}")
    embed.set_author(name=f"{user.display_name}'s Grow Op", icon_url=user.display_avatar.url)
    return embed


def build_store_embed(data, user, extra_msg=""):
    embed = discord.Embed(title="🏪  T H E   S T O R E  🏪",
                          description=f"*\"Need some... security? I got you, fam.\"*\n─────────────────", color=0x6D4C41)
    if extra_msg:
        _section(embed, "📝 Update", extra_msg)
    for pk, item in PROTECTION_ITEMS.items():
        dur = item["duration"] / 3600
        v = (f"💰 Cost: **{item['cost']}g**\n"
             f"🛡️ Raid reduction: **-{int(item['raid_reduction']*100)}%**\n"
             f"⏱️ Duration: **{dur:.0f}h**\n*{item['description']}*")
        embed.add_field(name=f"{item['emoji']} {item['name']}", value=v, inline=True)

    prot = get_active_protection_name(data)
    if prot:
        _section(embed, "🛡️ Active", prot)
    red = get_raid_reduction(data)
    embed.set_footer(text=f"💰 {data['gold']:,}g | Current raid reduction: {int(red*100)}%")
    embed.set_author(name=f"{user.display_name}'s Shopping", icon_url=user.display_avatar.url)
    return embed


def build_inventory_embed(data, user, extra_msg=""):
    w = get_current_weather()
    embed = discord.Embed(title="📦  S T A S H  📦",
                          description=f"*\"What're we sellin' today?\"*\n─────────────────", color=0xE65100)
    if extra_msg:
        _section(embed, "📝 Update", extra_msg)
    # Peppers
    pl = []
    ptotal = 0
    for pt, cnt in data["inventory"].items():
        p = get_effective_sell_price(pt)
        v = cnt * p
        ptotal += v
        pl.append(f"{PEPPERS[pt]['emoji']} **{PEPPERS[pt]['name']}** x{cnt} → {format_gold(v)}" if cnt else
                  f"{PEPPERS[pt]['emoji']} {PEPPERS[pt]['name']} — *none*")
    _section(embed, "🌶️ Peppers", "\n".join(pl))
    # Buds
    bl = []
    btotal = 0
    for st, cnt in data.get("bud_inventory", {}).items():
        p = get_effective_bud_price(st)
        v = cnt * p
        btotal += v
        bl.append(f"{STRAINS[st]['emoji']} **{STRAINS[st]['name']}** x{cnt} → {format_gold(v)}" if cnt else
                  f"{STRAINS[st]['emoji']} {STRAINS[st]['name']} — *none*")
    _section(embed, "🌿 Buds", "\n".join(bl))
    total = ptotal + btotal
    if data.get("rainbow_active"): total *= 2
    vs = f"💰 Total value: {format_gold(total)}\n🏦 Your gold: {format_gold(data['gold'])}"
    if data.get("rainbow_active"): vs += "\n🌈 **RAINBOW 2x ACTIVE!**"
    _section(embed, "💰 Value", vs)
    embed.set_footer(text=f"Weather prices: {w['emoji']} {w['name']}")
    embed.set_author(name=f"{user.display_name}'s Stash", icon_url=user.display_avatar.url)
    return embed


def build_casino_embed(data, user):
    embed = discord.Embed(title="🎰  T H E   C A S I N O  🎰",
                          description=f"*\"Step right up! The house always... well, sometimes wins.\"*\n─────────────────", color=0x880E4F)
    embed.add_field(name="🃏 Blackjack", value="Classic 21. Beat the dealer!\nBet 25g, 50g, 100g, or 250g.", inline=True)
    embed.add_field(name="🎡 Roulette", value="Pick red, black, or green.\nRed/Black pays 2x, Green pays 35x!", inline=True)
    embed.add_field(name="🃏 Poker", value="Texas Hold'em vs other players!\nHost a table and invite friends.", inline=True)
    cw = data.get("casino_wins", 0); cl = data.get("casino_losses", 0); cp = data.get("casino_profit", 0)
    _section(embed, "📊 Your Record",
               f"🏆 Wins: **{cw}** | ❌ Losses: **{cl}** | 💵 Net: {format_gold(cp)}")
    embed.set_footer(text=f"💰 Gold: {data['gold']:,}g | Gamble responsibly... or don't!")
    embed.set_author(name=f"{user.display_name} at the Casino", icon_url=user.display_avatar.url)
    return embed


def build_blackjack_bet_embed(data, user, msg=""):
    embed = discord.Embed(title="🃏  B L A C K J A C K  🃏",
                          description="*\"Place your bets! Closest to 21 wins.\"*", color=0x1B5E20)
    if msg:
        embed.add_field(name="", value=msg, inline=False)
    embed.add_field(name="Rules", value=(
        "• Get as close to 21 as possible without going over\n"
        "• Face cards = 10, Aces = 1 or 11\n"
        "• Natural 21 = 2.5x payout!\n"
        "• Beat the dealer to win 2x your bet"
    ), inline=False)
    embed.set_footer(text=f"💰 Gold: {data['gold']:,}g")
    return embed


def build_blackjack_play_embed(player, dealer, bet, gold):
    pv = hand_value(player)
    embed = discord.Embed(title="🃏 Blackjack", color=0x1B5E20)
    embed.add_field(name="Your Hand", value=f"{format_hand(player)}\nValue: **{pv}**", inline=True)
    embed.add_field(name="Dealer Shows", value=f"{format_card(dealer[0])} `??`", inline=True)
    embed.add_field(name="Bet", value=f"**{bet}g**", inline=True)
    embed.set_footer(text=f"💰 Gold: {gold:,}g")
    return embed


def build_roulette_embed(data, user, msg=""):
    embed = discord.Embed(title="🎡  R O U L E T T E  🎡",
                          description="*\"Round and round she goes...\"*", color=0xB71C1C)
    if msg:
        embed.add_field(name="", value=msg, inline=False)
    embed.add_field(name="Payouts", value=(
        "🔴 Red — **2x** payout\n"
        "⚫ Black — **2x** payout\n"
        "🟢 Green (0) — **35x** payout!"
    ), inline=False)
    embed.set_footer(text=f"💰 Gold: {data['gold']:,}g | Pick a bet amount, then a color!")
    return embed


def build_poker_lobby_embed(data, user, msg=""):
    embed = discord.Embed(title="🃏  P O K E R   L O B B Y  🃏",
                          description="*\"Texas Hold'em. Winner takes the pot.\"*", color=0x0D47A1)
    if msg:
        embed.add_field(name="", value=msg, inline=False)
    embed.add_field(name="How it works", value=(
        "1. **Host** picks a buy-in amount\n"
        "2. Other players **join** the table\n"
        "3. Host clicks **Start** (2+ players needed)\n"
        "4. Hands are sent via **DM** — check/call, raise, or fold\n"
        "5. Winner takes the entire pot!"
    ), inline=False)
    embed.set_footer(text=f"💰 Gold: {data['gold']:,}g")
    return embed


def build_poker_waiting_embed(table, user):
    embed = discord.Embed(title="🃏 Poker — Waiting for Players", color=0x0D47A1)
    players = "\n".join(f"• **{p['name']}**" for p in table.players.values())
    embed.add_field(name=f"Buy-in: {table.buy_in}g | Players ({len(table.players)}):", value=players, inline=False)
    embed.add_field(name="Pot", value=f"**{len(table.players) * table.buy_in}g**", inline=True)
    embed.set_footer(text="Other players: click Join! Host: click Start when ready.")
    return embed


def build_poker_game_embed(table):
    embed = discord.Embed(title="🃏 Poker — In Progress", color=0x0D47A1)
    embed.add_field(name="Phase", value=f"**{table.phase.upper()}**", inline=True)
    embed.add_field(name="Pot", value=f"**{table.pot}g**", inline=True)
    if table.community:
        embed.add_field(name="Community Cards", value=format_hand(table.community), inline=False)
    # Player status
    pl = []
    cp = table.current_player_id()
    for uid in table.turn_order:
        p = table.players[uid]
        status = "🏳️ Folded" if p["folded"] else ("👈 **YOUR TURN**" if uid == cp else "⏳ Waiting")
        pl.append(f"{'**' if uid == cp else ''}{p['name']}{'**' if uid == cp else ''} — {status}")
    embed.add_field(name="Players", value="\n".join(pl), inline=False)
    embed.set_footer(text="Check your DMs for your hand! 🃏")
    return embed


def build_menu_embed(data, user):
    w = get_current_weather()
    embed = discord.Embed(title="📋  M E N U  📋",
                          description="*\"Take a break. Check the stats, learn the ropes.\"*", color=0x5C6BC0)
    embed.add_field(name=f"{w['emoji']} Weather", value=f"**{w['name']}** — changes in {get_weather_time_str(w)}", inline=False)
    events = data.get("rare_events_seen", [])
    if events:
        recent = [f"{RARE_EVENTS.get(e['event'],{}).get('emoji','?')} {RARE_EVENTS.get(e['event'],{}).get('name','???')}"
                  for e in events[-3:]]
        embed.add_field(name="⭐ Recent Events", value="\n".join(reversed(recent)), inline=False)
    embed.add_field(name="📖 Guides", value="🏆 Leaderboard | 🌤️ Weather | ⭐ Rare Events", inline=False)
    # Lifetime
    lt = (f"🌶️ Peppers harvested: **{data.get('total_harvested',0)}** | Sold: **{data.get('total_sold',0)}**\n"
          f"🌿 Buds harvested: **{data.get('buds_harvested',0)}** | Sold: **{data.get('buds_sold',0)}**\n"
          f"🚔 Raids survived: **{data.get('raids_dodged',0)}** | Buds lost: **{data.get('buds_lost_to_raids',0)}**\n"
          f"🏦 Lifetime earned: {format_gold(data.get('total_earned',0))}")
    embed.add_field(name="── Lifetime Stats ──", value=lt, inline=False)
    embed.set_author(name=f"{user.display_name}'s Menu", icon_url=user.display_avatar.url)
    return embed


def build_leaderboard_embed(user):
    embed = discord.Embed(title="🏆  L E A D E R B O A R D  🏆", color=0xFFD600)
    all_u = get_all_users()
    if not all_u:
        embed.description = "No farmers yet!"
        return embed
    medals = ["🥇", "🥈", "🥉"]
    # Gold
    by_gold = sorted(all_u, key=lambda x: x[1].get("gold",0), reverse=True)[:10]
    gl = [f"{medals[i] if i<3 else f'`{i+1}.`'} **{u[1].get('display_name','?')}** — {format_gold(u[1].get('gold',0))}"
          for i, u in enumerate(by_gold)]
    embed.add_field(name="💰 Richest", value="\n".join(gl), inline=False)
    # Casino profit
    by_casino = sorted(all_u, key=lambda x: x[1].get("casino_profit",0), reverse=True)[:5]
    cl = [f"{medals[i] if i<3 else f'`{i+1}.`'} **{u[1].get('display_name','?')}** — {format_gold(u[1].get('casino_profit',0))}"
          for i, u in enumerate(by_casino)]
    embed.add_field(name="🎰 Best Gamblers", value="\n".join(cl), inline=False)
    # Harvested
    by_h = sorted(all_u, key=lambda x: x[1].get("total_harvested",0)+x[1].get("buds_harvested",0), reverse=True)[:5]
    hl = [f"{medals[i] if i<3 else f'`{i+1}.`'} **{u[1].get('display_name','?')}** — **{u[1].get('total_harvested',0)+u[1].get('buds_harvested',0)}** crops"
          for i, u in enumerate(by_h)]
    embed.add_field(name="🌱 Top Farmers", value="\n".join(hl), inline=False)
    embed.set_footer(text=f"Total farmers: {len(all_u)}")
    return embed


def build_weather_guide_embed():
    embed = discord.Embed(title="🌤️  W E A T H E R   G U I D E  🌤️", color=0x29B6F6,
                          description="*Weather changes every 2 hours and affects growth + sell prices.*")
    for wk, w in WEATHER_TYPES.items():
        ge = f"+{int((1-w['grow_modifier'])*100)}% faster" if w['grow_modifier']<1 else f"{int((w['grow_modifier']-1)*100)}% slower" if w['grow_modifier']>1 else "Normal"
        se = f"+{int((w['sell_modifier']-1)*100)}%" if w['sell_modifier']>1 else f"-{int((1-w['sell_modifier'])*100)}%" if w['sell_modifier']<1 else "Normal"
        embed.add_field(name=f"{w['emoji']} {w['name']}", value=f"🌱 Growth: **{ge}**\n💰 Prices: **{se}**\n📊 Chance: {w['weight']}%", inline=True)
    embed.add_field(name="💡 Tips", value=(
        "• Plant in **Rain/Storms** for speed\n• Sell in **Heat Waves** for +25%\n"
        "• **Fog** gives slight raid protection\n• Weather changes every **2h**"
    ), inline=False)
    return embed


def build_rare_events_embed(data):
    embed = discord.Embed(title="⭐  R A R E   E V E N T S  ⭐", color=0xAB47BC,
                          description="*Strange things happen in the valley... visit your farm to discover them!*")
    seen = {e["event"] for e in data.get("rare_events_seen", [])}
    for ek, ev in RARE_EVENTS.items():
        if ek in seen:
            embed.add_field(name=f"{ev['emoji']} {ev['name']}", value=f"**Effect:** {ev['effect']}\n**Chance:** {ev['chance']*100:.0f}%\n✅ Discovered!", inline=True)
        else:
            embed.add_field(name="❓ ???", value="*Visit your farm to discover...*\n❓ Not found", inline=True)
    embed.add_field(name="Progress", value=f"**{len(seen)}/{len(RARE_EVENTS)}** discovered", inline=False)
    return embed


# ─── Slash Command ────────────────────────────────────────────────────────────

@bot.tree.command(name="pep", description="Open your Spice & Dice dashboard!")
async def pep_command(interaction: discord.Interaction):
    data = load_user(interaction.user.id)
    data["display_name"] = interaction.user.display_name
    harvested = check_harvests(data)
    bud_harvested = check_bud_harvests(data)
    raid = check_raid(data)
    event = roll_rare_event(data)
    save_user(interaction.user.id, data)

    embed = build_dashboard_embed(data, interaction.user)

    # Notifications at top
    notifications = []
    if raid:
        if raid.get("dodged"):
            notifications.append(f"🛡️ Cops came by but your protection saved you!")
        else:
            notifications.append(f"🚨 **RAIDED!** Lost a {raid['lost_name']} from your grow op!")
    if harvested:
        parts = [f"{PEPPERS[pt]['emoji']} {c}x {PEPPERS[pt]['name']}" for pt, c in harvested.items()]
        notifications.append("🎉 **Pepper Harvest:** " + ", ".join(parts))
    if bud_harvested:
        parts = [f"{STRAINS[st]['emoji']} {c}x {STRAINS[st]['name']}" for st, c in bud_harvested.items()]
        notifications.append("🌿 **Bud Harvest:** " + ", ".join(parts))
    if event:
        notifications.append(f"{event['emoji']} **{event['name']}!** {event['effect_msg']}")

    if notifications:
        embed.insert_field_at(0, name="── 🔔 Notifications ──", value="\n".join(notifications), inline=False)

    await interaction.response.send_message(embed=embed, view=DashboardView(interaction.user.id))


# ─── Bot Events ──────────────────────────────────────────────────────────────

@bot.event
async def on_ready():
    print(f"🎲 Spice & Dice is online as {bot.user}!")
    print(f"   Serving {len(bot.guilds)} server(s)")
    try:
        synced = await bot.tree.sync()
        print(f"   Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"   Failed to sync: {e}")
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.playing, name="🌶️ /pep — Spice & Dice"))


# ─── Run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not TOKEN:
        print("=" * 50)
        print("  SPICE & DICE - Setup Required!")
        print("=" * 50)
        print("\nSet DISCORD_TOKEN in .env or environment variable.")
        print("Visit: https://discord.com/developers/applications")
        print("=" * 50)
    else:
        bot.run(TOKEN)
