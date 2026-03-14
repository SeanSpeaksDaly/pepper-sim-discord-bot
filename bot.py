"""
Pepper Sim - A cozy pepper farming Discord bot
Inspired by Stardew Valley vibes and JRPGs
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
from pathlib import Path

# ─── Config ───────────────────────────────────────────────────────────────────

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
        "grow_time": 60 * 30,       # 30 minutes
        "description": "A crunchy lil' garden pepper. Fresh off the vine!",
        "rarity": "Common",
        "image": "pepper_green.png",
    },
    "red": {
        "name": "Red Pep",
        "emoji": "🌶️",
        "seed_cost": 25,
        "sell_price": 60,
        "grow_time": 60 * 60,       # 1 hour
        "description": "Spicy!! This one's got some kick to it.",
        "rarity": "Uncommon",
        "image": "pepper_red.png",
    },
    "yellow": {
        "name": "Yellow Pep",
        "emoji": "💛",
        "seed_cost": 50,
        "sell_price": 130,
        "grow_time": 60 * 120,      # 2 hours
        "description": "Sweet and tangy. The townsfolk love these in salads.",
        "rarity": "Rare",
        "image": "pepper_yellow.png",
    },
    "golden": {
        "name": "Golden Pep",
        "emoji": "✨",
        "seed_cost": 200,
        "sell_price": 500,
        "grow_time": 60 * 360,      # 6 hours
        "description": "A legendary pepper that glows in the moonlight... worth a fortune!",
        "rarity": "Legendary",
        "image": "pepper_golden.png",
    },
}

# Field plot count per user
MAX_PLOTS = 6
STARTING_GOLD = 100

# ─── Stardew Valley Style Flavor Text ────────────────────────────────────────

GREETINGS = [
    "Mornin', farmer! The soil's lookin' good today.",
    "Hey there, partner! Ready to tend the peppers?",
    "Welcome back to the farm! The peppers missed ya.",
    "Well well, if it isn't my favorite farmer! Let's get growin'!",
    "The valley's peaceful today... perfect pepper weather!",
    "Howdy! I can smell the fresh soil from here.",
    "Another beautiful day on the farm! Let's make it count.",
    "The scarecrow says hi! ...Okay, I said hi. Let's farm!",
]

HARVEST_MESSAGES = [
    "You plucked {count}x {name} right off the vine! Nice haul!",
    "Fresh {name}! {count} beauties, ready for the market!",
    "Look at those gorgeous {name}s! {count} harvested!",
    "{count}x {name} harvested! The farm's really producin'!",
    "What a crop! {count}x {name} added to your basket!",
]

PLANT_MESSAGES = [
    "Seeds in the ground! Now we wait and hope for sunshine~",
    "Planted! Give 'em some time and they'll grow up strong.",
    "Into the soil they go! Farming's all about patience, friend.",
    "Seeds are set! I got a good feelin' about this batch.",
    "And... planted! The earth'll take care of the rest.",
]

SELL_MESSAGES = [
    "Sold! Pierre would be jealous of these prices.",
    "Ka-ching! {gold}g added to your wallet!",
    "The merchant's eyes lit up! +{gold}g!",
    "That's good business, farmer! +{gold}g in the register!",
    "Sold to the highest bidder! ...Okay, the only bidder. +{gold}g!",
]

EMPTY_FARM_MESSAGES = [
    "Your fields are wide open! Perfect time to plant somethin'.",
    "Nothin' but soil and potential out here. Let's plant!",
    "The plots are empty... they're beggin' for some seeds!",
    "Bare fields as far as the eye can see. Time to get plantin'!",
]

BROKE_MESSAGES = [
    "Hmm... your pockets are a bit light for that, friend.",
    "Not enough gold! Maybe sell some peppers first?",
    "Ah, you're a few coins short. The farm life's tough sometimes!",
    "Can't quite afford that... try harvestin' and sellin' first!",
]

NO_PLOTS_MESSAGES = [
    "All your plots are full! Wait for those peppers to grow~",
    "No empty plots! Your farm's bustlin' with activity!",
    "Every inch of soil is spoken for! Patience, farmer!",
]

# ─── Data Persistence ─────────────────────────────────────────────────────────

def get_data_path(user_id: int) -> Path:
    return DATA_DIR / f"{user_id}.json"


def load_user(user_id: int) -> dict:
    path = get_data_path(user_id)
    if path.exists():
        with open(path, "r") as f:
            return json.load(f)
    # New farmer!
    data = {
        "gold": STARTING_GOLD,
        "inventory": {"green": 0, "red": 0, "yellow": 0, "golden": 0},
        "plots": [],  # list of {"pepper": type, "planted_at": timestamp}
        "total_harvested": 0,
        "total_sold": 0,
        "total_earned": 0,
    }
    save_user(user_id, data)
    return data


def save_user(user_id: int, data: dict):
    path = get_data_path(user_id)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# ─── Game Logic Helpers ───────────────────────────────────────────────────────

def check_harvests(data: dict) -> list:
    """Auto-harvest any ready peppers. Returns list of harvested items."""
    now = time.time()
    harvested = {}
    remaining_plots = []

    for plot in data["plots"]:
        pepper_type = plot["pepper"]
        grow_time = PEPPERS[pepper_type]["grow_time"]
        if now - plot["planted_at"] >= grow_time:
            harvested[pepper_type] = harvested.get(pepper_type, 0) + 1
            data["inventory"][pepper_type] = data["inventory"].get(pepper_type, 0) + 1
            data["total_harvested"] = data.get("total_harvested", 0) + 1
            # Plot is now empty (field left open after harvest)
        else:
            remaining_plots.append(plot)

    data["plots"] = remaining_plots
    return harvested


def get_plot_status(plot: dict) -> str:
    """Get a visual status for a plot."""
    now = time.time()
    pepper_type = plot["pepper"]
    info = PEPPERS[pepper_type]
    elapsed = now - plot["planted_at"]
    grow_time = info["grow_time"]
    progress = min(elapsed / grow_time, 1.0)

    if progress >= 1.0:
        return f"{info['emoji']} **READY!**"

    # Growth stages
    bar_length = 8
    filled = int(progress * bar_length)
    empty = bar_length - filled
    bar = "█" * filled + "░" * empty

    remaining = grow_time - elapsed
    if remaining > 3600:
        time_str = f"{remaining / 3600:.1f}h"
    elif remaining > 60:
        time_str = f"{remaining / 60:.0f}m"
    else:
        time_str = f"{remaining:.0f}s"

    stage_emoji = "🌱" if progress < 0.33 else ("🌿" if progress < 0.66 else "🪴")
    return f"{stage_emoji} {info['name']} [{bar}] {time_str}"


def format_gold(amount: int) -> str:
    return f"**{amount:,}**g"


# ─── Bot Setup ────────────────────────────────────────────────────────────────

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


# ─── Views (Button UIs) ──────────────────────────────────────────────────────

class DashboardView(discord.ui.View):
    """Main dashboard with navigation buttons."""

    def __init__(self, user_id: int):
        super().__init__(timeout=120)
        self.user_id = user_id

    @discord.ui.button(label="🌾 Farm", style=discord.ButtonStyle.green, custom_id="farm")
    async def farm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Hey, that's not your farm! Use `/pep` to open yours.", ephemeral=True)
            return
        data = load_user(self.user_id)
        harvested = check_harvests(data)
        save_user(self.user_id, data)
        embed = build_farm_embed(data, harvested, interaction.user)
        view = FarmView(self.user_id)
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="🏪 Store", style=discord.ButtonStyle.blurple, custom_id="store")
    async def store_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Hey, that's not your farm! Use `/pep` to open yours.", ephemeral=True)
            return
        data = load_user(self.user_id)
        check_harvests(data)
        save_user(self.user_id, data)
        embed = build_store_embed(data, interaction.user)
        view = StoreView(self.user_id)
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="📦 Inventory", style=discord.ButtonStyle.grey, custom_id="inventory")
    async def inventory_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Hey, that's not your farm! Use `/pep` to open yours.", ephemeral=True)
            return
        data = load_user(self.user_id)
        check_harvests(data)
        save_user(self.user_id, data)
        embed = build_inventory_embed(data, interaction.user)
        view = InventoryView(self.user_id)
        await interaction.response.edit_message(embed=embed, view=view)


class FarmView(discord.ui.View):
    """Farm view with planting options and back button."""

    def __init__(self, user_id: int):
        super().__init__(timeout=120)
        self.user_id = user_id

    @discord.ui.button(label="🫑 Plant Green", style=discord.ButtonStyle.green, row=0)
    async def plant_green(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.do_plant(interaction, "green")

    @discord.ui.button(label="🌶️ Plant Red", style=discord.ButtonStyle.red, row=0)
    async def plant_red(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.do_plant(interaction, "red")

    @discord.ui.button(label="💛 Plant Yellow", style=discord.ButtonStyle.grey, row=0)
    async def plant_yellow(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.do_plant(interaction, "yellow")

    @discord.ui.button(label="✨ Plant Golden", style=discord.ButtonStyle.blurple, row=0)
    async def plant_golden(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.do_plant(interaction, "golden")

    @discord.ui.button(label="🔄 Refresh", style=discord.ButtonStyle.grey, row=1)
    async def refresh(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("That's not your farm!", ephemeral=True)
            return
        data = load_user(self.user_id)
        harvested = check_harvests(data)
        save_user(self.user_id, data)
        embed = build_farm_embed(data, harvested, interaction.user)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="◀ Back", style=discord.ButtonStyle.grey, row=1)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("That's not your farm!", ephemeral=True)
            return
        data = load_user(self.user_id)
        check_harvests(data)
        save_user(self.user_id, data)
        embed = build_dashboard_embed(data, interaction.user)
        view = DashboardView(self.user_id)
        await interaction.response.edit_message(embed=embed, view=view)

    async def do_plant(self, interaction: discord.Interaction, pepper_type: str):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("That's not your farm!", ephemeral=True)
            return

        data = load_user(self.user_id)
        check_harvests(data)
        info = PEPPERS[pepper_type]
        msg = ""

        if len(data["plots"]) >= MAX_PLOTS:
            msg = random.choice(NO_PLOTS_MESSAGES)
        elif data["gold"] < info["seed_cost"]:
            msg = random.choice(BROKE_MESSAGES)
        else:
            data["gold"] -= info["seed_cost"]
            data["plots"].append({"pepper": pepper_type, "planted_at": time.time()})
            msg = f"{info['emoji']} {random.choice(PLANT_MESSAGES)}\n-{info['seed_cost']}g for {info['name']} seeds."

        save_user(self.user_id, data)
        embed = build_farm_embed(data, {}, interaction.user, extra_msg=msg)
        await interaction.response.edit_message(embed=embed, view=self)


class StoreView(discord.ui.View):
    """Store for buying seeds."""

    def __init__(self, user_id: int):
        super().__init__(timeout=120)
        self.user_id = user_id

    @discord.ui.button(label="🫑 Green Seeds (10g)", style=discord.ButtonStyle.green, row=0)
    async def buy_green(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.do_buy(interaction, "green")

    @discord.ui.button(label="🌶️ Red Seeds (25g)", style=discord.ButtonStyle.red, row=0)
    async def buy_red(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.do_buy(interaction, "red")

    @discord.ui.button(label="💛 Yellow Seeds (50g)", style=discord.ButtonStyle.grey, row=0)
    async def buy_yellow(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.do_buy(interaction, "yellow")

    @discord.ui.button(label="✨ Golden Seeds (200g)", style=discord.ButtonStyle.blurple, row=0)
    async def buy_golden(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.do_buy(interaction, "golden")

    @discord.ui.button(label="◀ Back", style=discord.ButtonStyle.grey, row=1)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("That's not your store!", ephemeral=True)
            return
        data = load_user(self.user_id)
        check_harvests(data)
        save_user(self.user_id, data)
        embed = build_dashboard_embed(data, interaction.user)
        view = DashboardView(self.user_id)
        await interaction.response.edit_message(embed=embed, view=view)

    async def do_buy(self, interaction: discord.Interaction, pepper_type: str):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("That's not your store!", ephemeral=True)
            return

        data = load_user(self.user_id)
        check_harvests(data)
        info = PEPPERS[pepper_type]
        msg = ""

        if len(data["plots"]) >= MAX_PLOTS:
            msg = random.choice(NO_PLOTS_MESSAGES)
        elif data["gold"] < info["seed_cost"]:
            msg = random.choice(BROKE_MESSAGES)
        else:
            data["gold"] -= info["seed_cost"]
            data["plots"].append({"pepper": pepper_type, "planted_at": time.time()})
            msg = f"{info['emoji']} Bought {info['name']} seeds and planted 'em!\n-{info['seed_cost']}g"

        save_user(self.user_id, data)
        embed = build_store_embed(data, interaction.user, extra_msg=msg)
        await interaction.response.edit_message(embed=embed, view=self)


class InventoryView(discord.ui.View):
    """Inventory view for selling peppers."""

    def __init__(self, user_id: int):
        super().__init__(timeout=120)
        self.user_id = user_id

    @discord.ui.button(label="Sell Green Peps", style=discord.ButtonStyle.green, row=0)
    async def sell_green(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.do_sell(interaction, "green")

    @discord.ui.button(label="Sell Red Peps", style=discord.ButtonStyle.red, row=0)
    async def sell_red(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.do_sell(interaction, "red")

    @discord.ui.button(label="Sell Yellow Peps", style=discord.ButtonStyle.grey, row=0)
    async def sell_yellow(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.do_sell(interaction, "yellow")

    @discord.ui.button(label="Sell Golden Peps", style=discord.ButtonStyle.blurple, row=0)
    async def sell_golden(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.do_sell(interaction, "golden")

    @discord.ui.button(label="💰 Sell ALL", style=discord.ButtonStyle.danger, row=1)
    async def sell_all(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("That's not your inventory!", ephemeral=True)
            return
        data = load_user(self.user_id)
        check_harvests(data)
        total_gold = 0
        total_count = 0
        for ptype, count in data["inventory"].items():
            if count > 0:
                gold = count * PEPPERS[ptype]["sell_price"]
                total_gold += gold
                total_count += count
                data["total_sold"] = data.get("total_sold", 0) + count
                data["inventory"][ptype] = 0
        data["gold"] += total_gold
        data["total_earned"] = data.get("total_earned", 0) + total_gold
        save_user(self.user_id, data)

        if total_count > 0:
            msg = f"🤑 Sold everything! {total_count} peppers for {format_gold(total_gold)}!"
        else:
            msg = "Your basket's empty! Grow some peppers first~"

        embed = build_inventory_embed(data, interaction.user, extra_msg=msg)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="◀ Back", style=discord.ButtonStyle.grey, row=1)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("That's not your inventory!", ephemeral=True)
            return
        data = load_user(self.user_id)
        check_harvests(data)
        save_user(self.user_id, data)
        embed = build_dashboard_embed(data, interaction.user)
        view = DashboardView(self.user_id)
        await interaction.response.edit_message(embed=embed, view=view)

    async def do_sell(self, interaction: discord.Interaction, pepper_type: str):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("That's not your inventory!", ephemeral=True)
            return

        data = load_user(self.user_id)
        check_harvests(data)
        info = PEPPERS[pepper_type]
        count = data["inventory"].get(pepper_type, 0)

        if count <= 0:
            msg = f"You don't have any {info['name']}s to sell!"
        else:
            gold = count * info["sell_price"]
            data["gold"] += gold
            data["total_sold"] = data.get("total_sold", 0) + count
            data["total_earned"] = data.get("total_earned", 0) + gold
            data["inventory"][pepper_type] = 0
            msg = random.choice(SELL_MESSAGES).format(gold=gold) + f"\n{info['emoji']} {count}x {info['name']} → {format_gold(gold)}"

        save_user(self.user_id, data)
        embed = build_inventory_embed(data, interaction.user, extra_msg=msg)
        await interaction.response.edit_message(embed=embed, view=self)


# ─── Embed Builders ──────────────────────────────────────────────────────────

def build_dashboard_embed(data: dict, user: discord.User) -> discord.Embed:
    """Build the main dashboard embed."""
    greeting = random.choice(GREETINGS)

    embed = discord.Embed(
        title="🌶️  P E P P E R   S I M  🌶️",
        description=f"*\"{greeting}\"*",
        color=0x7CB342,
    )

    # Quick stats
    plots_used = len(data["plots"])
    total_inv = sum(data["inventory"].values())
    ready_count = sum(
        1 for p in data["plots"]
        if time.time() - p["planted_at"] >= PEPPERS[p["pepper"]]["grow_time"]
    )

    stats = (
        f"💰 Gold: {format_gold(data['gold'])}\n"
        f"🌾 Plots: {plots_used}/{MAX_PLOTS}\n"
        f"📦 Peppers in basket: {total_inv}\n"
    )
    if ready_count > 0:
        stats += f"🔔 **{ready_count} pepper(s) ready to harvest!**\n"

    embed.add_field(name="── Farm Overview ──", value=stats, inline=False)

    # Mini field preview
    if data["plots"]:
        field_lines = []
        for i, plot in enumerate(data["plots"]):
            field_lines.append(f"Plot {i+1}: {get_plot_status(plot)}")
        embed.add_field(name="── Your Fields ──", value="\n".join(field_lines), inline=False)
    else:
        embed.add_field(
            name="── Your Fields ──",
            value="*" + random.choice(EMPTY_FARM_MESSAGES) + "*",
            inline=False,
        )

    # Lifetime stats
    lifetime = (
        f"🌱 Total harvested: {data.get('total_harvested', 0)}\n"
        f"💸 Total sold: {data.get('total_sold', 0)}\n"
        f"🏦 Total earned: {format_gold(data.get('total_earned', 0))}"
    )
    embed.add_field(name="── Lifetime Stats ──", value=lifetime, inline=False)

    embed.set_footer(text="Use the buttons below to navigate! 🌿")
    embed.set_author(name=f"{user.display_name}'s Pepper Farm", icon_url=user.display_avatar.url)

    return embed


def build_farm_embed(data: dict, harvested: dict, user: discord.User, extra_msg: str = "") -> discord.Embed:
    """Build the farm view embed."""
    embed = discord.Embed(
        title="🌾  Y O U R   F A R M  🌾",
        color=0x558B2F,
    )

    # Show harvest results if any
    if harvested:
        harvest_lines = []
        for ptype, count in harvested.items():
            info = PEPPERS[ptype]
            msg = random.choice(HARVEST_MESSAGES).format(count=count, name=info["name"])
            harvest_lines.append(f"{info['emoji']} {msg}")
        embed.add_field(
            name="── 🎉 Auto-Harvest! ──",
            value="\n".join(harvest_lines),
            inline=False,
        )

    # Extra message (from planting, etc.)
    if extra_msg:
        embed.add_field(name="── Update ──", value=extra_msg, inline=False)

    # Field status
    if data["plots"]:
        field_lines = []
        for i, plot in enumerate(data["plots"]):
            field_lines.append(f"**Plot {i+1}:** {get_plot_status(plot)}")

        # Show empty plots
        empty = MAX_PLOTS - len(data["plots"])
        for i in range(empty):
            field_lines.append(f"**Plot {len(data['plots']) + i + 1}:** 🟫 *Empty — ready for seeds!*")

        embed.add_field(name="── Field Status ──", value="\n".join(field_lines), inline=False)
    else:
        lines = []
        for i in range(MAX_PLOTS):
            lines.append(f"**Plot {i+1}:** 🟫 *Empty — ready for seeds!*")
        embed.add_field(
            name="── Field Status ──",
            value="\n".join(lines),
            inline=False,
        )

    embed.add_field(
        name="── Seed Prices ──",
        value=(
            "🫑 Green: **10g** (30m grow)\n"
            "🌶️ Red: **25g** (1h grow)\n"
            "💛 Yellow: **50g** (2h grow)\n"
            "✨ Golden: **200g** (6h grow)"
        ),
        inline=False,
    )

    embed.set_footer(text=f"💰 Gold: {data['gold']:,}g  |  Plots: {len(data['plots'])}/{MAX_PLOTS}")
    embed.set_author(name=f"{user.display_name}'s Pepper Farm", icon_url=user.display_avatar.url)

    return embed


def build_store_embed(data: dict, user: discord.User, extra_msg: str = "") -> discord.Embed:
    """Build the store embed."""
    embed = discord.Embed(
        title="🏪  P I E R R E ' S   S E E D   S H O P  🏪",
        description="*\"Welcome, welcome! Only the finest seeds here at my shop!\"*",
        color=0x6D4C41,
    )

    if extra_msg:
        embed.add_field(name="── Update ──", value=extra_msg, inline=False)

    # Seed catalog
    for ptype, info in PEPPERS.items():
        value = (
            f"💰 Cost: **{info['seed_cost']}g**\n"
            f"📈 Sells for: **{info['sell_price']}g**\n"
            f"⏱️ Grow time: **{format_time(info['grow_time'])}**\n"
            f"*{info['description']}*"
        )
        embed.add_field(
            name=f"{info['emoji']} {info['name']} Seeds  ({info['rarity']})",
            value=value,
            inline=True,
        )

    embed.add_field(
        name="── 💡 Tip ──",
        value="*Buy seeds to automatically plant them in your next open plot! Peppers auto-harvest when ready, leaving the field open for new crops~*",
        inline=False,
    )

    embed.set_footer(text=f"💰 Your Gold: {data['gold']:,}g  |  Open Plots: {MAX_PLOTS - len(data['plots'])}/{MAX_PLOTS}")
    embed.set_author(name=f"{user.display_name}'s Shopping Trip", icon_url=user.display_avatar.url)

    return embed


def build_inventory_embed(data: dict, user: discord.User, extra_msg: str = "") -> discord.Embed:
    """Build the inventory/sell embed."""
    embed = discord.Embed(
        title="📦  P E P P E R   B A S K E T  📦",
        description="*\"Let's see what we've got in the ol' harvest basket...\"*",
        color=0xE65100,
    )

    if extra_msg:
        embed.add_field(name="── Update ──", value=extra_msg, inline=False)

    # Inventory listing
    inv_lines = []
    total_value = 0
    for ptype, count in data["inventory"].items():
        info = PEPPERS[ptype]
        value = count * info["sell_price"]
        total_value += value
        if count > 0:
            inv_lines.append(
                f"{info['emoji']} **{info['name']}** x{count}  →  {format_gold(value)}"
            )
        else:
            inv_lines.append(
                f"{info['emoji']} {info['name']}  —  *none*"
            )

    embed.add_field(
        name="── Your Peppers ──",
        value="\n".join(inv_lines),
        inline=False,
    )

    embed.add_field(
        name="── Total Value ──",
        value=f"💰 Basket worth: {format_gold(total_value)}\n🏦 Your gold: {format_gold(data['gold'])}",
        inline=False,
    )

    embed.set_footer(text="Hit a sell button to sell those peppers for gold! 💸")
    embed.set_author(name=f"{user.display_name}'s Basket", icon_url=user.display_avatar.url)

    return embed


def format_time(seconds: int) -> str:
    if seconds >= 3600:
        h = seconds // 3600
        return f"{h}h"
    return f"{seconds // 60}m"


# ─── Slash Command ────────────────────────────────────────────────────────────

@bot.tree.command(name="pep", description="Open your Pepper Farm dashboard!")
async def pep_command(interaction: discord.Interaction):
    data = load_user(interaction.user.id)
    harvested = check_harvests(data)
    save_user(interaction.user.id, data)

    embed = build_dashboard_embed(data, interaction.user)
    view = DashboardView(interaction.user.id)

    # If there were auto-harvested peppers, mention it
    if harvested:
        harvest_note = "🎉 **Auto-Harvest!** "
        parts = []
        for ptype, count in harvested.items():
            info = PEPPERS[ptype]
            parts.append(f"{info['emoji']} {count}x {info['name']}")
        harvest_note += ", ".join(parts) + " collected!"
        embed.insert_field_at(
            0,
            name="── 🔔 Welcome Back! ──",
            value=harvest_note,
            inline=False,
        )

    await interaction.response.send_message(embed=embed, view=view)


# ─── Bot Events ──────────────────────────────────────────────────────────────

@bot.event
async def on_ready():
    print(f"🌶️  Pepper Sim is online as {bot.user}!")
    print(f"    Serving {len(bot.guilds)} server(s)")
    try:
        synced = await bot.tree.sync()
        print(f"    Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"    Failed to sync commands: {e}")

    # Set the bot's status
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.playing,
            name="🌶️ /pep to farm peppers!",
        )
    )


# ─── Run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not TOKEN:
        print("=" * 50)
        print("🌶️  PEPPER SIM - Setup Required!")
        print("=" * 50)
        print()
        print("To run the bot, set your Discord bot token:")
        print()
        print("  Option 1: Environment variable")
        print("    set DISCORD_TOKEN=your-token-here")
        print("    python bot.py")
        print()
        print("  Option 2: Create a .env file")
        print("    DISCORD_TOKEN=your-token-here")
        print()
        print("Need a bot token? Visit:")
        print("  https://discord.com/developers/applications")
        print()
        print("Bot setup checklist:")
        print("  1. Create a New Application")
        print("  2. Go to Bot → Reset Token → Copy it")
        print("  3. Enable MESSAGE CONTENT INTENT")
        print("  4. Go to OAuth2 → URL Generator")
        print("     - Scopes: bot, applications.commands")
        print("     - Permissions: Send Messages, Embed Links,")
        print("       Attach Files, Use Slash Commands")
        print("  5. Use the generated URL to invite the bot")
        print("  6. Set the bot's name to 'Pepper Sim'")
        print("=" * 50)
    else:
        bot.run(TOKEN)
