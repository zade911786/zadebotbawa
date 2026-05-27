#!/usr/bin/env python3
# zade_bot.py — Zade Bot | Full Featured | TeleBotHosting Compatible

import asyncio, logging, random, string, time, os, tempfile, json, re
import aiosqlite
from datetime import date, datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

# ══════════════════════════════════════════════════════════════════
#  CONFIG
# ══════════════════════════════════════════════════════════════════
BOT_TOKEN   = "8315289537:AAGLNZPa071C9S5Itqmv-j_Io5UHWQMp2cY"
OWNER_ID    = 8558910409          # @Zade4everbot owner
BOT_NAME    = "Zade"
DB_PATH     = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zade.db")
GIPHY_KEY   = "AnmLxIBujSGw3V5ejU1K7KqD9Aggp6YH"   # Replace with real Giphy key

DAILY_AMOUNT        = 2000
DAILY_GEMS_PREMIUM  = 100

ROB_MAX_NORMAL    = 10_000
ROB_MAX_PREMIUM   = 100_000
ROB_TAX_NORMAL    = 0.10
ROB_TAX_PREMIUM   = 0.05
GIVE_TAX_NORMAL   = 0.10
GIVE_TAX_PREMIUM  = 0.05

KILL_REWARD_NORMAL  = (100, 200)
KILL_REWARD_PREMIUM = (200, 400)
KILL_XP_NORMAL      = (0, 5)
KILL_XP_PREMIUM     = (5, 10)
ROB_XP              = (0, 100)

ROB_KILL_LIMIT_NORMAL  = 200
ROB_KILL_LIMIT_PREMIUM = 400
PROTECT_COST_PER_DAY   = 500
CLAIM_GROUP_REWARD     = 10_000
REVIVE_COST            = 300    # cost deducted on /revive

PREMIUM_PRICES = {"24h": 5_000, "48h": 9_000, "7d": 25_000}

# XP Shop — items purchasable with XP
XP_SHOP = {
    "kill_shield":  {"xp": 500,  "desc": "Kill anyone even if protected (1 use)"},
    "double_rob":   {"xp": 300,  "desc": "Double next rob reward (1 use)"},
    "revive_free":  {"xp": 200,  "desc": "Revive for free (1 use)"},
}

AVAILABLE_VOICES = {
    "guy":         "en-US-GuyNeural",
    "christopher": "en-US-ChristopherNeural",
    "eric":        "en-US-EricNeural",
    "aria":        "en-US-AriaNeural",
    "jenny":       "en-US-JennyNeural",
    "ryan":        "en-GB-RyanNeural",
    "sonia":       "en-GB-SoniaNeural",
    "natasha":     "en-AU-NatashaNeural",
    "william":     "en-AU-WilliamNeural",
}

VOICE_DEMOS = {
    "guy":         "Hello, I'm Guy. A confident American voice.",
    "christopher": "Hello, I'm Christopher. Deep and authoritative.",
    "eric":        "Hey there! Eric here, friendly and casual.",
    "aria":        "Hi! I'm Aria, warm and expressive.",
    "jenny":       "Hello, I'm Jenny — clear and professional.",
    "ryan":        "Hiya, Ryan here with a British accent.",
    "sonia":       "Hello, I'm Sonia, a British female voice.",
    "natasha":     "G'day! Natasha here with an Aussie accent.",
    "william":     "Hello, I'm William — Australian and deep.",
}

logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)

# ══════════════════════════════════════════════════════════════════
#  DATABASE
# ══════════════════════════════════════════════════════════════════
async def init_db():
    async with aiosqlite.connect(DB_PATH) as d:
        await d.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id         INTEGER PRIMARY KEY,
            username        TEXT,
            first_name      TEXT DEFAULT 'User',
            balance         INTEGER DEFAULT 500,
            gems            INTEGER DEFAULT 0,
            xp              INTEGER DEFAULT 0,
            kills           INTEGER DEFAULT 0,
            is_alive        INTEGER DEFAULT 1,
            is_premium      INTEGER DEFAULT 0,
            premium_until   INTEGER DEFAULT 0,
            protected_until INTEGER DEFAULT 0,
            last_daily      INTEGER DEFAULT 0,
            rob_count       INTEGER DEFAULT 0,
            kill_count      INTEGER DEFAULT 0,
            started_bot     INTEGER DEFAULT 0,
            custom_sticker  TEXT DEFAULT NULL,
            custom_sticker_name TEXT DEFAULT NULL,
            xp_items        TEXT DEFAULT '{}'
        );
        CREATE TABLE IF NOT EXISTS username_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER,
            username    TEXT,
            changed_at  INTEGER
        );
        CREATE TABLE IF NOT EXISTS group_join (
            user_id  INTEGER,
            group_id INTEGER,
            joined_at INTEGER,
            PRIMARY KEY (user_id, group_id)
        );
        CREATE TABLE IF NOT EXISTS coupons (
            code        TEXT PRIMARY KEY,
            group_id    INTEGER UNIQUE,
            created_by  INTEGER,
            reward      INTEGER DEFAULT 500,
            max_claims  INTEGER DEFAULT 50,
            claims      INTEGER DEFAULT 0,
            created_at  INTEGER
        );
        CREATE TABLE IF NOT EXISTS coupon_claims (
            coupon_code TEXT,
            user_id     INTEGER,
            PRIMARY KEY (coupon_code, user_id)
        );
        CREATE TABLE IF NOT EXISTS group_settings (
            group_id    INTEGER PRIMARY KEY,
            tts_voice   TEXT DEFAULT 'en-US-GuyNeural',
            added_by    INTEGER,
            added_at    INTEGER,
            admin_tax_wallet INTEGER DEFAULT NULL
        );
        CREATE TABLE IF NOT EXISTS tax_wallet (
            group_id INTEGER PRIMARY KEY,
            balance  INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS clone_ids (
            clone_id    TEXT PRIMARY KEY,
            created_by  INTEGER,
            created_at  INTEGER,
            used        INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS daily_earnings (
            user_id INTEGER,
            date    TEXT,
            amount  INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, date)
        );
        CREATE TABLE IF NOT EXISTS img_credits (
            user_id  INTEGER PRIMARY KEY,
            credits  INTEGER DEFAULT 10,
            last_reset TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS img2_credits (
            user_id  INTEGER PRIMARY KEY,
            credits  INTEGER DEFAULT 2,
            last_reset TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS img3_credits (
            user_id  INTEGER PRIMARY KEY,
            credits  INTEGER DEFAULT 2,
            last_reset TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS img4_credits (
            user_id  INTEGER PRIMARY KEY,
            credits  INTEGER DEFAULT 2,
            last_reset TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS img5_credits (
            user_id  INTEGER PRIMARY KEY,
            credits  INTEGER DEFAULT 2,
            last_reset TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS img6_credits (
            user_id  INTEGER PRIMARY KEY,
            credits  INTEGER DEFAULT 2,
            last_reset TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS imgpro_credits (
            user_id  INTEGER PRIMARY KEY,
            credits  INTEGER DEFAULT 2,
            last_reset TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS shop_items (
            item_id     TEXT PRIMARY KEY,
            name        TEXT,
            description TEXT,
            price       INTEGER,
            active      INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS user_inventory (
            user_id  INTEGER,
            item_id  TEXT,
            quantity INTEGER DEFAULT 1,
            PRIMARY KEY (user_id, item_id)
        );
        INSERT OR IGNORE INTO shop_items VALUES
            ('vip_badge','⭐ VIP Badge','Show a VIP badge on your profile',5000,1),
            ('lucky_rob','🍀 Lucky Rob','Next rob = 2x loot (1 use)',3000,1),
            ('bomb','💣 Bomb','Kill target without combat check (1 use)',8000,1),
            ('shield_1d','🛡️ Shield 1D','1 day protection',1500,1),
            ('img_5','🎨 5 Image Credits','Buy 5 extra image gen credits',2500,1),
            ('img_15','🎨 15 Image Credits','Buy 15 extra image gen credits',6000,1),
            ('img_30','🎨 30 Image Credits','Buy 30 extra image gen credits',10000,1),
            ('mystery_box','🎁 Mystery Box','Random reward: cash, credits, items or jackpot!',4000,1);
        """)
        await d.commit()

async def get_user(uid, username=None, first_name=None):
    async with aiosqlite.connect(DB_PATH) as d:
        d.row_factory = aiosqlite.Row
        async with d.execute("SELECT * FROM users WHERE user_id=?", (uid,)) as c:
            u = await c.fetchone()
        if not u:
            await d.execute(
                "INSERT INTO users (user_id,username,first_name) VALUES (?,?,?)",
                (uid, username, first_name or "User")
            )
            await d.commit()
            async with d.execute("SELECT * FROM users WHERE user_id=?", (uid,)) as c:
                u = await c.fetchone()
        else:
            if username and u["username"] and username != u["username"]:
                await d.execute(
                    "INSERT INTO username_history (user_id,username,changed_at) VALUES (?,?,?)",
                    (uid, u["username"], int(time.time()))
                )
                await d.execute(
                    "UPDATE users SET username=?,first_name=? WHERE user_id=?",
                    (username, first_name or u["first_name"], uid)
                )
                await d.commit()
        return dict(u)

async def upd(uid, **kw):
    async with aiosqlite.connect(DB_PATH) as d:
        sets = ", ".join(f"{k}=?" for k in kw)
        await d.execute(f"UPDATE users SET {sets} WHERE user_id=?", [*kw.values(), uid])
        await d.commit()

async def add_bal(uid, amount):
    async with aiosqlite.connect(DB_PATH) as d:
        await d.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (amount, uid))
        await d.commit()

async def is_premium(uid):
    async with aiosqlite.connect(DB_PATH) as d:
        async with d.execute("SELECT is_premium,premium_until FROM users WHERE user_id=?", (uid,)) as c:
            r = await c.fetchone()
    return bool(r and r[0] and r[1] > int(time.time()))

async def get_top_rich(n=10):
    async with aiosqlite.connect(DB_PATH) as d:
        d.row_factory = aiosqlite.Row
        async with d.execute("SELECT * FROM users ORDER BY balance DESC LIMIT ?", (n,)) as c:
            return [dict(r) for r in await c.fetchall()]

async def get_top_kills(n=10):
    async with aiosqlite.connect(DB_PATH) as d:
        d.row_factory = aiosqlite.Row
        async with d.execute("SELECT * FROM users ORDER BY kills DESC LIMIT ?", (n,)) as c:
            return [dict(r) for r in await c.fetchall()]

async def record_earn(uid, amount):
    today = str(date.today())
    async with aiosqlite.connect(DB_PATH) as d:
        await d.execute(
            "INSERT INTO daily_earnings(user_id,date,amount) VALUES(?,?,?) "
            "ON CONFLICT(user_id,date) DO UPDATE SET amount=amount+?",
            (uid, today, amount, amount)
        )
        await d.commit()

async def lb_top10(n=10):
    async with aiosqlite.connect(DB_PATH) as d:
        d.row_factory = aiosqlite.Row
        async with d.execute(
            "SELECT * FROM users ORDER BY balance DESC LIMIT ?", (n,)
        ) as c:
            return [dict(r) for r in await c.fetchall()]

async def get_group_voice(gid):
    async with aiosqlite.connect(DB_PATH) as d:
        async with d.execute("SELECT tts_voice FROM group_settings WHERE group_id=?", (gid,)) as c:
            r = await c.fetchone()
    return r[0] if r else "en-US-GuyNeural"

async def set_group_voice(gid, voice):
    async with aiosqlite.connect(DB_PATH) as d:
        await d.execute(
            "INSERT INTO group_settings(group_id,tts_voice) VALUES(?,?) "
            "ON CONFLICT(group_id) DO UPDATE SET tts_voice=?",
            (gid, voice, voice)
        )
        await d.commit()

async def register_group(gid, uid):
    async with aiosqlite.connect(DB_PATH) as d:
        await d.execute(
            "INSERT OR IGNORE INTO group_settings(group_id,added_by,added_at) VALUES(?,?,?)",
            (gid, uid, int(time.time()))
        )
        await d.commit()

async def group_claimer(gid):
    async with aiosqlite.connect(DB_PATH) as d:
        async with d.execute("SELECT added_by FROM group_settings WHERE group_id=?", (gid,)) as c:
            r = await c.fetchone()
    return r[0] if r else None

async def add_tax(gid, amount):
    async with aiosqlite.connect(DB_PATH) as d:
        await d.execute(
            "INSERT INTO tax_wallet(group_id,balance) VALUES(?,?) "
            "ON CONFLICT(group_id) DO UPDATE SET balance=balance+?",
            (gid, amount, amount)
        )
        await d.commit()

async def get_tax(gid):
    async with aiosqlite.connect(DB_PATH) as d:
        async with d.execute("SELECT balance FROM tax_wallet WHERE group_id=?", (gid,)) as c:
            r = await c.fetchone()
    return r[0] if r else 0

async def create_coupon(code, gid, uid, reward, max_claims):
    async with aiosqlite.connect(DB_PATH) as d:
        async with d.execute("SELECT code FROM coupons WHERE group_id=?", (gid,)) as c:
            ex = await c.fetchone()
        if ex:
            return False, ex[0]
        await d.execute(
            "INSERT INTO coupons(code,group_id,created_by,reward,max_claims,created_at) VALUES(?,?,?,?,?,?)",
            (code, gid, uid, reward, max_claims, int(time.time()))
        )
        await d.commit()
        return True, code

async def claim_coupon(code, uid, gid):
    async with aiosqlite.connect(DB_PATH) as d:
        d.row_factory = aiosqlite.Row
        async with d.execute("SELECT * FROM coupons WHERE code=? AND group_id=?", (code, gid)) as c:
            cp = await c.fetchone()
        if not cp:
            return False, "❌ Invalid coupon for this group."
        cp = dict(cp)
        if cp["claims"] >= cp["max_claims"]:
            return False, "❌ Coupon fully claimed."
        async with d.execute("SELECT 1 FROM coupon_claims WHERE coupon_code=? AND user_id=?", (code, uid)) as c:
            if await c.fetchone():
                return False, "❌ Already claimed."
        await d.execute("INSERT INTO coupon_claims(coupon_code,user_id) VALUES(?,?)", (code, uid))
        await d.execute("UPDATE coupons SET claims=claims+1 WHERE code=?", (code,))
        await d.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (cp["reward"], uid))
        await d.commit()
        return True, cp["reward"]

async def delete_coupon(gid, uid):
    async with aiosqlite.connect(DB_PATH) as d:
        async with d.execute("SELECT code,created_by FROM coupons WHERE group_id=?", (gid,)) as c:
            cp = await c.fetchone()
        if not cp:
            return False, "No coupon for this group."
        if cp[1] != uid and uid != OWNER_ID:
            return False, "Only coupon creator or bot owner can delete."
        await d.execute("DELETE FROM coupons WHERE group_id=?", (gid,))
        await d.commit()
        return True, cp[0]

async def coupon_status(gid):
    async with aiosqlite.connect(DB_PATH) as d:
        d.row_factory = aiosqlite.Row
        async with d.execute("SELECT * FROM coupons WHERE group_id=?", (gid,)) as c:
            r = await c.fetchone()
    return dict(r) if r else None

async def get_uname_history(uid):
    async with aiosqlite.connect(DB_PATH) as d:
        d.row_factory = aiosqlite.Row
        async with d.execute(
            "SELECT * FROM username_history WHERE user_id=? ORDER BY changed_at DESC LIMIT 10", (uid,)
        ) as c:
            return [dict(r) for r in await c.fetchall()]

async def get_group_join(uid, gid):
    async with aiosqlite.connect(DB_PATH) as d:
        async with d.execute("SELECT joined_at FROM group_join WHERE user_id=? AND group_id=?", (uid, gid)) as c:
            r = await c.fetchone()
    return r[0] if r else None

async def set_group_join(uid, gid):
    async with aiosqlite.connect(DB_PATH) as d:
        await d.execute(
            "INSERT OR IGNORE INTO group_join(user_id,group_id,joined_at) VALUES(?,?,?)",
            (uid, gid, int(time.time()))
        )
        await d.commit()

async def get_user_position(gid, uid):
    """Get rank of user by balance."""
    async with aiosqlite.connect(DB_PATH) as d:
        async with d.execute("SELECT COUNT(*)+1 FROM users WHERE balance > (SELECT balance FROM users WHERE user_id=?)", (uid,)) as c:
            r = await c.fetchone()
    return r[0] if r else "?"

async def gen_clone_id():
    code = "ZADE-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    async with aiosqlite.connect(DB_PATH) as d:
        await d.execute(
            "INSERT INTO clone_ids(clone_id,created_by,created_at) VALUES(?,?,?)",
            (code, OWNER_ID, int(time.time()))
        )
        await d.commit()
    return code

async def validate_clone_id(code):
    async with aiosqlite.connect(DB_PATH) as d:
        async with d.execute("SELECT used FROM clone_ids WHERE clone_id=?", (code,)) as c:
            r = await c.fetchone()
        if r and r[0] == 0:
            await d.execute("UPDATE clone_ids SET used=1 WHERE clone_id=?", (code,))
            await d.commit()
            return True
    return False

async def get_active_groups():
    async with aiosqlite.connect(DB_PATH) as d:
        d.row_factory = aiosqlite.Row
        async with d.execute("SELECT * FROM group_settings") as c:
            return [dict(r) for r in await c.fetchall()]

# ══════════════════════════════════════════════════════════════════
#  UTILS
# ══════════════════════════════════════════════════════════════════
def mention(user):
    name = (user.first_name or user.username or "User")[:20]
    return f'<a href="tg://user?id={user.id}">{name}</a>'

def mentionD(first_name, uid, username=None):
    name = (first_name or username or "User")[:20]
    return f'<a href="tg://user?id={uid}">{name}</a>'

def cash(n): return f"${n:,}"
def is_group(update): return update.effective_chat.type in ("group", "supergroup")

async def is_admin(update, uid):
    try:
        m = await update.effective_chat.get_member(uid)
        return m.status in ("administrator", "creator")
    except:
        return False

def rnd_code(n=8): return "".join(random.choices(string.ascii_uppercase + string.digits, k=n))

async def giphy_random(tag="money"):
    """Fetch random GIF from Giphy."""
    try:
        import aiohttp
        url = f"https://api.giphy.com/v1/gifs/random?api_key={GIPHY_KEY}&tag={tag}&rating=pg-13"
        async with aiohttp.ClientSession() as s:
            async with s.get(url) as r:
                data = await r.json()
                return data["data"]["images"]["original"]["url"]
    except:
        return None

async def send_with_gif(update, text, tag="money"):
    gif_url = await giphy_random(tag)
    if gif_url:
        try:
            await update.message.reply_animation(animation=gif_url, caption=text, parse_mode="HTML")
            return
        except:
            pass
    await update.message.reply_text(text, parse_mode="HTML")

def get_xp_items(user):
    try:
        return json.loads(user.get("xp_items") or "{}")
    except:
        return {}

async def save_xp_items(uid, items):
    await upd(uid, xp_items=json.dumps(items))

# ══════════════════════════════════════════════════════════════════
#  SOCIAL MESSAGES
# ══════════════════════════════════════════════════════════════════
SOCIAL = {
    "slap":    ["{a} slapped {b} so hard the room shook! 👋💥", "{a} gave {b} a legendary slap! 😤", "{a} SLAPPED {b} into next week 😂"],
    "hug":     ["{a} hugged {b} tightly! 🤗", "{a} gave {b} the warmest hug 💕", "{a} won't let go of {b}! 😊"],
    "kiss":    ["{a} kissed {b}! 😘💋", "{a} gave {b} a sweet kiss 💗", "{a} smoooched {b}! 😚"],
    "punch":   ["{a} punched {b} right in the face! 👊💥", "{a} threw a haymaker at {b}! 😤", "{a} decked {b}! BOOM 💥"],
    "bite":    ["{a} bit {b}! Ow! 😬", "{a} took a chomp out of {b}! 🦷", "{a} bit {b} like a snack 😂"],
    "love":    ["{a} is totally in love with {b}! 💘", "{a} sent love to {b}! 💝", "{a} ❤️ {b}"],
    "look":    ["{a} is staring at {b}... 👀", "{a} can't stop looking at {b} 😳", "{a} gave {b} a long look 👁️"],
    "crush":   ["{a} has a crush on {b}! 🙈💗", "{a} is blushing around {b}! 😊", "Looks like {a} likes {b}... 💕"],
    "murder":  ["{a} tried to murder {b}! 🗡️💀", "{a} went full villain on {b} 😈", "{a} plotted against {b}! 🔪"],
    "pat":     ["{a} gently patted {b} on the head! 🥹", "{a} gave {b} the most wholesome head pat 🤍", "{a} patted {b} like a good boi 😊"],
    "poke":    ["{a} poked {b}! Hey! 👉", "{a} keeps poking {b}... 😅", "{a} aggressively poked {b} 😂"],
    "tickle":  ["{a} tickled {b} mercilessly! 🤣", "{a} found {b}'s tickle spot! 😂", "{a} tickled {b} until they cried! 🤭"],
    "wave":    ["{a} waved at {b}! 👋😊", "{a} is waving hello to {b}!", "Hey {b}, {a} is waving at you! 👋"],
    "wink":    ["{a} winked at {b}! 😉", "{a} gave {b} a cheeky wink 😏", "{a} winked... {b} is shook 😳"],
    "cry":     ["{a} is crying because of {b}! 😭", "{a} sobbed all over {b} 😢💧", "{a} ugly cried on {b}'s shoulder 😭"],
    "laugh":   ["{a} burst out laughing at {b}! 😂", "{a} can't stop laughing at {b} 🤣", "{a} is on the floor laughing at {b} 😂"],
    "dance":   ["{a} is dancing with {b}! 💃🕺", "{a} dragged {b} to the dance floor! 🎶", "{a} and {b} are vibing! 🕺"],
    "cuddle":  ["{a} cuddled up to {b}! 🥰", "{a} and {b} are cuddling aww 💕", "{a} wrapped {b} in a cozy cuddle 🤍"],
    "highfive":["{a} high-fived {b}! ✋🤚", "{a} and {b} nailed the high five! 🙌", "SLAP! {a} high-fived {b}! 🙌"],
    "throw":   ["{a} threw something at {b}! 🤾💥", "{a} launched {b} across the room! 😂", "{a} YEET'd {b}! 🚀"],
}

SOCIAL_GIPHY = {
    "slap":     "anime slap",
    "hug":      "anime hug",
    "kiss":     "anime kiss",
    "punch":    "anime punch",
    "bite":     "anime bite",
    "love":     "anime love",
    "look":     "anime stare",
    "crush":    "anime blush",
    "murder":   "anime kill",
    "pat":      "anime pat head",
    "poke":     "anime poke",
    "tickle":   "anime tickle",
    "wave":     "anime wave",
    "wink":     "anime wink",
    "cry":      "anime cry",
    "laugh":    "anime laugh",
    "dance":    "anime dance",
    "cuddle":   "anime cuddle",
    "highfive": "anime high five",
    "throw":    "anime yeet",
}

# Economy/combat GIF tags
GIF_TAGS = {
    "rob":   "steal money",
    "kill":  "anime fight",
    "daily": "cash money",
}

# ══════════════════════════════════════════════════════════════════
#  INLINE KEYBOARDS
# ══════════════════════════════════════════════════════════════════
def _b(text, *, cb=None, url=None, style=None):
    """Build a single raw button dict with optional style (Bot API 9.4+)."""
    btn = {"text": text}
    if cb:   btn["callback_data"] = cb
    if url:  btn["url"] = url
    if style: btn["style"] = style
    return btn

def _rm(*rows):
    """Build raw InlineKeyboardMarkup JSON string from rows of _b() dicts."""
    import json as _j
    return _j.dumps({"inline_keyboard": list(rows)})

def kb_start(bot_username=""):
    add_url = f"https://t.me/{bot_username}?startgroup=true" if bot_username else "https://t.me/"
    return _rm(
        [_b("💰 Balance", cb="cb_bal", style="primary"),   _b("📋 Help", cb="cb_help", style="primary")],
        [_b("🏆 Leaderboard", cb="cb_lb", style="primary"), _b("👑 Premium", cb="cb_premium", style="success")],
        [_b("🏪 Shop", cb="cb_shop", style="primary"),      _b("➕ Add to Group", url=add_url)],
        [_b("🤖 Owner", url="https://t.me/Zade4everbot")],
    )

def kb_help():
    return _rm(
        [_b("💰 Economy", cb="help_economy", style="primary"),  _b("⚔️ Combat", cb="help_combat", style="danger")],
        [_b("🎭 Social", cb="help_social", style="primary"),    _b("🔧 Utility", cb="help_utility", style="primary")],
        [_b("🏆 Leaderboard", cb="help_lb", style="primary"),   _b("🎟️ Coupons", cb="help_coupon", style="primary")],
        [_b("👑 Premium", cb="help_premium", style="success"),  _b("🛠️ Admin", cb="help_admin", style="danger")],
        [_b("🤖 Clone This Bot", cb="help_clone", style="success")],
        [_b("« Back", cb="cb_start")],
    )

def kb_voices():
    import json as _j
    rows = []
    keys = list(AVAILABLE_VOICES.keys())
    for i in range(0, len(keys), 2):
        row = [_b(f"🔊 {keys[i].title()}", cb=f"voice_demo_{keys[i]}", style="primary")]
        if i+1 < len(keys):
            row.append(_b(f"🔊 {keys[i+1].title()}", cb=f"voice_demo_{keys[i+1]}", style="primary"))
        rows.append(row)
    rows.append([_b("« Back", cb="cb_start")])
    return _j.dumps({"inline_keyboard": rows})

def kb_premium():
    return _rm(
        [_b("⚡ 24h — $5,000", cb="buy_24h", style="success"), _b("💫 48h — $9,000", cb="buy_48h", style="success")],
        [_b("👑 7 Days — $25,000", cb="buy_7d", style="success")],
        [_b("« Back", cb="cb_start")],
    )

def kb_lb():
    return _rm(
        [_b("💰 Top Balance", cb="lb_balance", style="primary"), _b("⚔️ Top Kills", cb="lb_kills", style="danger")],
        [_b("« Back", cb="cb_start")],
    )

def kb_panel():
    return _rm(
        [_b("📊 Active Groups", cb="panel_groups", style="primary"), _b("🔑 Gen Clone ID", cb="panel_genid", style="success")],
        [_b("💸 Broadcast", cb="panel_broadcast", style="danger"),   _b("📈 Stats", cb="panel_stats", style="primary")],
    )

def kb_xp_shop():
    import json as _j
    rows = []
    for key, item in XP_SHOP.items():
        rows.append([_b(f"🛒 {item['desc'][:30]} — {item['xp']} XP", cb=f"xpbuy_{key}", style="success")])
    rows.append([_b("« Back", cb="cb_start")])
    return _j.dumps({"inline_keyboard": rows})

# ══════════════════════════════════════════════════════════════════
#  HANDLERS — START / HELP
# ══════════════════════════════════════════════════════════════════
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    user = await get_user(u.id, u.username, u.first_name)
    prem = await is_premium(u.id)
    badge = "💓 Premium" if prem else "👤 Free"

    if not user["started_bot"]:
        await upd(u.id, started_bot=1)
        # Notify owner about new user
        try:
            chat_info = ""
            if update.effective_chat and update.effective_chat.id != u.id:
                chat_info = f"\n📍 Chat: <code>{update.effective_chat.id}</code>"
            await ctx.bot.send_message(
                OWNER_ID,
                f"🔔 <b>New Bot Start!</b>\n\n"
                f"👤 {mention(u)}\n"
                f"🆔 <code>{u.id}</code>\n"
                f"📛 @{u.username or 'no_username'}{chat_info}",
                parse_mode="HTML"
            )
        except:
            pass
        await update.message.reply_text(
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚡ <b>Welcome to {BOT_NAME} Bot!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Hey {mention(u)}! 👋\n\n"
            f"I'm an advanced <b>economy & combat</b> bot.\n"
            f"Rob, kill, earn, trade — dominate the leaderboard!\n\n"
            f"🎁 <b>Starting balance:</b> $500\n"
            f"💰 Use /daily to claim <b>$2,000</b> right now!\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📋 /help — All commands\n"
            f"💰 /daily — Free daily cash\n"
            f"⚔️ /kill — Eliminate enemies\n"
            f"👑 /pay — Upgrade to Premium\n"
            f"━━━━━━━━━━━━━━━━━━━━━━",
            parse_mode="HTML",
            reply_markup=kb_start(ctx.bot.username)
        )
        return

    prot_txt = ""
    if user["protected_until"] > int(time.time()):
        rem = user["protected_until"] - int(time.time())
        h, m = divmod(rem // 60, 60)
        prot_txt = f"\n  🛡️ Protected  <b>{h}h {m}m left</b>"

    alive_txt = "✅  Alive" if user["is_alive"] else "💀  Dead — /revive"
    prem_tag  = "  ✦ 💓 PREMIUM" if prem else ""

    prem_line = "\n✦ <b>PREMIUM MEMBER</b> 💓" if prem else ""
    await update.message.reply_text(
        f"⚡ <b>ZADE BOT</b> — Dashboard{prem_line}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 {mention(u)}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💵 Balance  ›  <b>{cash(user['balance'])}</b>\n"
        f"💎 Gems     ›  <b>{user['gems']}</b>\n"
        f"🏅 XP       ›  <b>{user['xp']}</b>\n"
        f"⚔️ Kills    ›  <b>{user['kills']}</b>\n"
        f"❤️ Status   ›  {alive_txt}{prot_txt}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━",
        parse_mode="HTML",
        reply_markup=kb_start(ctx.bot.username)
    )

def help_economy_text():
    return (
        "💰 <b>Economy Commands</b>\n\n"
        "<code>/daily</code> — Claim $2,000 daily\n"
        "<code>/bal</code> — Check your balance\n"
        "<code>/give &lt;amount&gt;</code> — Send money (reply) + tax breakdown\n"
        "<code>/rob</code> — Rob someone (reply)\n"
        "<code>/pay 24h|48h|7d</code> — Buy premium\n"
        "<code>/protect 1d|2d|3d</code> — Buy protection\n"
        "<code>/xpshop</code> — Spend XP on items\n"
    )

def help_combat_text():
    return (
        "⚔️ <b>Combat Commands</b>\n\n"
        "<code>/kill</code> — Kill someone (reply)\n"
        "<code>/revive</code> — Revive (costs " + cash(REVIVE_COST) + ")\n"
        "<code>/check</code> — Check protection status 💓\n"
        "<code>/protect 1d|2d|3d</code> — Shield yourself\n\n"
        "💡 <i>XP Shop: buy kill_shield to bypass protection!</i>\n"
    )

def help_social_text():
    return (
        "🎭 <b>Social Commands</b>\n\n"
        "<code>/slap</code> 👋  <code>/hug</code> 🤗  <code>/kiss</code> 😘  <code>/punch</code> 👊\n"
        "<code>/bite</code> 🦷  <code>/love</code> 💘  <code>/look</code> 👀  <code>/crush</code> 🙈\n"
        "<code>/murder</code> 🗡️  <code>/pat</code> 🥹  <code>/poke</code> 👉  <code>/tickle</code> 🤣\n"
        "<code>/wave</code> 👋  <code>/wink</code> 😉  <code>/cry</code> 😭  <code>/laugh</code> 😂\n"
        "<code>/dance</code> 💃  <code>/cuddle</code> 🥰  <code>/highfive</code> 🙌  <code>/throw</code> 🚀\n\n"
        "↩️ <i>Reply to a user to use any social command.</i>\n"
    )

def help_utility_text():
    return (
        "🔧 <b>Utility Commands</b>\n\n"
        "<code>/tr &lt;text&gt;</code> — Translate (Google Translate)\n"
        "<code>/tts &lt;text&gt;</code> — Text to speech\n"
        "<code>/voices</code> — View TTS voices with demo\n"
        "<code>/admins</code> — List group admins\n"
        "<code>/owner</code> — Tag group owner\n"
        "<code>/details</code> — Full user profile + join date + position\n"
        "<code>/setsticker &lt;name&gt;</code> — Set custom sticker (reply to sticker, premium)\n"
        "<code>/img &lt;prompt&gt;</code> — Generate AI image (groups only)\n"
        "<code>/imgcredits</code> — Check your image credits\n"
        "<code>/shop</code> — Cash shop — buy items with balance\n"
        "<code>/inv</code> — Your inventory\n"
        "<code>/use &lt;item&gt;</code> — Use an item from inventory\n"
    )

def help_lb_text():
    return (
        "🏆 <b>Leaderboard</b>\n\n"
        "<code>/lb</code> — Top 10 richest users\n"
        "<code>/topkill</code> — Top 10 killers\n"
    )

def help_coupon_text():
    return (
        "🎟️ <b>Coupons</b> (Group admins only)\n\n"
        "<code>/create_coupon &lt;reward&gt; &lt;max&gt;</code> — Create coupon\n"
        "<code>/coupon &lt;code&gt;</code> — Claim coupon\n"
        "<code>/del_coupon</code> — Delete coupon\n"
        "<code>/status</code> — Coupon status\n"
        "<code>/claim</code> — Claim group reward\n"
    )

def help_premium_text():
    return (
        "👑 <b>Premium Perks</b>\n\n"
        "• 2× rewards on rob & kill\n"
        "• Lower tax (5% vs 10%)\n"
        "• Higher rob cap ($100K vs $10K)\n"
        "• 100 💎 Gems per daily\n"
        "• 2d/3d protection access\n"
        "• Custom sticker with <code>/setsticker</code>\n\n"
        "<code>/pay 24h|48h|7d</code> — Buy premium\n"
    )

def help_admin_text():
    return (
        "🛠️ <b>Admin Commands</b>\n\n"
        "<code>/addbal &lt;amount&gt;</code> — Add balance (reply or user_id) — Owner only\n"
        "<code>/dedbal &lt;amount&gt;</code> — Deduct balance (reply or user_id) — Owner only\n"
        "<code>/addcredits &lt;amount&gt;</code> — Give image credits (reply or user_id) — Owner only\n"
        "<code>/taxbal</code> — Check group tax wallet — Admin only\n"
        "<code>/withdrawtax</code> — Withdraw tax to balance — Admin only\n"
        "<code>/create_coupon</code> — Create group coupon — Admin only\n"
        "<code>/set_tts &lt;voice&gt;</code> — Set TTS voice — Admin only\n"
        "<code>/claim</code> — Claim group — Admin only\n"
    )

HELP_PAGES = {
    "help_economy": help_economy_text,
    "help_combat":  help_combat_text,
    "help_social":  help_social_text,
    "help_utility": help_utility_text,
    "help_lb":      help_lb_text,
    "help_coupon":  help_coupon_text,
    "help_premium": help_premium_text,
    "help_admin":   help_admin_text,
}

async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"╔══════════════════════╗\n"
        f"║    ⚡ <b>{BOT_NAME} BOT</b>       ║\n"
        f"╚══════════════════════╝\n\n"
        f"Select a category below to view commands:",
        parse_mode="HTML",
        reply_markup=kb_help()
    )

# ══════════════════════════════════════════════════════════════════
#  HANDLERS — ECONOMY
# ══════════════════════════════════════════════════════════════════
async def cmd_daily(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    user = await get_user(u.id, u.username, u.first_name)
    prem = await is_premium(u.id)
    now = int(time.time())

    if now - user["last_daily"] < 86400:
        rem = 86400 - (now - user["last_daily"])
        h, m = divmod(rem // 60, 60)
        await update.message.reply_text(
            f"⏳ Already claimed!\n\nCome back in <b>{h}h {m}m</b>.",
            parse_mode="HTML"
        )
        return

    reward = DAILY_AMOUNT
    gems   = DAILY_GEMS_PREMIUM if prem else 0
    prefix = "💓" if prem else "👤"

    await add_bal(u.id, reward)
    await upd(u.id, last_daily=now)
    if gems:
        await upd(u.id, gems=user["gems"] + gems)
    await record_earn(u.id, reward)

    text = (
        f"✅ {prefix} {mention(u)} claimed daily reward!\n\n"
        f"💵 <b>+{cash(reward)}</b>"
        + (f"\n💎 <b>+{gems} Gems</b>" if gems else "")
    )
    await send_with_gif(update, text, GIF_TAGS["daily"])

async def cmd_bal(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    target = update.message.reply_to_message.from_user if update.message.reply_to_message else update.effective_user
    user = await get_user(target.id, target.username, target.first_name)
    prem = await is_premium(target.id)
    prefix = "💓" if prem else "👤"
    alive  = "✅ Alive" if user["is_alive"] else "💀 Dead"
    prot   = ""
    if user["protected_until"] > int(time.time()):
        rem = user["protected_until"] - int(time.time())
        h, m = divmod(rem // 60, 60)
        prot = f"\n🛡️ Protected: <b>{h}h {m}m</b>"

    await update.message.reply_text(
        f"💰 <b>Balance — {mention(target)}</b>\n\n"
        f"{prefix} Status: {alive}{prot}\n"
        f"💵 Cash: <b>{cash(user['balance'])}</b>\n"
        f"💎 Gems: <b>{user['gems']}</b>\n"
        f"⚔️ Kills: <b>{user['kills']}</b>\n"
        f"🏅 XP: <b>{user['xp']}</b>",
        parse_mode="HTML"
    )

async def cmd_give(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if not update.message.reply_to_message:
        await update.message.reply_text("↩️ Reply to someone to give money.\nUsage: /give <amount>"); return
    if not ctx.args:
        await update.message.reply_text("Usage: /give <amount> (reply)"); return
    try: amount = int(ctx.args[0])
    except: await update.message.reply_text("❌ Invalid amount."); return
    if amount <= 0: await update.message.reply_text("❌ Amount must be positive."); return

    target = update.message.reply_to_message.from_user
    if target.id == u.id: await update.message.reply_text("❌ Can't give to yourself."); return

    giver = await get_user(u.id, u.username, u.first_name)
    prem  = await is_premium(u.id)
    tax_rate = GIVE_TAX_PREMIUM if prem else GIVE_TAX_NORMAL
    fee   = int(amount * tax_rate)
    total = amount + fee

    if giver["balance"] < total:
        await update.message.reply_text(
            f"❌ Insufficient funds!\n\n"
            f"💸 Amount: {cash(amount)}\n"
            f"🏦 Tax ({int(tax_rate*100)}%): {cash(fee)}\n"
            f"📊 Total needed: {cash(total)}\n"
            f"💰 Your balance: {cash(giver['balance'])}"
        ); return

    await add_bal(u.id, -total)
    await add_bal(target.id, amount)
    # Tax goes to group admin wallet if in group
    if is_group(update):
        await add_tax(update.effective_chat.id, fee)
    await get_user(target.id, target.username, target.first_name)
    new_bal = giver["balance"] - total
    await update.message.reply_text(
        f"🎁 <b>Transfer Complete!</b>\n\n"
        f"👤 From: {mention(u)}\n"
        f"👤 To: {mention(target)}\n\n"
        f"💸 Sent: <b>{cash(amount)}</b>\n"
        f"🏦 Tax ({int(tax_rate*100)}%): <b>{cash(fee)}</b>\n"
        f"📤 Total deducted: <b>{cash(total)}</b>\n"
        f"💰 Your remaining balance: <b>{cash(new_bal)}</b>",
        parse_mode="HTML"
    )

async def cmd_rob(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if not update.message.reply_to_message:
        await update.message.reply_text("↩️ Reply to someone to rob."); return
    target = update.message.reply_to_message.from_user
    if target.id == u.id: await update.message.reply_text("❌ Can't rob yourself."); return
    if target.is_bot: await update.message.reply_text("❌ You can't rob a bot."); return

    robber = await get_user(u.id, u.username, u.first_name)
    victim = await get_user(target.id, target.username, target.first_name)
    prem   = await is_premium(u.id)
    limit  = ROB_KILL_LIMIT_PREMIUM if prem else ROB_KILL_LIMIT_NORMAL

    if robber["rob_count"] >= limit:
        await update.message.reply_text(f"❌ Daily rob limit reached ({limit})."); return
    if victim["protected_until"] > int(time.time()):
        await update.message.reply_text(f"🛡️ {mention(target)} is protected!", parse_mode="HTML"); return
    if victim["balance"] <= 0:
        await update.message.reply_text(f"💸 {mention(target)} is broke!", parse_mode="HTML"); return

    max_rob  = ROB_MAX_PREMIUM if prem else ROB_MAX_NORMAL
    steal    = min(random.randint(100, max_rob), victim["balance"])
    tax_rate = ROB_TAX_PREMIUM if prem else ROB_TAX_NORMAL

    # Check lucky_rob item
    robber_items = get_xp_items(robber)
    if robber_items.get("lucky_rob", 0) > 0:
        steal = min(steal * 2, victim["balance"])
        robber_items["lucky_rob"] -= 1
        await save_xp_items(u.id, robber_items)

    fee      = int(steal * tax_rate)
    net      = steal - fee
    xp       = random.randint(*ROB_XP)

    await add_bal(target.id, -steal)
    await add_bal(u.id, net)
    if is_group(update):
        await add_tax(update.effective_chat.id, fee)
    await upd(u.id, rob_count=robber["rob_count"]+1, xp=robber["xp"]+xp)

    text = (
        f"🦹 <b>{mention(u)} robbed {mention(target)}!</b>\n\n"
        f"💰 Stolen: <b>{cash(steal)}</b>\n"
        f"🏦 Tax ({int(tax_rate*100)}%): <b>{cash(fee)}</b>\n"
        f"✅ Net received: <b>{cash(net)}</b>\n"
        f"🏅 XP gained: <b>+{xp}</b>"
    )
    await send_with_gif(update, text, GIF_TAGS["rob"])

async def cmd_kill(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if not update.message.reply_to_message:
        await update.message.reply_text("↩️ Reply to someone to kill."); return
    target = update.message.reply_to_message.from_user
    if target.id == u.id: await update.message.reply_text("❌ Can't kill yourself."); return
    if target.is_bot: await update.message.reply_text("❌ Bots can't be killed. 🤖"); return
    if target.id == OWNER_ID: await update.message.reply_text("❌ You can't touch the bot owner 😤"); return

    killer = await get_user(u.id, u.username, u.first_name)
    victim = await get_user(target.id, target.username, target.first_name)
    prem   = await is_premium(u.id)
    limit  = ROB_KILL_LIMIT_PREMIUM if prem else ROB_KILL_LIMIT_NORMAL

    if not victim["is_alive"]:
        await update.message.reply_text(f"💀 {mention(target)} is already dead!", parse_mode="HTML"); return

    # Check protection — unless user has kill_shield from XP shop
    items = get_xp_items(killer)
    has_shield = items.get("kill_shield", 0) > 0
    if victim["protected_until"] > int(time.time()) and not has_shield:
        await update.message.reply_text(f"🛡️ {mention(target)} is protected! Buy <b>kill_shield</b> from XP Shop to bypass.", parse_mode="HTML"); return
    if has_shield and victim["protected_until"] > int(time.time()):
        items["kill_shield"] -= 1
        await save_xp_items(u.id, items)

    if killer["kill_count"] >= limit:
        await update.message.reply_text(f"❌ Kill limit reached ({limit}/day)."); return

    reward = random.randint(*(KILL_REWARD_PREMIUM if prem else KILL_REWARD_NORMAL))
    xp     = random.randint(*(KILL_XP_PREMIUM if prem else KILL_XP_NORMAL))

    await upd(target.id, is_alive=0)
    await add_bal(u.id, reward)
    await upd(u.id, kills=killer["kills"]+1, kill_count=killer["kill_count"]+1, xp=killer["xp"]+xp)

    text = (
        f"⚔️ <b>{mention(u)} eliminated {mention(target)}!</b>\n\n"
        f"💰 Reward: <b>{cash(reward)}</b>\n"
        f"🏅 XP: <b>+{xp}</b>\n"
        f"💀 {mention(target)} is dead — use /revive."
    )
    await send_with_gif(update, text, GIF_TAGS["kill"])

async def cmd_revive(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    target = update.message.reply_to_message.from_user if update.message.reply_to_message else u
    victim = await get_user(target.id, target.username, target.first_name)
    actor  = await get_user(u.id, u.username, u.first_name)
    if victim["is_alive"]:
        await update.message.reply_text(f"✅ {mention(target)} is already alive!", parse_mode="HTML"); return

    # Check XP shop free revive
    items = get_xp_items(actor)
    if items.get("revive_free", 0) > 0:
        items["revive_free"] -= 1
        await save_xp_items(u.id, items)
        await upd(target.id, is_alive=1)
        await update.message.reply_text(f"💫 {mention(u)} revived {mention(target)} using a free revive token! ❤️", parse_mode="HTML"); return

    if actor["balance"] < REVIVE_COST:
        await update.message.reply_text(f"❌ Revive costs {cash(REVIVE_COST)}. You have {cash(actor['balance'])}."); return
    await add_bal(u.id, -REVIVE_COST)
    await upd(target.id, is_alive=1)
    await update.message.reply_text(
        f"💫 {mention(u)} revived {mention(target)}!\n💸 Cost: {cash(REVIVE_COST)} | ❤️ Back alive!",
        parse_mode="HTML"
    )

async def cmd_protect(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    prem = await is_premium(u.id)
    if not ctx.args: await update.message.reply_text("Usage: /protect 1d | 2d | 3d"); return
    arg = ctx.args[0].lower()
    days_map = {"1d": 1, "2d": 2, "3d": 3}
    if arg not in days_map: await update.message.reply_text("❌ Choose: 1d, 2d, or 3d"); return
    if not prem and arg != "1d": await update.message.reply_text("❌ 2d/3d protection requires Premium."); return
    days = days_map[arg]
    cost = PROTECT_COST_PER_DAY * days
    user = await get_user(u.id, u.username, u.first_name)
    if user["balance"] < cost:
        await update.message.reply_text(f"❌ Need {cash(cost)}. You have {cash(user['balance'])}."); return
    until = int(time.time()) + days * 86400
    await add_bal(u.id, -cost)
    await upd(u.id, protected_until=until)
    await update.message.reply_text(
        f"🛡️ {mention(u)} protected for <b>{days}d</b>!\n💸 Cost: {cash(cost)}",
        parse_mode="HTML"
    )

async def cmd_check(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if not await is_premium(u.id): await update.message.reply_text("❌ /check is 💓 Premium only."); return
    target = update.message.reply_to_message.from_user if update.message.reply_to_message else u
    victim = await get_user(target.id, target.username, target.first_name)
    now = int(time.time())
    if victim["protected_until"] > now:
        rem = victim["protected_until"] - now
        h, m = divmod(rem // 60, 60)
        status = f"🛡️ Protected — {h}h {m}m left"
    else:
        status = "❌ Not protected"
    await update.message.reply_text(f"🔍 {mention(target)}: {status}", parse_mode="HTML")

async def cmd_toprich(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_group(update): await update.message.reply_text("❌ Use this command in a group."); return
    top  = await get_top_rich()
    text = "💰 <b>Top 10 Richest</b>\n\n"
    for i, r in enumerate(top, 1):
        p    = "💓" if r["is_premium"] else "👤"
        name = r["first_name"] or r["username"] or "User"
        text += f"<b>{i}.</b> {p} {name} — <b>{cash(r['balance'])}</b>\n"
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=kb_lb())

async def cmd_lb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_group(update): await update.message.reply_text("❌ Use this command in a group."); return
    top  = await lb_top10()
    text = "🏆 <b>Balance Leaderboard — Top 10</b>\n\n"
    for i, r in enumerate(top, 1):
        p    = "💓" if r["is_premium"] else "👤"
        name = r["first_name"] or r["username"] or "User"
        text += f"<b>{i}.</b> {p} {name} — <b>{cash(r['balance'])}</b>\n"
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=kb_lb())

async def cmd_topkill(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_group(update): await update.message.reply_text("❌ Use this command in a group."); return
    top  = await get_top_kills()
    text = "⚔️ <b>Top 10 Killers</b>\n\n"
    for i, r in enumerate(top, 1):
        p    = "💓" if r["is_premium"] else "👤"
        name = r["first_name"] or r["username"] or "User"
        text += f"<b>{i}.</b> {p} {name} — <b>{r['kills']} kills</b>\n"
    await update.message.reply_text(text, parse_mode="HTML")

async def cmd_pay(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if await is_premium(u.id): await update.message.reply_text("💓 You're already Premium!"); return
    if not ctx.args or ctx.args[0] not in PREMIUM_PRICES:
        await update.message.reply_text(
            "👑 <b>Buy Premium</b>\n\nChoose a plan:",
            parse_mode="HTML",
            reply_markup=kb_premium()
        ); return
    plan = ctx.args[0]
    cost = PREMIUM_PRICES[plan]
    user = await get_user(u.id, u.username, u.first_name)
    if user["balance"] < cost:
        await update.message.reply_text(f"❌ Need {cash(cost)}. You have {cash(user['balance'])}."); return
    hours = {"24h": 24, "48h": 48, "7d": 168}[plan]
    until = int(time.time()) + hours * 3600
    await add_bal(u.id, -cost)
    await upd(u.id, is_premium=1, premium_until=until)
    await update.message.reply_text(f"💓 {mention(u)} is now <b>Premium</b> for <b>{plan}</b>! ✨", parse_mode="HTML")

async def cmd_addbal(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: await update.message.reply_text("❌ Owner only."); return
    if not ctx.args:
        await update.message.reply_text("Usage:\n/addbal <amount> (reply to user)\n/addbal <user_id> <amount>"); return

    # Check if first arg is a user_id (large number) or amount
    if len(ctx.args) >= 2 and ctx.args[0].lstrip('-').isdigit() and len(ctx.args[0]) >= 5:
        # /addbal <userid> <amount>
        try:
            target_id = int(ctx.args[0])
            amount    = int(ctx.args[1])
        except:
            await update.message.reply_text("❌ Invalid format."); return
        await get_user(target_id)
        await add_bal(target_id, amount)
        await update.message.reply_text(
            f"✅ Added <b>{cash(amount)}</b> to user <code>{target_id}</code>.",
            parse_mode="HTML"
        )
    elif update.message.reply_to_message:
        try: amount = int(ctx.args[0])
        except: await update.message.reply_text("❌ Invalid amount."); return
        target = update.message.reply_to_message.from_user
        await get_user(target.id, target.username, target.first_name)
        await add_bal(target.id, amount)
        await update.message.reply_text(
            f"✅ Added <b>{cash(amount)}</b> to {mention(target)}.",
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text("Usage:\n/addbal <amount> (reply to user)\n/addbal <user_id> <amount>")

async def cmd_dedbal(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Deduct balance — owner only. /dedbal <amount> (reply) or /dedbal <userid> <amount>"""
    if update.effective_user.id != OWNER_ID: await update.message.reply_text("❌ Owner only."); return
    if not ctx.args:
        await update.message.reply_text("Usage:\n/dedbal <amount> (reply to user)\n/dedbal <user_id> <amount>"); return

    if len(ctx.args) >= 2 and ctx.args[0].lstrip('-').isdigit() and len(ctx.args[0]) >= 5:
        try:
            target_id = int(ctx.args[0])
            amount    = int(ctx.args[1])
        except:
            await update.message.reply_text("❌ Invalid format."); return
        await get_user(target_id)
        await add_bal(target_id, -amount)
        await update.message.reply_text(
            f"✅ Deducted <b>{cash(amount)}</b> from user <code>{target_id}</code>.",
            parse_mode="HTML"
        )
    elif update.message.reply_to_message:
        try: amount = int(ctx.args[0])
        except: await update.message.reply_text("❌ Invalid amount."); return
        target = update.message.reply_to_message.from_user
        await get_user(target.id, target.username, target.first_name)
        await add_bal(target.id, -amount)
        await update.message.reply_text(
            f"✅ Deducted <b>{cash(amount)}</b> from {mention(target)}.",
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text("Usage:\n/dedbal <amount> (reply to user)\n/dedbal <user_id> <amount>")

# ── Tax Wallet ─────────────────────────────────────────────────
async def cmd_taxbal(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_group(update): await update.message.reply_text("❌ Groups only."); return
    if not await is_admin(update, update.effective_user.id) and update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Admins only."); return
    bal = await get_tax(update.effective_chat.id)
    await update.message.reply_text(
        f"🏦 <b>Group Tax Wallet</b>\n\n💰 Accumulated: <b>{cash(bal)}</b>\n\nUse /withdrawtax to claim.",
        parse_mode="HTML"
    )

async def cmd_withdrawtax(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if not is_group(update): await update.message.reply_text("❌ Groups only."); return
    if not await is_admin(update, u.id) and u.id != OWNER_ID:
        await update.message.reply_text("❌ Admins only."); return
    bal = await get_tax(update.effective_chat.id)
    if bal <= 0: await update.message.reply_text("❌ No tax accumulated yet."); return
    await add_bal(u.id, bal)
    async with aiosqlite.connect(DB_PATH) as d:
        await d.execute("UPDATE tax_wallet SET balance=0 WHERE group_id=?", (update.effective_chat.id,))
        await d.commit()
    await update.message.reply_text(
        f"✅ {mention(u)} withdrew <b>{cash(bal)}</b> from group tax wallet!",
        parse_mode="HTML"
    )

# ── XP Shop ────────────────────────────────────────────────────
async def cmd_xpshop(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    user = await get_user(u.id, u.username, u.first_name)
    text = f"🛒 <b>XP Shop</b> — Your XP: <b>{user['xp']}</b>\n\nSelect an item to purchase:"
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=kb_xp_shop())

# ══════════════════════════════════════════════════════════════════
#  HANDLERS — SOCIAL
# ══════════════════════════════════════════════════════════════════
async def social(update: Update, action: str):
    u = update.effective_user
    await get_user(u.id, u.username, u.first_name)
    if not update.message.reply_to_message:
        await update.message.reply_text(f"↩️ Reply to someone to {action} them."); return
    target = update.message.reply_to_message.from_user
    await get_user(target.id, target.username, target.first_name)
    a, b = mention(u), mention(target)
    text  = random.choice(SOCIAL[action]).format(a=a, b=b)
    await send_with_gif(update, text, SOCIAL_GIPHY.get(action, action))

async def cmd_slap(u, c):     await social(u, "slap")
async def cmd_hug(u, c):      await social(u, "hug")
async def cmd_kiss(u, c):     await social(u, "kiss")
async def cmd_punch(u, c):    await social(u, "punch")
async def cmd_bite(u, c):     await social(u, "bite")
async def cmd_love(u, c):     await social(u, "love")
async def cmd_look(u, c):     await social(u, "look")
async def cmd_crush(u, c):    await social(u, "crush")
async def cmd_murder(u, c):   await social(u, "murder")
async def cmd_pat(u, c):      await social(u, "pat")
async def cmd_poke(u, c):     await social(u, "poke")
async def cmd_tickle(u, c):   await social(u, "tickle")
async def cmd_wave(u, c):     await social(u, "wave")
async def cmd_wink(u, c):     await social(u, "wink")
async def cmd_cry(u, c):      await social(u, "cry")
async def cmd_laugh(u, c):    await social(u, "laugh")
async def cmd_dance(u, c):    await social(u, "dance")
async def cmd_cuddle(u, c):   await social(u, "cuddle")
async def cmd_highfive(u, c): await social(u, "highfive")
async def cmd_throw(u, c):    await social(u, "throw")

# ══════════════════════════════════════════════════════════════════
#  HANDLERS — COUPON
# ══════════════════════════════════════════════════════════════════
async def cmd_create_coupon(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if not is_group(update): await update.message.reply_text("❌ Groups only."); return
    if not await is_admin(update, u.id) and u.id != OWNER_ID:
        await update.message.reply_text("❌ Admins only."); return
    reward = int(ctx.args[0]) if ctx.args else 500
    max_c  = int(ctx.args[1]) if len(ctx.args) > 1 else 50
    code   = rnd_code()
    ok, result = await create_coupon(code, update.effective_chat.id, u.id, reward, max_c)
    if not ok:
        await update.message.reply_text(f"❌ Group already has coupon: <code>{result}</code>. Delete first.", parse_mode="HTML"); return
    await update.message.reply_text(
        f"✅ <b>Coupon Created!</b>\n\n🎟️ Code: <code>{code}</code>\n💰 Reward: {cash(reward)}\n👥 Max claims: {max_c}\n\nUse: /coupon {code}",
        parse_mode="HTML"
    )

async def cmd_coupon(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if not is_group(update): await update.message.reply_text("❌ Groups only."); return
    if not ctx.args: await update.message.reply_text("Usage: /coupon <code>"); return
    await get_user(u.id, u.username, u.first_name)
    code = ctx.args[0].upper()
    ok, result = await claim_coupon(code, u.id, update.effective_chat.id)
    if not ok: await update.message.reply_text(result); return
    await update.message.reply_text(f"🎉 {mention(u)} claimed coupon! 💵 <b>+{cash(result)}</b>", parse_mode="HTML")

async def cmd_del_coupon(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if not is_group(update): await update.message.reply_text("❌ Groups only."); return
    if not await is_admin(update, u.id) and u.id != OWNER_ID:
        await update.message.reply_text("❌ Admins only."); return
    ok, result = await delete_coupon(update.effective_chat.id, u.id)
    if not ok: await update.message.reply_text(f"❌ {result}"); return
    await update.message.reply_text(f"✅ Coupon <code>{result}</code> deleted.", parse_mode="HTML")

async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_group(update): await update.message.reply_text("❌ Groups only."); return
    cp = await coupon_status(update.effective_chat.id)
    if not cp: await update.message.reply_text("❌ No active coupon."); return
    await update.message.reply_text(
        f"🎟️ <b>Coupon Status</b>\n\nCode: <code>{cp['code']}</code>\n"
        f"💰 Reward: {cash(cp['reward'])}\n✅ Claimed: {cp['claims']}/{cp['max_claims']}\n"
        f"🔄 Remaining: {cp['max_claims'] - cp['claims']}",
        parse_mode="HTML"
    )

async def cmd_claim(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if not is_group(update):
        await update.message.reply_text("➡️ Add me to a group and use /claim there!"); return
    if not await is_admin(update, u.id) and u.id != OWNER_ID:
        await update.message.reply_text("❌ Only group admins can /claim."); return
    gid     = update.effective_chat.id
    claimer = await group_claimer(gid)
    if claimer:
        msg = "❌ You already claimed reward for this group!" if claimer == u.id else "❌ Group already claimed by another admin."
        await update.message.reply_text(msg); return
    await register_group(gid, u.id)
    await get_user(u.id, u.username, u.first_name)
    await add_bal(u.id, CLAIM_GROUP_REWARD)
    await update.message.reply_text(
        f"🎉 {mention(u)} claimed this group!\n\n💰 Reward: <b>{cash(CLAIM_GROUP_REWARD)}</b>\n✨ Group features unlocked!",
        parse_mode="HTML"
    )

# ══════════════════════════════════════════════════════════════════
#  HANDLERS — UTILITY
# ══════════════════════════════════════════════════════════════════
async def cmd_tr(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    text = (msg.reply_to_message.text if msg.reply_to_message and msg.reply_to_message.text
            else " ".join(ctx.args) if ctx.args else None)
    if not ctx.args and not (msg.reply_to_message and msg.reply_to_message.text):
        await msg.reply_text("Usage: /tr <text>  or  /tr <lang> <text>  e.g. /tr es Hello"); return
    if not text: return
    lang = "en"
    if ctx.args and len(ctx.args) > 1 and len(ctx.args[0]) <= 5 and ctx.args[0].isalpha():
        lang = ctx.args[0].lower()
        text = " ".join(ctx.args[1:])
    try:
        import aiohttp, urllib.parse
        # Google Translate unofficial free API
        encoded = urllib.parse.quote(text)
        url = (
            f"https://translate.googleapis.com/translate_a/single"
            f"?client=gtx&sl=auto&tl={lang}&dt=t&dt=ld&q={encoded}"
        )
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10),
                                   headers={"User-Agent": "Mozilla/5.0"}) as r:
                data = await r.json(content_type=None)
        # Parse response: data[0] is list of translation chunks
        translated_parts = [chunk[0] for chunk in data[0] if chunk and chunk[0]]
        translated = "".join(translated_parts)
        # Detected language is at data[2]
        detected = data[2] if len(data) > 2 and data[2] else "?"
        if not translated:
            await msg.reply_text("❌ Translation failed: empty response"); return
        await msg.reply_text(
            f"🌐 <b>Translation</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔍 Detected: <b>{str(detected).upper()}</b>  ›  🗣 <b>{lang.upper()}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{translated}",
            parse_mode="HTML"
        )
    except Exception as e:
        await msg.reply_text(f"❌ Translation failed: {e}")

async def cmd_tts(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    text = (msg.reply_to_message.text if msg.reply_to_message and msg.reply_to_message.text
            else " ".join(ctx.args) if ctx.args else None)
    if not text: await msg.reply_text("Usage: /tts <text> or reply with /tts"); return
    if len(text) > 500: await msg.reply_text("❌ Max 500 chars."); return
    voice = await get_group_voice(update.effective_chat.id) if is_group(update) else "en-US-GuyNeural"
    tmp_path = None
    try:
        import edge_tts, uuid
        tmp_path = f"/tmp/tts_{uuid.uuid4().hex}.mp3"
        communicate = edge_tts.Communicate(text=text, voice=voice)
        await communicate.save(tmp_path)
        with open(tmp_path, "rb") as f:
            await msg.reply_voice(voice=f, caption=f"🔊 {text[:80]}")
    except Exception as e:
        err = str(e)
        if "403" in err or "wss" in err.lower():
            await msg.reply_text("❌ TTS service temporarily unavailable. Try again in a moment.")
        else:
            await msg.reply_text(f"❌ TTS failed: {err}")
    finally:
        if tmp_path:
            try: os.unlink(tmp_path)
            except: pass

async def cmd_voices(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔊 <b>Available TTS Voices</b>\n\nTap a voice to hear a demo:",
        parse_mode="HTML",
        reply_markup=kb_voices()
    )

async def cmd_set_tts(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if not is_group(update): await update.message.reply_text("❌ Groups only."); return
    if not await is_admin(update, u.id) and u.id != OWNER_ID:
        await update.message.reply_text("❌ Admins only."); return
    if not ctx.args:
        await update.message.reply_text("Use /voices to browse and set.", parse_mode="HTML"); return
    key = ctx.args[0].lower()
    if key not in AVAILABLE_VOICES: await update.message.reply_text("❌ Unknown voice. Use /voices to list."); return
    await set_group_voice(update.effective_chat.id, AVAILABLE_VOICES[key])
    await update.message.reply_text(f"✅ TTS voice set to <b>{AVAILABLE_VOICES[key]}</b>", parse_mode="HTML")

async def cmd_admins(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_group(update): await update.message.reply_text("❌ Groups only."); return
    try:
        admins = await update.effective_chat.get_administrators()
        text   = "👑 <b>Group Admins</b>\n\n"
        for a in admins:
            if a.user.is_bot: continue
            role = "🔱 Owner" if a.status == "creator" else "⭐ Admin"
            text += f"{role} — <a href='tg://user?id={a.user.id}'>{a.user.first_name}</a>\n"
        await update.message.reply_text(text, parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def cmd_owner(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_group(update): await update.message.reply_text("❌ Groups only."); return
    try:
        for a in await update.effective_chat.get_administrators():
            if a.status == "creator":
                await update.message.reply_text(
                    f"🔱 Group Owner: <a href='tg://user?id={a.user.id}'>{a.user.first_name}</a>",
                    parse_mode="HTML"
                ); return
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def cmd_details(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    target = update.message.reply_to_message.from_user if update.message.reply_to_message else update.effective_user
    await get_user(target.id, target.username, target.first_name)
    history  = await get_uname_history(target.id)
    position = await get_user_position(update.effective_chat.id if is_group(update) else 0, target.id)

    # Try to get join date in group
    join_ts = None
    if is_group(update):
        join_ts = await get_group_join(target.id, update.effective_chat.id)
        if not join_ts:
            try:
                member = await update.effective_chat.get_member(target.id)
                # Store join date if first seen
                await set_group_join(target.id, update.effective_chat.id)
                join_ts = int(time.time())
            except:
                pass

    text = (
        f"📋 <b>User Details</b>\n\n"
        f"👤 Name: {mention(target)}\n"
        f"🆔 ID: <code>{target.id}</code>\n"
        f"📛 Username: @{target.username or 'N/A'}\n"
    )
    if join_ts:
        text += f"📅 Joined group: <b>{datetime.fromtimestamp(join_ts).strftime('%Y-%m-%d')}</b>\n"
    text += f"🏅 Global position: <b>#{position}</b>\n"
    if history:
        text += "\n📜 <b>Past Usernames:</b>\n"
        for r in history:
            dt = datetime.fromtimestamp(r["changed_at"]).strftime("%Y-%m-%d")
            text += f"• @{r['username']} ({dt})\n"
    else:
        text += "\n📜 No username history."
    await update.message.reply_text(text, parse_mode="HTML")

# ── Custom Sticker ─────────────────────────────────────────────
async def cmd_setsticker(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if not await is_premium(u.id):
        await update.message.reply_text("❌ /setsticker is 💓 Premium only."); return
    if not update.message.reply_to_message or not update.message.reply_to_message.sticker:
        await update.message.reply_text("↩️ Reply to a sticker and use /setsticker <name>"); return
    if not ctx.args:
        await update.message.reply_text("Usage: /setsticker <name> (reply to sticker)"); return
    name = ctx.args[0].lower()
    file_id = update.message.reply_to_message.sticker.file_id
    await upd(u.id, custom_sticker=file_id, custom_sticker_name=name)
    await update.message.reply_text(
        f"✅ Sticker saved as <b>{name}</b>!\n\n"
        f"Whenever anyone types <code>{name}</code> in any group, your sticker will be sent! 🎯",
        parse_mode="HTML"
    )

async def handle_sticker_trigger(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Auto-reply with custom sticker when trigger name is mentioned in any group message."""
    if not update.message or not update.message.text:
        return
    text_lower = update.message.text.lower()
    # Get all users with custom stickers
    async with aiosqlite.connect(DB_PATH) as d:
        d.row_factory = aiosqlite.Row
        async with d.execute("SELECT custom_sticker, custom_sticker_name FROM users WHERE custom_sticker IS NOT NULL AND custom_sticker_name IS NOT NULL") as c:
            stickers = [dict(r) for r in await c.fetchall()]
    for s in stickers:
        name = s["custom_sticker_name"]
        if name and name in text_lower:
            try:
                await update.message.reply_sticker(s["custom_sticker"])
            except:
                pass

# ══════════════════════════════════════════════════════════════════
#  HANDLERS — LEADERBOARD
# ══════════════════════════════════════════════════════════════════
# /lb already defined above as cmd_lb

# ══════════════════════════════════════════════════════════════════
#  HANDLERS — OWNER PANEL
# ══════════════════════════════════════════════════════════════════
async def cmd_panel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Owner only."); return
    await update.message.reply_text(
        f"╔══════════════════════╗\n"
        f"║  ⚙️  <b>OWNER PANEL</b>  ║\n"
        f"╚══════════════════════╝\n\n"
        f"  Select an action below:",
        parse_mode="HTML",
        reply_markup=kb_panel()
    )

async def cmd_genid(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Owner only."); return
    code = await gen_clone_id()
    await update.message.reply_text(
        f"🔑 <b>Clone ID Generated</b>\n\n<code>{code}</code>\n\n"
        f"Share this with the person who wants to clone the bot.\nID is single-use.",
        parse_mode="HTML"
    )

# ══════════════════════════════════════════════════════════════════
#  HANDLERS — CLONE FLOW (conversation via ctx.user_data)
# ══════════════════════════════════════════════════════════════════
CLONE_STEPS = {}  # user_id -> state dict

async def cmd_clone(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if is_group(update): await update.message.reply_text("↩️ Use /clone in private chat with me."); return
    if not ctx.args:
        await update.message.reply_text("Usage: /clone <ID>\n\nGet a clone ID from the bot owner."); return
    code = ctx.args[0].strip().upper()
    valid = await validate_clone_id(code)
    if not valid:
        await update.message.reply_text("❌ Invalid or already used clone ID."); return

    CLONE_STEPS[u.id] = {"step": "awaiting_joinyesno", "code": code}
    keyboard = _rm([_b("✅ Yes — join requirements", cb="clone_joinyesno_yes", style="success"), _b("❌ No", cb="clone_joinyesno_no", style="danger")])
    await update.message.reply_text(
        "🤖 <b>Clone Setup</b>\n\n"
        "Do you want users to join your channel/group before using the bot?",
        parse_mode="HTML",
        reply_markup=keyboard
    )

async def cmd_clone_msg(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle freeform text during clone setup — only fires if user is in active clone flow."""
    u = update.effective_user

    # ── /img6 custom reply handler ───────────────────────────────
    i6 = IMG6_STATE.get(u.id, {})
    if i6.get("awaiting_reply"):
        request_id = i6["awaiting_reply"]
        user_reply = update.message.text.strip()
        prompt     = i6.get("prompt", "")
        IMG6_STATE[u.id].pop("awaiting_reply", None)
        import aiohttp as _ah
        wm = await update.message.reply_text(
            f"💬 <b>Reply sent:</b> <code>{user_reply[:60]}</code>\n⏳ Waiting...",
            parse_mode="HTML"
        )
        try:
            async with _ah.ClientSession() as session:
                async with session.post(
                    f"{DDG_API_BASE}/image/reply",
                    json={"id": request_id, "message": user_reply},
                    timeout=_ah.ClientTimeout(total=15)
                ) as r:
                    await r.json(content_type=None)
            result = await _ddg_poll(request_id, "image")
            try: await wm.delete()
            except: pass
            if result.get("status") == "needs_reply":
                question = result.get("text", "AI needs more info.")
                await update.message.reply_text(
                    f"❓ <b>AI is asking:</b>\n\n<i>{question}</i>",
                    parse_mode="HTML",
                    api_kwargs={"reply_markup": kb_img6_reply(request_id, question)},
                )
            elif result.get("status") == "done" and result.get("images"):
                is_owner = (u.id == OWNER_ID)
                if not is_owner:
                    await deduct_model_credit(u.id, "img6_credits")
                    cl = await get_model_credits(u.id, "img6_credits")
                    credits_line = f"📸 Credits Left • <b>{cl}</b> remaining today"
                else:
                    credits_line = "👑 Owner Access • Unlimited"
                uname = f"@{u.username}" if u.username else (u.first_name or "User")
                caption = (
                    f"✨ <b>Image Generated!</b>\n"
                    f"╭━━━━━━━━━━━━━━━━━━╮\n"
                    f"│ 👤 User » {uname}\n"
                    f"│ 🤖 Model » {result.get('model','GPT Image 2')}\n"
                    f"│ 📝 Prompt » {prompt[:55]}{'...' if len(prompt)>55 else ''}\n"
                    f"╰━━━━━━━━━━━━━━━━━━╯\n"
                    f"{credits_line}\n\n🔁 <b>Regenerate or done:</b>"
                )
                await update.message.reply_photo(
                    photo=result["images"][0], caption=caption, parse_mode="HTML",
                    api_kwargs={"reply_markup": kb_img6_regen(prompt)},
                )
            else:
                err = result.get("error", "No images")
                await update.message.reply_text(f"❌ <code>{err}</code>", parse_mode="HTML")
        except Exception as e:
            try: await wm.delete()
            except: pass
            await update.message.reply_text(f"❌ Error: {e}")
        return
    # ────────────────────────────────────────────────────────────────

    state = CLONE_STEPS.get(u.id)
    # No active clone session → ignore, don't reply
    if not state:
        return
    step = state.get("step")
    # Still waiting for button press — ignore text
    if step == "awaiting_joinyesno":
        await update.message.reply_text("👆 Please tap a button above to continue.")
        return

    text = update.message.text.strip()

    if step == "wait_channel":
        state["channel"] = text
        state["step"] = "wait_group"
        CLONE_STEPS[u.id] = state
        await update.message.reply_text(
            "📎 Send your <b>group invite link</b> (or type <code>none</code> to skip):",
            parse_mode="HTML"
        )

    elif step == "wait_group":
        state["group"] = None if text.lower() == "none" else text
        state["step"] = "wait_token"
        CLONE_STEPS[u.id] = state
        await update.message.reply_text(
            "🔑 Send your <b>bot token</b> (from @BotFather):",
            parse_mode="HTML"
        )

    elif step == "wait_token":
        if not re.match(r'^\d+:[A-Za-z0-9_-]{35,}$', text):
            await update.message.reply_text("❌ That doesn't look like a valid bot token. Try again:"); return
        state["token"] = text
        state["step"] = "wait_botname"
        CLONE_STEPS[u.id] = state
        await update.message.reply_text("✏️ Send your <b>bot name</b> (display name):", parse_mode="HTML")

    elif step == "wait_botname":
        state["botname"] = text
        state["step"] = "wait_ownerid"
        CLONE_STEPS[u.id] = state
        await update.message.reply_text("🆔 Send your <b>Telegram user ID</b> (numbers only):", parse_mode="HTML")

    elif step == "wait_ownerid":
        if not text.lstrip('-').isdigit():
            await update.message.reply_text("❌ Owner ID must be a number. Try again:"); return
        state["ownerid"] = text
        state["step"] = "delivering"
        CLONE_STEPS[u.id] = state
        await update.message.reply_text("⚙️ Building your bot package...", parse_mode="HTML")
        await deliver_clone(update, state)

async def deliver_clone(update: Update, state: dict):
    u = update.effective_user
    token   = state.get("token", "YOUR_BOT_TOKEN_HERE")
    botname = state.get("botname", "MyBot")
    ownerid = state.get("ownerid", "YOUR_ID")
    channel = state.get("channel")
    group   = state.get("group")

    # Read this bot's own source and patch config values
    try:
        self_path = os.path.abspath(__file__)
        with open(self_path, "r", encoding="utf-8") as f:
            source = f.read()
    except Exception:
        source = "# Could not read source file. Contact owner.\n"

    # Patch config lines
    source = re.sub(r'BOT_TOKEN\s*=\s*".*?"', f'BOT_TOKEN   = "{token}"', source)
    source = re.sub(r'OWNER_ID\s*=\s*\d+.*', f'OWNER_ID    = {ownerid}', source)
    source = re.sub(r'BOT_NAME\s*=\s*".*?"', f'BOT_NAME    = "{botname}"', source)
    # Wipe owner's Giphy key — cloner must supply their own
    source = re.sub(r'GIPHY_KEY\s*=\s*".*?"', 'GIPHY_KEY   = "YOUR_GIPHY_API_KEY"', source)

    # Inject force-join block if needed
    if channel or group:
        links = [x for x in [channel, group] if x]
        force_block = (
            f"\n# ── Force Join ──\nFORCE_JOIN = {json.dumps(links)}\n\n"
            "async def check_membership(bot, uid):\n"
            "    for link in FORCE_JOIN:\n"
            "        try:\n"
            "            chat_id = link if link.lstrip('@').startswith(str(abs(int(link)))) else '@' + link.lstrip('https://t.me/').lstrip('@')\n"
            "            member = await bot.get_chat_member(chat_id, uid)\n"
            "            if member.status in ('left', 'kicked'): return False\n"
            "        except: pass\n"
            "    return True\n"
        )
        # Insert after imports block
        source = source.replace(
            "logging.basicConfig(",
            force_block + "\nlogging.basicConfig(",
            1
        )

    # Write to temp file and send
    safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', botname.lower())
    fname = f"/tmp/{safe_name}_bot.py"
    with open(fname, "w", encoding="utf-8") as f:
        f.write(source)

    shell_cmds = (
        f"# ── Install dependencies ──\n"
        f"pip install python-telegram-bot aiosqlite aiohttp edge-tts deep-translator\n\n"
        f"# ── Run the bot ──\n"
        f"python {safe_name}_bot.py\n\n"
        f"# ── TeleBotHosting: upload {safe_name}_bot.py then run above ──\n"
    )

    join_info = ""
    if channel or group:
        join_info = f"📢 Force join: {channel or ''} {group or ''}".strip()
    else:
        join_info = "🔓 No force join requirement"

    keyboard = _rm([_b("🚀 TeleBotHosting Guide", cb="clone_tbh", style="primary")], [_b("« Main Menu", cb="cb_start")])

    await update.message.reply_text(
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ <b>Clone Package Ready!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🤖 Bot name: <b>{botname}</b>\n"
        f"👤 Owner ID: <code>{ownerid}</code>\n"
        f"{join_info}\n\n"
        f"📄 Source file incoming below ↓",
        parse_mode="HTML",
        reply_markup=keyboard
    )

    with open(fname, "rb") as f:
        await update.message.reply_document(
            f,
            filename=f"{safe_name}_bot.py",
            caption=(
                f"📄 <b>{botname} Bot</b> — Full source\n\n"
                f"Token, owner ID and bot name are pre-filled.\n"
                f"Replace <code>YOUR_GIPHY_API_KEY</code> with your Giphy key."
            ),
            parse_mode="HTML"
        )

    await update.message.reply_text(
        f"╔══════════════════════╗\n"
        f"║  💻  <b>SHELL COMMANDS</b>  ║\n"
        f"╚══════════════════════╝\n\n"
        f"<pre>{shell_cmds}</pre>\n\n"
        f"  📌  <b>Giphy API Key</b> (for GIFs):\n"
        f"  1. Go to https://developers.giphy.com\n"
        f"  2. Log in → Create App → SDK → get API Key\n"
        f"  3. Paste it as <code>GIPHY_KEY</code> in your bot file",
        parse_mode="HTML"
    )

    # Send requirements.txt
    req_content = (
        "python-telegram-bot==20.7\n"
        "aiosqlite==0.19.0\n"
        "aiohttp==3.9.3\n"
        "edge-tts==6.1.9\n"
        "deep-translator==1.11.4\n"
    )
    req_fname = f"/tmp/{safe_name}_requirements.txt"
    with open(req_fname, "w") as _rf:
        _rf.write(req_content)
    with open(req_fname, "rb") as _rf:
        await update.message.reply_document(
            _rf, filename="requirements.txt",
            caption="📦 Install: <code>pip install -r requirements.txt</code>",
            parse_mode="HTML"
        )
    try:
        os.unlink(req_fname)
    except:
        pass

    try:
        os.unlink(fname)
    except:
        pass

    if u.id in CLONE_STEPS:
        del CLONE_STEPS[u.id]

# ══════════════════════════════════════════════════════════════════
#  CALLBACK QUERY HANDLER
# ══════════════════════════════════════════════════════════════════
async def callback_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q    = update.callback_query
    data = q.data
    u    = q.from_user
    await q.answer()

    # ── img5 ─────────────────────────────────────────────────────────
    if data.startswith("i5s:"):
        # i5s:<style_val>:<prompt_b64>
        parts = data.split(":", 2)
        if len(parts) == 3:
            _, style_val, p_b64 = parts
            import base64
            try: prompt = base64.b64decode(p_b64.encode()).decode()
            except: prompt = p_b64
            style_label = next((l for l, v in PRODIA_STYLES if v == style_val), style_val)
            import json as _j
            # Build aspect keyboard — encode prompt in b64 again
            p_enc = base64.b64encode(prompt[:40].encode()).decode()
            s_enc = style_val[:20]
            aspect_kb = _j.dumps({"inline_keyboard": [
                [
                    {"text": "⬛ Square",    "callback_data": f"i5a:square:{s_enc}:{p_enc}",   "style": "primary"},
                    {"text": "📱 Portrait",  "callback_data": f"i5a:portrait:{s_enc}:{p_enc}", "style": "primary"},
                    {"text": "🖼 Landscape", "callback_data": f"i5a:landscape:{s_enc}:{p_enc}","style": "primary"},
                ],
                [
                    {"text": "« Back", "callback_data": f"i5_back:{p_enc}", "style": "primary"},
                    {"text": "❌ Cancel", "callback_data": "i5_cancel", "style": "danger"},
                ],
            ]})
            txt = (
                f"🖼 <b>Step 2 — Pick Aspect Ratio</b>\n\n"
                f"📝 Prompt: <code>{prompt[:60]}{'...' if len(prompt)>60 else ''}</code>\n"
                f"🎨 Style: <b>{style_label}</b>\n\n"
                f"Choose aspect ratio:"
            )
            try:
                await q.edit_message_text(txt, parse_mode="HTML", api_kwargs={"reply_markup": aspect_kb})
            except Exception:
                await ctx.bot.send_message(q.message.chat_id, txt, parse_mode="HTML", api_kwargs={"reply_markup": aspect_kb})
        return

    if data.startswith("i5a:"):
        # i5a:<aspect>:<style_val>:<prompt_b64>
        parts = data.split(":", 3)
        if len(parts) == 4:
            _, aspect, style_val, p_b64 = parts
            import base64
            try: prompt = base64.b64decode(p_b64.encode()).decode()
            except: prompt = p_b64
            await q.answer(f"🖼 Generating {aspect}...")
            try: await q.edit_message_reply_markup(reply_markup=None)
            except: pass
            chat_id = q.message.chat_id
            # Credits check
            is_owner = (u.id == OWNER_ID)
            if not is_owner:
                credits = await get_model_credits(u.id, "img5_credits")
                if credits <= 0:
                    await ctx.bot.send_message(chat_id,
                        "❌ <b>No /img5 credits left!</b>\n\n"
                        "📸 Daily free: <b>2/day</b> (resets midnight)\n"
                        "👑 Ask owner: /addcredits5", parse_mode="HTML")
                    return
            style_label = next((l for l, v in PRODIA_STYLES if v == style_val), style_val)
            username_str = f"@{u.username}" if u.username else (u.first_name or "User")
            # Send wait message
            wm = await ctx.bot.send_message(chat_id,
                f"✨ <b>Generating Your Image...</b>\n"
                f"『────────────────────』\n"
                f"✦ 𝗠𝗼𝗱𝗲𝗹  │ <code>FLUX.2</code>\n"
                f"✦ 𝗣𝗿𝗼𝗺𝗽𝘁 │ <code>{prompt[:50]}{'...' if len(prompt)>50 else ''}</code>\n"
                f"✦ 𝗦𝘁𝘆𝗹𝗲  │ {style_label}\n"
                f"✦ 𝗔𝘀𝗽𝗲𝗰𝘁 │ {aspect.upper()}\n"
                f"✦ 𝗧𝗶𝗺𝗲   │ 5–30s\n"
                f"❖ 𝗥𝗲𝗾𝘂𝗲𝘀𝘁𝗲𝗱 𝗯𝘆 : <b>{username_str}</b>\n"
                f"『────────────────────』\n"
                f"<i>🖌 Crafting your exclusive creation...</i>",
                parse_mode="HTML")
            import aiohttp, urllib.parse, time as _t
            start = _t.time()
            try:
                enc = urllib.parse.quote_plus(prompt.strip())
                url = f"{PRODIA_API_BASE}?prompt={enc}&style={style_val}&aspect={aspect}"
                async with aiohttp.ClientSession() as s:
                    async with s.get(url, timeout=aiohttp.ClientTimeout(total=90)) as r:
                        rj = await r.json(content_type=None)
                image_url = rj.get("image_url")
                if not image_url:
                    err = rj.get("error") or rj.get("message") or str(rj)[:200]
                    try: await wm.delete()
                    except: pass
                    await ctx.bot.send_message(chat_id, f"❌ <b>Generation failed</b>\n<code>{err}</code>", parse_mode="HTML")
                    return
                taken = int(_t.time() - start)
                dims  = rj.get("dimensions", "—")
                if not is_owner:
                    await deduct_model_credit(u.id, "img5_credits")
                    cl = await get_model_credits(u.id, "img5_credits")
                    credits_line = f"📸 Credits Left • <b>{cl}</b> remaining today"
                else:
                    credits_line = "👑 Owner Access • Unlimited"
                # Regen keyboard — store prompt in b64
                import base64 as _b64, json as _j
                p_enc2 = _b64.b64encode(prompt[:40].encode()).decode()
                s_enc2 = style_val[:20]
                a_enc2 = aspect[:10]
                regen_kb = _j.dumps({"inline_keyboard": [
                    [
                        {"text": "🎨 Change Style",  "callback_data": f"i5_chstyle:{p_enc2}", "style": "primary"},
                        {"text": "🖼 Change Aspect", "callback_data": f"i5_chaspect:{s_enc2}:{p_enc2}", "style": "primary"},
                    ],
                    [
                        {"text": "🔁 Regenerate",   "callback_data": f"i5_regen:{s_enc2}:{a_enc2}:{p_enc2}", "style": "success"},
                        {"text": "✅ Done",          "callback_data": "i5_cancel", "style": "danger"},
                    ],
                ]})
                caption = (
                    f"✨ <b>Image Generated!</b>\n"
                    f"╭━━━━━━━━━━━━━━━━━━╮\n"
                    f"│ 👤 User » {username_str}\n"
                    f"│ 🎭 Style » {style_label}\n"
                    f"│ 🖼 Aspect » {aspect.upper()} ({dims})\n"
                    f"│ 📝 Prompt » {prompt[:55]}{'...' if len(prompt)>55 else ''}\n"
                    f"│ ⚡ Time » {taken}s\n"
                    f"╰━━━━━━━━━━━━━━━━━━╯\n"
                    f"{credits_line}\n\n"
                    f"🔁 <b>Regenerate or change style/aspect:</b>"
                )
                try: await wm.delete()
                except: pass
                await ctx.bot.send_photo(chat_id, photo=image_url, caption=caption, parse_mode="HTML",
                                         api_kwargs={"reply_markup": regen_kb})
            except asyncio.TimeoutError:
                try: await wm.delete()
                except: pass
                await ctx.bot.send_message(chat_id, "❌ Timed out (90s). Try again!")
            except Exception as e:
                try: await wm.delete()
                except: pass
                await ctx.bot.send_message(chat_id, f"❌ Generation failed: {e}")
        return

    if data.startswith("i5_back:"):
        p_b64 = data[8:]
        import base64, json as _j
        try: prompt = base64.b64decode(p_b64.encode()).decode()
        except: prompt = p_b64
        p_enc = base64.b64encode(prompt[:40].encode()).decode()
        style_kb = _j.dumps({"inline_keyboard":
            [[{"text": lbl, "callback_data": f"i5s:{val}:{p_enc}", "style": "primary"}
              for lbl, val in PRODIA_STYLES[i:i+2]]
             for i in range(0, len(PRODIA_STYLES), 2)] +
            [[{"text": "❌ Cancel", "callback_data": "i5_cancel", "style": "danger"}]]
        })
        txt = (f"🎨 <b>Pick a Style</b>\n\n"
               f"📝 Prompt: <code>{prompt[:60]}{'...' if len(prompt)>60 else ''}</code>\n\n"
               f"Choose an art style:")
        try:
            await q.edit_message_text(txt, parse_mode="HTML", api_kwargs={"reply_markup": style_kb})
        except Exception:
            await ctx.bot.send_message(q.message.chat_id, txt, parse_mode="HTML", api_kwargs={"reply_markup": style_kb})
        return

    if data.startswith("i5_chstyle:"):
        p_b64 = data[11:]
        import base64, json as _j
        try: prompt = base64.b64decode(p_b64.encode()).decode()
        except: prompt = p_b64
        p_enc = base64.b64encode(prompt[:40].encode()).decode()
        style_kb = _j.dumps({"inline_keyboard":
            [[{"text": lbl, "callback_data": f"i5s:{val}:{p_enc}", "style": "primary"}
              for lbl, val in PRODIA_STYLES[i:i+2]]
             for i in range(0, len(PRODIA_STYLES), 2)] +
            [[{"text": "❌ Cancel", "callback_data": "i5_cancel", "style": "danger"}]]
        })
        txt = (f"🎨 <b>Change Style</b>\n\n"
               f"📝 Prompt: <code>{prompt[:60]}{'...' if len(prompt)>60 else ''}</code>\n\n"
               f"Pick a new style:")
        await ctx.bot.send_message(q.message.chat_id, txt, parse_mode="HTML", api_kwargs={"reply_markup": style_kb})
        return

    if data.startswith("i5_chaspect:"):
        rest = data[12:]
        s_enc, p_b64 = rest.split(":", 1) if ":" in rest else (rest, "")
        import base64, json as _j
        try: prompt = base64.b64decode(p_b64.encode()).decode()
        except: prompt = p_b64
        p_enc = base64.b64encode(prompt[:40].encode()).decode()
        aspect_kb = _j.dumps({"inline_keyboard": [
            [
                {"text": "⬛ Square",    "callback_data": f"i5a:square:{s_enc}:{p_enc}",   "style": "primary"},
                {"text": "📱 Portrait",  "callback_data": f"i5a:portrait:{s_enc}:{p_enc}", "style": "primary"},
                {"text": "🖼 Landscape", "callback_data": f"i5a:landscape:{s_enc}:{p_enc}","style": "primary"},
            ],
            [{"text": "❌ Cancel", "callback_data": "i5_cancel", "style": "danger"}],
        ]})
        txt = (f"🖼 <b>Change Aspect Ratio</b>\n\n"
               f"📝 Prompt: <code>{prompt[:60]}{'...' if len(prompt)>60 else ''}</code>\n\n"
               f"Pick a new aspect:")
        await ctx.bot.send_message(q.message.chat_id, txt, parse_mode="HTML", api_kwargs={"reply_markup": aspect_kb})
        return

    if data.startswith("i5_regen:"):
        rest = data[9:]
        parts = rest.split(":", 2)
        if len(parts) == 3:
            s_enc, a_enc, p_b64 = parts
            import base64
            try: prompt = base64.b64decode(p_b64.encode()).decode()
            except: prompt = p_b64
            await q.answer("🔁 Regenerating...")
            try: await q.edit_message_reply_markup(reply_markup=None)
            except: pass
            # Re-trigger i5a logic by faking callback data and re-entering
            # Simpler: directly call the generation inline
            chat_id = q.message.chat_id
            style_val = s_enc
            aspect    = a_enc
            is_owner = (u.id == OWNER_ID)
            if not is_owner:
                credits = await get_model_credits(u.id, "img5_credits")
                if credits <= 0:
                    await ctx.bot.send_message(chat_id,
                        "❌ <b>No /img5 credits left!</b>\n\n"
                        "📸 Daily free: <b>2/day</b> (resets midnight)\n"
                        "👑 Ask owner: /addcredits5", parse_mode="HTML")
                    return
            style_label  = next((l for l, v in PRODIA_STYLES if v == style_val), style_val)
            username_str = f"@{u.username}" if u.username else (u.first_name or "User")
            wm = await ctx.bot.send_message(chat_id,
                f"✨ <b>Regenerating...</b>\n"
                f"『────────────────────』\n"
                f"✦ 𝗠𝗼𝗱𝗲𝗹  │ <code>FLUX.2</code>\n"
                f"✦ 𝗣𝗿𝗼𝗺𝗽𝘁 │ <code>{prompt[:50]}{'...' if len(prompt)>50 else ''}</code>\n"
                f"✦ 𝗦𝘁𝘆𝗹𝗲  │ {style_label}\n"
                f"✦ 𝗔𝘀𝗽𝗲𝗰𝘁 │ {aspect.upper()}\n"
                f"『────────────────────』\n"
                f"<i>🖌 Crafting your exclusive creation...</i>",
                parse_mode="HTML")
            import aiohttp, urllib.parse, time as _t, base64 as _b64, json as _j
            start = _t.time()
            try:
                enc = urllib.parse.quote_plus(prompt.strip())
                url = f"{PRODIA_API_BASE}?prompt={enc}&style={style_val}&aspect={aspect}"
                async with aiohttp.ClientSession() as s:
                    async with s.get(url, timeout=aiohttp.ClientTimeout(total=90)) as r:
                        rj = await r.json(content_type=None)
                image_url = rj.get("image_url")
                if not image_url:
                    err = rj.get("error") or rj.get("message") or str(rj)[:200]
                    try: await wm.delete()
                    except: pass
                    await ctx.bot.send_message(chat_id, f"❌ <b>Generation failed</b>\n<code>{err}</code>", parse_mode="HTML")
                    return
                taken = int(_t.time() - start)
                dims  = rj.get("dimensions", "—")
                if not is_owner:
                    await deduct_model_credit(u.id, "img5_credits")
                    cl = await get_model_credits(u.id, "img5_credits")
                    credits_line = f"📸 Credits Left • <b>{cl}</b> remaining today"
                else:
                    credits_line = "👑 Owner Access • Unlimited"
                p_enc2 = _b64.b64encode(prompt[:40].encode()).decode()
                regen_kb = _j.dumps({"inline_keyboard": [
                    [
                        {"text": "🎨 Change Style",  "callback_data": f"i5_chstyle:{p_enc2}", "style": "primary"},
                        {"text": "🖼 Change Aspect", "callback_data": f"i5_chaspect:{style_val[:20]}:{p_enc2}", "style": "primary"},
                    ],
                    [
                        {"text": "🔁 Regenerate",   "callback_data": f"i5_regen:{style_val[:20]}:{aspect[:10]}:{p_enc2}", "style": "success"},
                        {"text": "✅ Done",          "callback_data": "i5_cancel", "style": "danger"},
                    ],
                ]})
                caption = (
                    f"✨ <b>Image Generated!</b>\n"
                    f"╭━━━━━━━━━━━━━━━━━━╮\n"
                    f"│ 👤 User » {username_str}\n"
                    f"│ 🎭 Style » {style_label}\n"
                    f"│ 🖼 Aspect » {aspect.upper()} ({dims})\n"
                    f"│ 📝 Prompt » {prompt[:55]}{'...' if len(prompt)>55 else ''}\n"
                    f"│ ⚡ Time » {taken}s\n"
                    f"╰━━━━━━━━━━━━━━━━━━╯\n"
                    f"{credits_line}\n\n"
                    f"🔁 <b>Regenerate or change style/aspect:</b>"
                )
                try: await wm.delete()
                except: pass
                await ctx.bot.send_photo(chat_id, photo=image_url, caption=caption, parse_mode="HTML",
                                         api_kwargs={"reply_markup": regen_kb})
            except asyncio.TimeoutError:
                try: await wm.delete()
                except: pass
                await ctx.bot.send_message(chat_id, "❌ Timed out (90s). Try again!")
            except Exception as e:
                try: await wm.delete()
                except: pass
                await ctx.bot.send_message(chat_id, f"❌ Generation failed: {e}")
        return

    if data == "i5_cancel":
        IMG5_STATE.pop(u.id, None)
        try: await q.edit_message_reply_markup(reply_markup=None)
        except: pass
        await q.answer("✅ Done.")
        return

    # ── img6 callbacks ─────────────────────────────────
    if data.startswith("i6_regen:"):
        safe_p = data[9:]
        full_prompt = IMG6_STATE.get(u.id, {}).get("prompt", safe_p)
        await q.answer("🔁 Regenerating...")
        try: await q.edit_message_reply_markup(reply_markup=None)
        except: pass
        await _do_ddg_gen(q.message, u, full_prompt)
        return

    if data == "i6_done":
        IMG6_STATE.pop(u.id, None)
        try: await q.edit_message_reply_markup(reply_markup=None)
        except: pass
        await q.answer("✅ Done!")
        return

    if data.startswith("i6_ans:"):
        # i6_ans:<yes|no>:<request_id>
        rest = data[7:]
        answer, safe_id = rest.split(":", 1) if ":" in rest else (rest, "")
        state = IMG6_STATE.get(u.id, {})
        request_id = state.get("request_id", safe_id)
        prompt = state.get("prompt", "")
        await q.answer("✅ Sending reply...")
        try: await q.edit_message_reply_markup(reply_markup=None)
        except: pass
        # Send reply to DDG API
        import aiohttp as _ah
        wm = await q.message.reply_text(
            f"💬 <b>Reply sent:</b> <code>{answer}</code>\n"
            f"⏳ Waiting for result...",
            parse_mode="HTML"
        )
        try:
            async with _ah.ClientSession() as session:
                async with session.post(
                    f"{DDG_API_BASE}/image/reply",
                    json={"id": request_id, "message": answer},
                    timeout=_ah.ClientTimeout(total=15)
                ) as r:
                    await r.json(content_type=None)
            # Poll for result
            result = await _ddg_poll(request_id, "image")
            try: await wm.delete()
            except: pass
            if result.get("status") == "needs_reply":
                question = result.get("text", "AI needs more info.")
                await q.message.reply_text(
                    f"❓ <b>AI is asking again:</b>\n\n<i>{question}</i>",
                    parse_mode="HTML",
                    api_kwargs={"reply_markup": kb_img6_reply(request_id, question)},
                )
                return
            if result.get("status") != "done" or not result.get("images"):
                err = result.get("error", "No images returned")
                await q.message.reply_text(f"❌ <b>Failed:</b> <code>{err}</code>", parse_mode="HTML")
                return
            # Success
            is_owner = (u.id == OWNER_ID)
            if not is_owner:
                await deduct_model_credit(u.id, "img6_credits")
                credits_left = await get_model_credits(u.id, "img6_credits")
                credits_line = f"📸 Credits Left • <b>{credits_left}</b> remaining today"
            else:
                credits_line = "👑 Owner Access • Unlimited"
            username_str = f"@{u.username}" if u.username else (u.first_name or "User")
            model_str = result.get("model", "GPT Image 2")
            caption = (
                f"✨ <b>Image Generated!</b>\n"
                f"╭━━━━━━━━━━━━━━━━━━╮\n"
                f"│ 👤 User » {username_str}\n"
                f"│ 🤖 Model » {model_str}\n"
                f"│ 📝 Prompt » {prompt[:55]}{'...' if len(prompt)>55 else ''}\n"
                f"╰━━━━━━━━━━━━━━━━━━╯\n"
                f"{credits_line}\n\n"
                f"🔁 <b>Regenerate or done:</b>"
            )
            await q.message.reply_photo(
                photo=result["images"][0],
                caption=caption,
                parse_mode="HTML",
                api_kwargs={"reply_markup": kb_img6_regen(prompt)},
            )
        except Exception as e:
            try: await wm.delete()
            except: pass
            await q.message.reply_text(f"❌ Generation failed: {e}")
        return

    if data.startswith("i6_custom:"):
        safe_id = data[10:]
        state = IMG6_STATE.get(u.id, {})
        request_id = state.get("request_id", safe_id)
        IMG6_STATE.setdefault(u.id, {})["awaiting_reply"] = request_id
        try: await q.edit_message_reply_markup(reply_markup=None)
        except: pass
        await q.message.reply_text(
            "💬 <b>Type your reply</b> as a normal message.\n"
            "<i>Just send it in chat — bot will forward it automatically.</i>",
            parse_mode="HTML"
        )
        return

    # ── Aspect ratio regen (img2/3/4) ───────────
    if data.startswith("aspect:"):
        parts = data.split(":", 3)
        if len(parts) == 4:
            _, cmd_name, aspect, prompt = parts
            if cmd_name not in ("img2", "img3", "img4"):
                await q.answer("Unknown command.", show_alert=True); return
            aspect_val = aspect if aspect != "none" else None
            aspect_disp = aspect.upper() if aspect != "none" else "Auto"
            await q.answer(f"🖼 Generating with {aspect_disp} aspect...")
            # Remove the keyboard from the original message so it can't be double-pressed
            try:
                await q.edit_message_reply_markup(reply_markup=None)
            except Exception:
                pass
            class _FakeUpdate:
                def __init__(self, msg):
                    self.message = msg
                    self.effective_chat = msg.chat
                    self.effective_user = u
            await _do_bing_img_gen(_FakeUpdate(q.message), u, prompt, cmd_name, aspect_val)
        return

    # ── Start menu ──────────────────────────────
    if data == "cb_start":
        user = await get_user(u.id, u.username, u.first_name)
        prem = await is_premium(u.id)
        badge = "💓 Premium" if prem else "👤 Free"
        alive_txt = "✅ Alive" if user["is_alive"] else "💀 Dead"
        prem_line = "\n✦ <b>PREMIUM MEMBER</b> 💓" if prem else ""
        await q.edit_message_text(
            f"⚡ <b>ZADE BOT</b> — Dashboard{prem_line}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 {mention(u)}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💵 Balance  ›  <b>{cash(user['balance'])}</b>\n"
            f"💎 Gems     ›  <b>{user['gems']}</b>\n"
            f"🏅 XP       ›  <b>{user['xp']}</b>\n"
            f"⚔️ Kills    ›  <b>{user['kills']}</b>\n"
            f"❤️ Status   ›  {alive_txt}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━",
            parse_mode="HTML", reply_markup=kb_start(ctx.bot.username)
        )

    elif data == "cb_bal":
        user = await get_user(u.id, u.username, u.first_name)
        prem = await is_premium(u.id)
        prefix = "💓" if prem else "👤"
        alive  = "✅ Alive" if user["is_alive"] else "💀 Dead"
        await q.edit_message_text(
            f"💰 <b>Your Balance</b>\n\n{prefix} Status: {alive}\n"
            f"💵 Cash: <b>{cash(user['balance'])}</b>\n"
            f"💎 Gems: <b>{user['gems']}</b>\n"
            f"⚔️ Kills: <b>{user['kills']}</b>\n"
            f"🏅 XP: <b>{user['xp']}</b>",
            parse_mode="HTML",
            reply_markup=_rm([_b("« Back", cb="cb_start")])
        )

    elif data == "cb_help":
        await q.edit_message_text(
            f"╔══════════════════════╗\n║    ⚡ <b>{BOT_NAME} BOT</b>       ║\n╚══════════════════════╝\n\nSelect a category:",
            parse_mode="HTML", reply_markup=kb_help()
        )

    elif data in HELP_PAGES:
        await q.edit_message_text(
            HELP_PAGES[data](),
            parse_mode="HTML",
            reply_markup=_rm([_b("« Back", cb="cb_help")])
        )

    elif data == "cb_lb":
        top  = await lb_top10()
        text = "🏆 <b>Balance Leaderboard — Top 10</b>\n\n"
        for i, r in enumerate(top, 1):
            p    = "💓" if r["is_premium"] else "👤"
            name = r["first_name"] or r["username"] or "User"
            text += f"<b>{i}.</b> {p} {name} — <b>{cash(r['balance'])}</b>\n"
        await q.edit_message_text(text, parse_mode="HTML", reply_markup=kb_lb())

    elif data == "lb_balance":
        top  = await lb_top10()
        text = "💰 <b>Top 10 Richest</b>\n\n"
        for i, r in enumerate(top, 1):
            p    = "💓" if r["is_premium"] else "👤"
            name = r["first_name"] or r["username"] or "User"
            text += f"<b>{i}.</b> {p} {name} — <b>{cash(r['balance'])}</b>\n"
        await q.edit_message_text(text, parse_mode="HTML", reply_markup=kb_lb())

    elif data == "lb_kills":
        top  = await get_top_kills()
        text = "⚔️ <b>Top 10 Killers</b>\n\n"
        for i, r in enumerate(top, 1):
            p    = "💓" if r["is_premium"] else "👤"
            name = r["first_name"] or r["username"] or "User"
            text += f"<b>{i}.</b> {p} {name} — <b>{r['kills']} kills</b>\n"
        await q.edit_message_text(text, parse_mode="HTML", reply_markup=_rm([_b("« Back", cb="cb_lb")]))

    elif data == "cb_premium":
        await q.edit_message_text(
            "👑 <b>Buy Premium</b>\n\n"
            "• 2× rewards on rob & kill\n"
            "• Lower tax (5%)\n"
            "• 100 💎 Gems/day\n"
            "• Custom sticker trigger\n\n"
            "Select a plan:",
            parse_mode="HTML", reply_markup=kb_premium()
        )

    elif data.startswith("buy_"):
        plan = data[4:]
        if plan not in PREMIUM_PRICES:
            await q.answer("Invalid plan.", show_alert=True); return
        if await is_premium(u.id):
            await q.answer("You're already Premium! 💓", show_alert=True); return
        user = await get_user(u.id, u.username, u.first_name)
        cost = PREMIUM_PRICES[plan]
        if user["balance"] < cost:
            await q.answer(f"❌ Need {cash(cost)}. You have {cash(user['balance'])}.", show_alert=True); return
        hours = {"24h": 24, "48h": 48, "7d": 168}[plan]
        until = int(time.time()) + hours * 3600
        await add_bal(u.id, -cost)
        await upd(u.id, is_premium=1, premium_until=until)
        exp_dt = datetime.fromtimestamp(until).strftime("%Y-%m-%d %H:%M")
        name = (u.first_name or u.username or "User")[:20]
        await q.edit_message_text(
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💓 <b>Premium Activated!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👤 {name}\n"
            f"📦 Plan: <b>{plan}</b>\n"
            f"💸 Paid: <b>{cash(cost)}</b>\n"
            f"⏳ Expires: <b>{exp_dt}</b>\n\n"
            f"Enjoy your premium perks! ✨",
            parse_mode="HTML",
            reply_markup=_rm([_b("« Back", cb="cb_start")])
        )

    # ── Voice demo ──────────────────────────────
    elif data.startswith("voice_demo_"):
        key = data[len("voice_demo_"):]
        if key not in AVAILABLE_VOICES:
            await q.answer("Unknown voice.", show_alert=True); return
        demo_text = VOICE_DEMOS.get(key, f"Hi, I'm {key.title()}!")
        voice = AVAILABLE_VOICES[key]
        tmp_path = None
        try:
            import edge_tts, uuid
            tmp_path = f"/tmp/demo_{uuid.uuid4().hex}.mp3"
            communicate = edge_tts.Communicate(text=demo_text, voice=voice)
            await communicate.save(tmp_path)
            with open(tmp_path, "rb") as f:
                await q.message.reply_voice(
                    voice=f,
                    caption=f"🔊 <b>{key.title()}</b> — {voice}\n<i>{demo_text}</i>",
                    parse_mode="HTML"
                )
        except Exception as e:
            err = str(e)
            if "403" in err or "wss" in err.lower():
                await q.message.reply_text("❌ TTS service temporarily unavailable. Try again shortly.")
            else:
                await q.message.reply_text(f"❌ Demo failed: {err}")
        finally:
            if tmp_path:
                try: os.unlink(tmp_path)
                except: pass

    # ── XP Shop purchase ─────────────────────────
    elif data.startswith("xpbuy_"):
        key = data[6:]
        if key not in XP_SHOP:
            await q.answer("Invalid item.", show_alert=True); return
        item = XP_SHOP[key]
        user = await get_user(u.id, u.username, u.first_name)
        if user["xp"] < item["xp"]:
            await q.answer(f"❌ Need {item['xp']} XP. You have {user['xp']}.", show_alert=True); return
        items = get_xp_items(user)
        items[key] = items.get(key, 0) + 1
        await save_xp_items(u.id, items)
        await upd(u.id, xp=user["xp"] - item["xp"])
        await q.answer(f"✅ Purchased: {item['desc'][:30]}!", show_alert=True)
        await q.edit_message_text(
            f"✅ <b>Purchase Successful!</b>\n\n🛒 {item['desc']}\n💰 Cost: {item['xp']} XP\n🏅 Remaining XP: {user['xp'] - item['xp']}",
            parse_mode="HTML"
        )

    # ── Owner Panel ──────────────────────────────
    elif data == "panel_groups":
        if u.id != OWNER_ID: await q.answer("Owner only.", show_alert=True); return
        groups = await get_active_groups()
        # Also count from group_join table for more accurate count
        async with aiosqlite.connect(DB_PATH) as _d:
            async with _d.execute("SELECT COUNT(DISTINCT group_id) FROM group_join") as _c:
                join_count = (await _c.fetchone())[0]
        text = (
            f"╔══════════════════════╗\n"
            f"║  📊  <b>ACTIVE GROUPS</b>  ║\n"
            f"╚══════════════════════╝\n\n"
            f"  🏠  Claimed groups: <b>{len(groups)}</b>\n"
            f"  👥  Groups with members: <b>{join_count}</b>\n\n"
        )
        for g in groups[:20]:
            gid = g["group_id"]
            added = g.get("added_by", "?")
            text += f"  • <code>{gid}</code>  (claimed by <code>{added}</code>)\n"
        await q.edit_message_text(text, parse_mode="HTML", reply_markup=_rm([_b("« Back", cb="panel_back")]))

    elif data == "panel_genid":
        if u.id != OWNER_ID: await q.answer("Owner only.", show_alert=True); return
        code = await gen_clone_id()
        await q.edit_message_text(
            f"🔑 <b>Clone ID Generated</b>\n\n<code>{code}</code>\n\nSingle-use. Share with cloner.",
            parse_mode="HTML",
            reply_markup=_rm([_b("« Back", cb="panel_back")])
        )

    elif data == "panel_stats":
        if u.id != OWNER_ID: await q.answer("Owner only.", show_alert=True); return
        async with aiosqlite.connect(DB_PATH) as d:
            async with d.execute("SELECT COUNT(*) FROM users") as c:
                total_users = (await c.fetchone())[0]
            async with d.execute("SELECT COUNT(*) FROM users WHERE is_premium=1 AND premium_until>?", (int(time.time()),)) as c:
                prem_users = (await c.fetchone())[0]
        await q.edit_message_text(
            f"📈 <b>Bot Stats</b>\n\n"
            f"👥 Total users: <b>{total_users}</b>\n"
            f"💓 Premium users: <b>{prem_users}</b>",
            parse_mode="HTML",
            reply_markup=_rm([_b("« Back", cb="panel_back")])
        )

    elif data == "panel_back":
        await q.edit_message_text(
            f"╔══════════════════════╗\n"
            f"║  ⚙️  <b>OWNER PANEL</b>  ║\n"
            f"╚══════════════════════╝\n\n"
            f"  Select an action below:",
            parse_mode="HTML", reply_markup=kb_panel()
        )

    elif data == "panel_broadcast":
        if u.id != OWNER_ID: await q.answer("Owner only.", show_alert=True); return
        await q.edit_message_text(
            "📢 <b>Broadcast</b>\n\nSend: <code>/broadcast Your message here</code>",
            parse_mode="HTML",
            reply_markup=_rm([_b("« Back", cb="panel_back")])
        )

    # ── Shop callbacks ───────────────────────────
    elif data.startswith("shop_buy_"):
        item_id = data[9:]
        items = await get_shop_items()
        item_map = {i["item_id"]: i for i in items}
        if item_id not in item_map:
            await q.answer("❌ Invalid item.", show_alert=True); return
        item = item_map[item_id]
        user = await get_user(u.id, u.username, u.first_name)
        if user["balance"] < item["price"]:
            await q.answer(f"❌ Need {cash(item['price'])}. You have {cash(user['balance'])}.", show_alert=True); return
        await add_bal(u.id, -item["price"])
        # img credits — apply immediately, no inventory step
        qty_map = {"img_5": 5, "img_15": 15, "img_30": 30}
        if item_id in qty_map:
            amt = qty_map[item_id]
            await add_img_credits(u.id, amt)
            credits_now = await get_img_credits(u.id)
            await q.answer(f"✅ +{amt} image credits added!", show_alert=True)
            await q.edit_message_text(
                f"✅ <b>Purchase Successful!</b>\n\n"
                f"🎨 <b>+{amt} Image Credits</b> added instantly!\n"
                f"📸 Total credits: <b>{credits_now}</b>\n"
                f"💸 Paid: <b>{cash(item['price'])}</b>",
                parse_mode="HTML",
                reply_markup=_rm([_b("🏪 Back to Shop", cb="cb_shop", style="primary")])
            )
        else:
            await add_inventory(u.id, item_id)
            await q.answer(f"✅ Purchased {item['name']}!", show_alert=True)
            use_hint = f"\n\nUse <code>/use {item_id}</code> to activate!" if item_id != "vip_badge" else "\n\n⭐ Badge active on your profile!"
            await q.edit_message_text(
                f"✅ <b>Purchase Successful!</b>\n\n"
                f"{item['name']}\n"
                f"<i>{item['description']}</i>\n\n"
                f"💸 Paid: <b>{cash(item['price'])}</b>\n"
                f"💰 Balance left: <b>{cash(user['balance'] - item['price'])}</b>"
                f"{use_hint}",
                parse_mode="HTML",
                reply_markup=_rm([_b("🏪 Back to Shop", cb="cb_shop", style="primary")])
            )

    elif data == "shop_inv":
        inv = await get_inventory(u.id)
        all_items = await get_shop_items()
        item_map = {i["item_id"]: i for i in all_items}
        if not inv:
            await q.answer("Your inventory is empty!", show_alert=True); return
        text = "🎒 <b>Your Inventory</b>\n\n"
        for item_id, qty in inv.items():
            meta = item_map.get(item_id, {})
            name = meta.get("name", item_id)
            text += f"• {name} × <b>{qty}</b>\n"
        await q.edit_message_text(
            text, parse_mode="HTML",
            reply_markup=_rm([_b("🏪 Back to Shop", cb="cb_shop", style="primary")])
        )

    elif data == "cb_shop":
        items = await get_shop_items()
        user = await get_user(u.id, u.username, u.first_name)
        text = (
            f"🏪 <b>Cash Shop</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💵 Your Balance: <b>{cash(user['balance'])}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        )
        for item in items:
            text += f"• <b>{item['name']}</b> — {cash(item['price'])}\n  <i>{item['description']}</i>\n\n"
        await q.edit_message_text(text, parse_mode="HTML", reply_markup=kb_shop(items))

    # ── Clone info from help ─────────────────────
    elif data == "help_clone":
        await q.edit_message_text(
            f"╔══════════════════════╗\n"
            f"║  🤖  <b>CLONE THIS BOT</b>  ║\n"
            f"╚══════════════════════╝\n\n"
            f"To clone Zade Bot:\n\n"
            f"  1️⃣  Contact @Zade4everbot to get a <b>Clone ID</b>\n"
            f"  2️⃣  Start the bot in DM\n"
            f"  3️⃣  Send <code>/clone YOUR_ID</code>\n"
            f"  4️⃣  Follow the setup steps\n"
            f"  5️⃣  Get your full source code + shell commands\n\n"
            f"  🎁  You get the <b>complete bot</b> with your token,\n"
            f"  name and owner ID pre-filled!",
            parse_mode="HTML",
            reply_markup=_rm([_b("🤖 Contact Owner", url="https://t.me/Zade4everbot", style="primary")], [_b("« Back", cb="cb_help")])
        )

    # ── Clone flow ───────────────────────────────
    elif data == "clone_joinyesno_yes":
        state = CLONE_STEPS.get(u.id, {})
        state["join_required"] = True
        state["step"] = "wait_channel"
        CLONE_STEPS[u.id] = state
        await q.edit_message_text("📢 Send your <b>channel username or invite link</b> (e.g. @mychannel or https://t.me/mychannel):", parse_mode="HTML")

    elif data == "clone_joinyesno_no":
        state = CLONE_STEPS.get(u.id, {})
        state["join_required"] = False
        state["channel"] = None
        state["group"] = None
        state["step"] = "wait_token"
        CLONE_STEPS[u.id] = state
        await q.edit_message_text("🔑 Send your <b>bot token</b> (from @BotFather):", parse_mode="HTML")

    elif data == "clone_tbh":
        await q.message.reply_text(
            "🚀 <b>TeleBotHosting Guide</b>\n\n"
            "1. Go to https://telebot-hosting.com\n"
            "2. Create a new project\n"
            "3. Upload the .py file sent to you\n"
            "4. Install requirements via shell:\n"
            "<pre>pip install python-telegram-bot aiosqlite aiohttp edge-tts deep-translator</pre>\n"
            "5. Run: <code>python yourbot.py</code>\n\n"
            "⚡ Done!",
            parse_mode="HTML"
        )

# ══════════════════════════════════════════════════════════════════
#  HANDLERS — CASH SHOP
# ══════════════════════════════════════════════════════════════════
async def get_shop_items():
    async with aiosqlite.connect(DB_PATH) as d:
        d.row_factory = aiosqlite.Row
        async with d.execute("SELECT * FROM shop_items WHERE active=1") as c:
            return [dict(r) for r in await c.fetchall()]

async def get_inventory(uid):
    async with aiosqlite.connect(DB_PATH) as d:
        d.row_factory = aiosqlite.Row
        async with d.execute("SELECT * FROM user_inventory WHERE user_id=? AND quantity>0", (uid,)) as c:
            return {r["item_id"]: r["quantity"] for r in await c.fetchall()}

async def add_inventory(uid, item_id, qty=1):
    async with aiosqlite.connect(DB_PATH) as d:
        await d.execute(
            "INSERT INTO user_inventory(user_id,item_id,quantity) VALUES(?,?,?) "
            "ON CONFLICT(user_id,item_id) DO UPDATE SET quantity=quantity+?",
            (uid, item_id, qty, qty)
        )
        await d.commit()

async def use_inventory(uid, item_id):
    async with aiosqlite.connect(DB_PATH) as d:
        async with d.execute("SELECT quantity FROM user_inventory WHERE user_id=? AND item_id=?", (uid, item_id)) as c:
            r = await c.fetchone()
        if not r or r[0] <= 0:
            return False
        await d.execute("UPDATE user_inventory SET quantity=quantity-1 WHERE user_id=? AND item_id=?", (uid, item_id))
        await d.commit()
        return True

def kb_shop(items):
    import json as _j
    rows = []
    for item in items:
        rows.append([_b(f"🛒 {item['name']} — {cash(item['price'])}", cb=f"shop_buy_{item['item_id']}", style="primary")])
    rows.append([_b("🎒 My Inventory", cb="shop_inv", style="success")])
    rows.append([_b("« Back", cb="cb_start")])
    return _j.dumps({"inline_keyboard": rows})

async def cmd_shop(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    items = await get_shop_items()
    u = update.effective_user
    user = await get_user(u.id, u.username, u.first_name)
    text = (
        f"🏪 <b>Cash Shop</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💵 Your Balance: <b>{cash(user['balance'])}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    for item in items:
        text += f"• <b>{item['name']}</b> — {cash(item['price'])}\n  <i>{item['description']}</i>\n\n"
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=kb_shop(items))

async def cmd_inv(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    inv = await get_inventory(u.id)
    items = await get_shop_items()
    item_map = {i["item_id"]: i for i in items}
    if not inv:
        await update.message.reply_text("🎒 Your inventory is empty. Use /shop to buy items!"); return
    text = "🎒 <b>Your Inventory</b>\n\n"
    for item_id, qty in inv.items():
        meta = item_map.get(item_id, {})
        name = meta.get("name", item_id)
        desc = meta.get("description", "")
        text += f"• {name} × <b>{qty}</b>\n  <i>{desc}</i>\n\n"
    await update.message.reply_text(text, parse_mode="HTML")

async def cmd_use(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if not ctx.args:
        await update.message.reply_text("Usage: /use <item_id>\n\nCheck /inv for your items."); return
    item_id = ctx.args[0].lower()
    user = await get_user(u.id, u.username, u.first_name)

    if item_id == "lucky_rob":
        ok = await use_inventory(u.id, item_id)
        if not ok: await update.message.reply_text("❌ You don't have Lucky Rob!"); return
        # Store pending effect in xp_items style
        items = get_xp_items(user)
        items["lucky_rob"] = items.get("lucky_rob", 0) + 1
        await save_xp_items(u.id, items)
        await update.message.reply_text("🍀 <b>Lucky Rob activated!</b> Your next rob will give 2× loot!", parse_mode="HTML")

    elif item_id == "shield_1d":
        ok = await use_inventory(u.id, item_id)
        if not ok: await update.message.reply_text("❌ You don't have Shield 1D!"); return
        until = int(time.time()) + 86400
        await upd(u.id, protected_until=until)
        await update.message.reply_text("🛡️ <b>Shield activated!</b> You're protected for 24 hours!", parse_mode="HTML")

    elif item_id == "bomb":
        if not update.message.reply_to_message:
            await update.message.reply_text("↩️ Reply to target to use Bomb!"); return
        target = update.message.reply_to_message.from_user
        if target.is_bot: await update.message.reply_text("❌ Can't bomb a bot!"); return
        if target.id == OWNER_ID: await update.message.reply_text("❌ Can't bomb the owner!"); return
        ok = await use_inventory(u.id, item_id)
        if not ok: await update.message.reply_text("❌ You don't have a Bomb!"); return
        victim = await get_user(target.id, target.username, target.first_name)
        if not victim["is_alive"]:
            await update.message.reply_text(f"💀 {mention(target)} is already dead!", parse_mode="HTML"); return
        await upd(target.id, is_alive=0)
        await update.message.reply_text(
            f"💣 <b>BOOM!</b> {mention(u)} bombed {mention(target)}!\n💀 Instant kill — no protection checks!",
            parse_mode="HTML"
        )

    elif item_id in ("img_5", "img_15", "img_30"):
        qty_map = {"img_5": 5, "img_15": 15, "img_30": 30}
        ok = await use_inventory(u.id, item_id)
        if not ok: await update.message.reply_text(f"❌ You don't have {item_id}!"); return
        amt = qty_map[item_id]
        await add_img_credits(u.id, amt)
        credits_now = await get_img_credits(u.id)
        await update.message.reply_text(
            f"🎨 <b>+{amt} Image Credits added!</b>\n\n"
            f"📸 Total credits now: <b>{credits_now}</b>",
            parse_mode="HTML"
        )

    elif item_id == "mystery_box":
        ok = await use_inventory(u.id, item_id)
        if not ok: await update.message.reply_text("❌ You don't have a Mystery Box!"); return
        # Weighted random outcomes
        roll = random.random()
        if roll < 0.35:
            # Cash reward
            prize = random.choice([1000, 2000, 3000, 5000, 7000])
            await add_bal(u.id, prize)
            result = f"💰 <b>{cash(prize)}</b> cash!"
        elif roll < 0.55:
            # Image credits
            prize = random.choice([5, 10, 20])
            await add_img_credits(u.id, prize)
            result = f"🎨 <b>{prize} image credits!</b>"
        elif roll < 0.70:
            # Lucky Rob item
            await add_inventory(u.id, "lucky_rob")
            result = "🍀 <b>Lucky Rob</b> item! (next rob = 2x)"
        elif roll < 0.82:
            # Shield 1D
            until = int(time.time()) + 86400
            await upd(u.id, protected_until=until)
            result = "🛡️ <b>1 Day Shield!</b> You're protected!"
        elif roll < 0.92:
            # XP bonus
            prize = random.choice([100, 200, 500])
            user_now = await get_user(u.id)
            await upd(u.id, xp=user_now["xp"] + prize)
            result = f"🏅 <b>+{prize} XP!</b>"
        elif roll < 0.98:
            # Bomb item
            await add_inventory(u.id, "bomb")
            result = "💣 <b>Bomb!</b> Instant kill item!"
        else:
            # JACKPOT
            prize = random.randint(20000, 50000)
            await add_bal(u.id, prize)
            result = f"🎰 <b>JACKPOT! {cash(prize)}!!!</b> 🎉🎉🎉"
        await update.message.reply_text(
            f"🎁 <b>Mystery Box Opened!</b>\n\n"
            f"You got: {result}",
            parse_mode="HTML"
        )

    elif item_id == "vip_badge":
        await update.message.reply_text("⭐ VIP Badge is a profile cosmetic — it shows on your /bal and /details!")
    else:
        await update.message.reply_text(f"❌ Unknown item: <code>{item_id}</code>. Check /inv.", parse_mode="HTML")

# ══════════════════════════════════════════════════════════════════
#  HANDLERS — IMAGE GENERATION (Groups only)
# ══════════════════════════════════════════════════════════════════
IMG_STYLES = [
    "pointillism","typography","line_art","caricature","adorable_kawaii",
    "psychedelic","watercolor","colored_pencil_art","futuristic_retro_cyberpunk",
    "stained_glass","comic","sumi_e_symbolic","monochrome","van_gogh","manga",
    "surreal_painting","papercraft_kirigami","papercraft_paper_quilling","pixel_art",
    "cubist","papercraft_paper_mache","lowpoly","sticker","dripping_paint_splatter",
    "ink_dripping","cross_stitching","graffiti","alcohol_ink","tlingit_art",
    "pop_art","fauvism"
]
IMG_DAILY_FREE = 5   # free credits per day for normal users

async def get_img_credits(uid):
    today = str(date.today())
    async with aiosqlite.connect(DB_PATH) as d:
        d.row_factory = aiosqlite.Row
        async with d.execute("SELECT credits, last_reset FROM img_credits WHERE user_id=?", (uid,)) as c:
            r = await c.fetchone()
        if not r:
            await d.execute("INSERT OR IGNORE INTO img_credits(user_id,credits,last_reset) VALUES(?,?,?)", (uid, IMG_DAILY_FREE, today))
            await d.commit()
            return IMG_DAILY_FREE
        r = dict(r)
        if r["last_reset"] != today:
            # Daily reset — but only reset to free amount if current < free amount
            # (extra purchased credits carry over)
            new_credits = max(r["credits"], IMG_DAILY_FREE)
            await d.execute("UPDATE img_credits SET credits=?, last_reset=? WHERE user_id=?", (new_credits, today, uid))
            await d.commit()
            return new_credits
        return r["credits"]

async def deduct_img_credit(uid):
    async with aiosqlite.connect(DB_PATH) as d:
        await d.execute("UPDATE img_credits SET credits=MAX(0,credits-1) WHERE user_id=?", (uid,))
        await d.commit()

async def add_img_credits(uid, amount):
    today = str(date.today())
    async with aiosqlite.connect(DB_PATH) as d:
        await d.execute(
            "INSERT INTO img_credits(user_id,credits,last_reset) VALUES(?,?,?) "
            "ON CONFLICT(user_id) DO UPDATE SET credits=credits+?",
            (uid, amount, today, amount)
        )
        await d.commit()

# ── New model credit helpers (img2–img5, 2/day, no shop) ──────────

MODEL_DAILY_FREE = 2  # daily free credits for /img2–/img5

MODEL_INFO = {
    "img2":    {"table": "img2_credits",   "model": "dalle",   "label": "DALL-E 3",       "wait": "10–60s",  "timeout": 120},
    "img3":    {"table": "img3_credits",   "model": "gpt4o",   "label": "GPT-4o",          "wait": "40–100s", "timeout": 200},
    "img4":    {"table": "img4_credits",   "model": "ma1",     "label": "MA-1",            "wait": "60–120s", "timeout": 240},
    "img6":    {"table": "img6_credits",   "model": "ddg",     "label": "GPT Image 2", "wait": "30–60s",  "timeout": 150},
    "imgpro":  {"table": "imgpro_credits", "model": "gpt_image_2_edit", "label": "GPT IMAGE PRO", "wait": "60–120s", "timeout": 150},
}

# ── img5 API config ────────────────────────────────
PRODIA_API_BASE = "https://zade-prodimg-api.vercel.app/v1"
PRODIA_STYLES = [
    ("📷 Photographic",  "photographic"),
    ("🎬 Cinematic",     "cinematic"),
    ("🌸 Anime",         "anime"),
    ("🎨 Digital Art",   "digital-art"),
    ("🧙 Fantasy Art",   "fantasy-art"),
    ("💥 Comic Book",    "comic-book"),
    ("⚡ Neon Punk",     "neon-punk"),
    ("👾 Pixel Art",     "pixel-art"),
    ("✏️ Line Art",      "line-art"),
    ("🔷 Low Poly",      "low-poly"),
    ("📄 Origami",       "origami"),
    ("🧊 3D Model",      "3d-model"),
]
PRODIA_ASPECTS = [
    ("⬛ Square",    "square"),
    ("📱 Portrait",  "portrait"),
    ("🖼 Landscape", "landscape"),
]

# State store: {user_id: {"prompt":..., "style":..., "aspect":..., "chat_id":...}}
IMG5_STATE: dict = {}

# ── img6 API config ────────────────────────────────────
DDG_API_BASE   = "https://ddg-api-iota.vercel.app/api"
DDG_POLL_WAIT  = 30   # initial wait before first poll
DDG_POLL_INT   = 8    # poll every 8s
DDG_POLL_MAX   = 150  # max total wait seconds

# {user_id: {"prompt":..., "request_id":..., "chat_id":..., "msg_id":...}}
IMG6_STATE: dict = {}

BING_IMG_BASE = "https://zade-bingimg-api.vercel.app/"

# Account selection: 0=auto-rotate(6h), 1=account1, 2=account2
BING_ACCOUNT: int = 0  # default auto-rotate

# In-memory cooldown tracker for /imgpro — {user_id: last_gen_timestamp}
IMGPRO_COOLDOWN: dict[int, float] = {}
IMGPRO_COOLDOWN_SEC = 60

async def get_model_credits(uid, table):
    today = str(date.today())
    async with aiosqlite.connect(DB_PATH) as d:
        d.row_factory = aiosqlite.Row
        async with d.execute(f"SELECT credits, last_reset FROM {table} WHERE user_id=?", (uid,)) as c:
            r = await c.fetchone()
        if not r:
            await d.execute(f"INSERT OR IGNORE INTO {table}(user_id,credits,last_reset) VALUES(?,?,?)", (uid, MODEL_DAILY_FREE, today))
            await d.commit()
            return MODEL_DAILY_FREE
        r = dict(r)
        if r["last_reset"] != today:
            await d.execute(f"UPDATE {table} SET credits=?, last_reset=? WHERE user_id=?", (MODEL_DAILY_FREE, today, uid))
            await d.commit()
            return MODEL_DAILY_FREE
        return r["credits"]

async def deduct_model_credit(uid, table):
    async with aiosqlite.connect(DB_PATH) as d:
        await d.execute(f"UPDATE {table} SET credits=MAX(0,credits-1) WHERE user_id=?", (uid,))
        await d.commit()

async def add_model_credits(uid, table, amount):
    today = str(date.today())
    async with aiosqlite.connect(DB_PATH) as d:
        await d.execute(
            f"INSERT INTO {table}(user_id,credits,last_reset) VALUES(?,?,?) "
            f"ON CONFLICT(user_id) DO UPDATE SET credits=credits+?",
            (uid, amount, today, amount)
        )
        await d.commit()

def _styled_markup(rows_with_styles: list) -> dict:
    """
    Build a raw InlineKeyboardMarkup dict with `style` field per button (Bot API 9.4+).
    rows_with_styles: list of rows; each row is a list of (text, callback_data, style|None).
    Returns a dict ready to pass as `reply_markup` in bot.send_*/edit_* via api_kwargs.
    Use build_raw_markup() helper to get the JSON string.
    """
    keyboard = []
    for row in rows_with_styles:
        kbd_row = []
        for text, cbd, style in row:
            btn = {"text": text, "callback_data": cbd}
            if style:
                btn["style"] = style
            kbd_row.append(btn)
        keyboard.append(kbd_row)
    return {"inline_keyboard": keyboard}

# kb_aspect replaced by kb_aspect_styled below

def kb_aspect_styled(cmd_name: str, prompt: str) -> str:
    """
    Raw JSON string of inline_keyboard with Bot API 9.4 `style` per button.
    callback_data capped at 64 bytes total.
    Pass via api_kwargs={"reply_markup": kb_aspect_styled(...)}
    """
    import json as _j
    prefix_max = max(len(f"aspect:{cmd_name}:{r}:") for r in ("square", "portrait", "landscape", "none"))
    max_prompt = 64 - prefix_max
    safe_prompt = prompt[:max_prompt]

    def _btn(text, ratio, style):
        return {"text": text, "callback_data": f"aspect:{cmd_name}:{ratio}:{safe_prompt}", "style": style}

    keyboard = [
        [_btn("⬛ Square", "square", "primary"),    _btn("📱 Portrait",   "portrait",  "primary")],
        [_btn("🖼 Landscape", "landscape", "primary"), _btn("✖️ None",     "none",      "danger")],
    ]
    return _j.dumps({"inline_keyboard": keyboard})


async def _do_bing_img_gen(update, u, prompt: str, cmd_name: str, aspect: str = None):
    """Image gen for /img2/3/4 using zade-bingimg-api."""
    info = MODEL_INFO[cmd_name]
    table       = info["table"]
    model       = info["model"]
    label       = info["label"]
    wait        = info["wait"]
    timeout_sec = info["timeout"]
    is_owner = (u.id == OWNER_ID)

    if not is_owner:
        credits = await get_model_credits(u.id, table)
        if credits <= 0:
            suffix = cmd_name[-1] if cmd_name != "imgpro" else "pro"
            await update.message.reply_text(
                f"❌ <b>No credits left for {label}!</b>\n\n"
                f"📸 Daily free: <b>{MODEL_DAILY_FREE}/day</b> (resets midnight)\n"
                f"⚠️ These credits are NOT available in /shop\n"
                f"👑 Ask owner: /addcredits{suffix} (owner only)",
                parse_mode="HTML"
            ); return

    if not prompt:
        await update.message.reply_text("❌ Prompt can't be empty!"); return

    username_str = f"@{u.username}" if u.username else (u.first_name or "User")
    aspect_disp  = aspect.upper() if aspect and aspect != "none" else "Auto"

    wait_msg = await update.message.reply_text(
        f"✨ <b>Generating Your Image...</b>\n"
        f"『────────────────────』\n"
        f"✦ 𝗠𝗼𝗱𝗲𝗹  │ <code>{label}</code>\n"
        f"✦ 𝗣𝗿𝗼𝗺𝗽𝘁 │ <code>{prompt[:50]}{'...' if len(prompt)>50 else ''}</code>\n"
        f"✦ 𝗔𝘀𝗽𝗲𝗰𝘁 │ {aspect_disp}\n"
        f"✦ 𝗧𝗶𝗺𝗲   │ {wait}\n"
        f"❖ 𝗥𝗲𝗾𝘂𝗲𝘀𝘁𝗲𝗱 𝗯𝘆 : <b>{username_str}</b>\n"
        f"『────────────────────』\n"
        f"<i>🖌 Crafting your exclusive creation...</i>",
        parse_mode="HTML"
    )

    start_time = time.time()
    try:
        import aiohttp, urllib.parse
        # Sanitize prompt: remove/replace commas, collapse whitespace
        clean_prompt = prompt.replace(",", " ").replace("  ", " ").strip()
        enc_prompt = urllib.parse.quote_plus(clean_prompt)
        url = f"{BING_IMG_BASE}?prompt={enc_prompt}&model={model}"
        if aspect and aspect != "none":
            url += f"&aspect={aspect}"
        # Account selection
        if BING_ACCOUNT in (1, 2):
            url += f"&account={BING_ACCOUNT}"
        # else: no param = API auto-rotates

        timeout = aiohttp.ClientTimeout(
            total=timeout_sec,
            connect=15,          # fail fast if server unreachable
            sock_read=timeout_sec  # wait full duration for response body
        )
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=timeout) as r:
                if r.status == 504:
                    raise asyncio.TimeoutError  # Vercel gateway timeout
                resp_json = await r.json(content_type=None)

        if not resp_json.get("success"):
            code    = resp_json.get("code", "UNKNOWN")
            detail  = resp_json.get("details") or resp_json.get("message") or ""
            try: await wait_msg.delete()
            except: pass

            if code == "INTERNAL_PIPELINE_FAULT" or "rejected" in detail.lower() or "safety" in detail.lower() or "block" in detail.lower():
                await update.message.reply_text(
                    f"🚫 <b>Prompt Rejected by AI Safety Filter</b>\n\n"
                    f"Your prompt was flagged and blocked.\n\n"
                    f"💡 <b>Try:</b>\n"
                    f"• Remove sensitive words\n"
                    f"• Rephrase more neutrally\n"
                    f"• Use /img (basic model) instead",
                    parse_mode="HTML"
                )
            elif code in ("RATE_LIMIT", "QUOTA_EXCEEDED"):
                await update.message.reply_text(
                    f"⏳ <b>API Rate Limited</b>\n\nToo many requests. Wait a minute and try again.",
                    parse_mode="HTML"
                )
            else:
                await update.message.reply_text(
                    f"❌ <b>Generation Failed</b> (<code>{code}</code>)\n\n"
                    f"<i>{detail[:200]}</i>\n\nTry again or use a different prompt.",
                    parse_mode="HTML"
                )
            return

        images_data = resp_json.get("images", {}).get("images", [])
        if not images_data:
            try: await wait_msg.delete()
            except: pass
            await update.message.reply_text("❌ No images returned. Try again!"); return

        time_taken = int(time.time() - start_time)
        display_prompt = prompt  # show original, not enhanced

        if not is_owner:
            await deduct_model_credit(u.id, table)
            credits_left = await get_model_credits(u.id, table)
            credits_line = f"📸 Credits Left • <b>{credits_left}</b> remaining today"
        else:
            credits_line = "👑 Owner Access • Unlimited"

        caption = (
            f"✨ <b>Image Generated!</b>\n"
            f"╭━━━━━━━━━━━━━━━━━━╮\n"
            f"│ 👤 User » {username_str}\n"
            f"│ 🤖 Model » {label}\n"
            f"│ 📝 Prompt » {display_prompt[:60]}{'...' if len(display_prompt) > 60 else ''}\n"
            f"│ 🖼 Aspect » {aspect_disp}\n"
            f"│ ⚡ Time » {time_taken}s\n"
            f"╰━━━━━━━━━━━━━━━━━━╯\n"
            f"{credits_line}\n\n"
            f"🔁 <b>Regenerate with a different aspect ratio:</b>"
        )

        try: await wait_msg.delete()
        except: pass

        # Raw JSON markup with Bot API 9.4 `style` field — passed via api_kwargs
        styled_rm_json = kb_aspect_styled(cmd_name, prompt)

        if len(images_data) == 1:
            # Single image — attach styled keyboard directly to the photo
            await update.message.reply_photo(
                photo=images_data[0]["url"],
                caption=caption,
                parse_mode="HTML",
                api_kwargs={"reply_markup": styled_rm_json},
            )
        else:
            from telegram import InputMediaPhoto
            # Send all images as media group (no keyboard support on groups)
            media = []
            for i, img in enumerate(images_data):
                if i == 0:
                    media.append(InputMediaPhoto(media=img["url"], caption=caption, parse_mode="HTML"))
                else:
                    media.append(InputMediaPhoto(media=img["url"]))
            sent = await update.message.reply_media_group(media=media)
            # Attach aspect keyboard as reply to the FIRST photo of the group
            first_msg = sent[0] if sent else None
            reply_to = first_msg.message_id if first_msg else update.message.message_id
            await update.message.get_bot().send_message(
                chat_id=update.message.chat_id,
                text="🔁 <b>Regenerate with a different aspect ratio:</b>",
                parse_mode="HTML",
                reply_to_message_id=reply_to,
                api_kwargs={"reply_markup": styled_rm_json},
            )

    except asyncio.TimeoutError:
        try: await wait_msg.delete()
        except: pass
        await update.message.reply_text(f"❌ Timed out ({timeout_sec}s). API busy, try again!")
    except Exception as e:
        try: await wait_msg.delete()
        except: pass
        await update.message.reply_text(f"❌ Image generation failed: {e}")


# KEPT FOR REFERENCE — old model gen, now unused by img2/3/4
async def _do_model_img_gen(update: Update, u, prompt: str, cmd_name: str):
    """LEGACY — only called by imgpro flow if needed."""
    info = MODEL_INFO.get(cmd_name, {})
    if not info:
        await update.message.reply_text("❌ Unknown model."); return
    # redirect to bing gen for now
    await _do_bing_img_gen(update, u, prompt, cmd_name)
    return
    is_owner = (u.id == OWNER_ID)

    if not is_owner:
        credits = await get_model_credits(u.id, table)
        if credits <= 0:
            await update.message.reply_text(
                f"❌ <b>No credits left for {label}!</b>\n\n"
                f"📸 Daily free: <b>{MODEL_DAILY_FREE}/day</b> (resets midnight)\n"
                f"⚠️ These credits are NOT available in /shop\n"
                f"👑 Ask owner: /addcredits{cmd_name[-1]} (owner only)",
                parse_mode="HTML"
            ); return

    if not prompt:
        await update.message.reply_text("❌ Prompt can't be empty!"); return

    username_str = f"@{u.username}" if u.username else (u.first_name or "User")
    num = cmd_name[-1]  # '2','3','4','5'

    wait_msg = await update.message.reply_text(
        f"✨ <b>Generating Your Image...</b>\n"
        f"『────────────────────』\n"
        f"✦ 𝗠𝗼𝗱𝗲𝗹  │ <code>{label}</code>\n"
        f"✦ 𝗣𝗿𝗼𝗺𝗽𝘁 │ <code>{prompt[:50]}{'...' if len(prompt)>50 else ''}</code>\n"
        f"✦ 𝗧𝗶𝗺𝗲   │ 30–60s\n"
        f"❖ 𝗥𝗲𝗾𝘂𝗲𝘀𝘁𝗲𝗱 𝗯𝘆 : <b>{username_str}</b>\n"
        f"『────────────────────』\n"
        f"<i>🖌Crafting your exclusive creation...</i>",
        parse_mode="HTML"
    )

    start_time = time.time()
    try:
        import aiohttp, urllib.parse
        clean_prompt = prompt.replace(",", " ").replace("  ", " ").strip()
        enc_prompt = urllib.parse.quote_plus(clean_prompt)
        url = f"https://zade-gpt2.vercel.app/api?gen={enc_prompt}&model={model}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=120)) as r:
                resp_json = await r.json(content_type=None)

        image_url = resp_json.get("image_url")
        if not image_url:
            err_msg = resp_json.get("error") or resp_json.get("message") or str(resp_json)[:200]
            try: await wait_msg.delete()
            except: pass
            await update.message.reply_text(
                f"❌ <b>Generation failed</b>\n<code>{err_msg}</code>\n\nTry a different prompt!",
                parse_mode="HTML"
            ); return

        time_taken = int(time.time() - start_time)

        if not is_owner:
            await deduct_model_credit(u.id, table)
            credits_left = await get_model_credits(u.id, table)
            credits_line = f"📸 Credits Left • <b>{credits_left}</b> remaining today"
        else:
            credits_line = "👑 Owner Access • Unlimited"

        caption = (
            f"✨ <b>Image Generated!</b>\n"
            f"╭━━━━━━━━━━━━━━━━━━╮\n"
            f"│ 👤 User » {username_str}\n"
            f"│ 🆔 ID » <code>{u.id}</code>\n"
            f"│ 🤖 Model » {label}\n"
            f"│ 📝 Prompt » {prompt[:60]}{'...' if len(prompt) > 60 else ''}\n"
            f"│ ⚡ Time » {time_taken}s\n"
            f"╰━━━━━━━━━━━━━━━━━━╯\n"
            f"{credits_line}"
        )

        try: await wait_msg.delete()
        except: pass
        await update.message.reply_photo(photo=image_url, caption=caption, parse_mode="HTML")

    except asyncio.TimeoutError:
        try: await wait_msg.delete()
        except: pass
        await update.message.reply_text("❌ Timed out (120s). API busy, try again!")
    except Exception as e:
        try: await wait_msg.delete()
        except: pass
        await update.message.reply_text(f"❌ Image generation failed: {e}")


async def cmd_img2(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if not is_group(update): await update.message.reply_text("❌ Groups only!"); return
    if not ctx.args:
        await update.message.reply_text(
            "🖼️ Usage: <code>/img2 your prompt</code>\n"
            "🤖 Model: <b>DALL-E 3</b> · 4 images · 2 tokens/day\n"
            "⏳ Wait time: 10–60s",
            parse_mode="HTML"
        ); return
    await _do_bing_img_gen(update, u, " ".join(ctx.args).strip(), "img2")

async def cmd_img3(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if not is_group(update): await update.message.reply_text("❌ Groups only!"); return
    if not ctx.args:
        await update.message.reply_text(
            "🖼️ Usage: <code>/img3 your prompt</code>\n"
            "🤖 Model: <b>GPT-4o</b> · 2 tokens/day\n"
            "⏳ Wait time: 40–100s",
            parse_mode="HTML"
        ); return
    await _do_bing_img_gen(update, u, " ".join(ctx.args).strip(), "img3")

async def cmd_img4(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if not is_group(update): await update.message.reply_text("❌ Groups only!"); return
    if not ctx.args:
        await update.message.reply_text(
            "🖼️ Usage: <code>/img4 your prompt</code>\n"
            "🤖 Model: <b>MA-1</b> · 1–2 images · 2 tokens/day\n"
            "⏳ Wait time: 60–120s",
            parse_mode="HTML"
        ); return
    await _do_bing_img_gen(update, u, " ".join(ctx.args).strip(), "img4")

# ── /img5 keyboard builders ──────────────────────────────────────

def kb_img5_styles(prompt: str) -> str:
    """Style selection keyboard for /img5 — 2 per row, styled buttons."""
    import json as _j
    safe = prompt[:30]
    rows = []
    for i in range(0, len(PRODIA_STYLES), 2):
        row = []
        for label, val in PRODIA_STYLES[i:i+2]:
            row.append({"text": label, "callback_data": f"i5s:{val}:{safe}", "style": "primary"})
        rows.append(row)
    rows.append([{"text": "❌ Cancel", "callback_data": "i5_cancel", "style": "danger"}])
    return _j.dumps({"inline_keyboard": rows})

def kb_img5_aspects(prompt: str, style: str) -> str:
    """Aspect selection keyboard for /img5."""
    import json as _j
    safe_p = prompt[:25]
    safe_s = style[:15]
    rows = [
        [
            {"text": "⬛ Square",    "callback_data": f"i5a:square:{safe_s}:{safe_p}",   "style": "primary"},
            {"text": "📱 Portrait",  "callback_data": f"i5a:portrait:{safe_s}:{safe_p}", "style": "primary"},
            {"text": "🖼 Landscape", "callback_data": f"i5a:landscape:{safe_s}:{safe_p}","style": "primary"},
        ],
        [{"text": "« Back to Styles", "callback_data": f"i5_back:{safe_p}", "style": "primary"},
         {"text": "❌ Cancel",         "callback_data": "i5_cancel",                       "style": "danger"}],
    ]
    return _j.dumps({"inline_keyboard": rows})

def kb_img5_regen(prompt: str, style: str, aspect: str) -> str:
    """Post-gen keyboard — regen with diff style/aspect."""
    import json as _j
    safe_p = prompt[:20]
    safe_s = style[:15]
    safe_a = aspect[:10]
    rows = [
        [
            {"text": "🎨 Change Style",  "callback_data": f"i5_chstyle:{safe_p}", "style": "primary"},
            {"text": "🖼 Change Aspect", "callback_data": f"i5_chaspect:{safe_s}:{safe_p}", "style": "primary"},
        ],
        [{"text": "🔁 Regenerate Same", "callback_data": f"i5_regen:{safe_s}:{safe_a}:{safe_p}", "style": "success"},
         {"text": "❌ Done",             "callback_data": "i5_cancel", "style": "danger"}],
    ]
    return _j.dumps({"inline_keyboard": rows})


async def _do_prodia_gen(msg_obj, u, prompt: str, style: str, aspect: str, edit_msg=None):
    """Core Prodia generation. msg_obj = telegram Message object."""
    import aiohttp, urllib.parse

    is_owner = (u.id == OWNER_ID)
    if not is_owner:
        credits = await get_model_credits(u.id, "img5_credits")
        if credits <= 0:
            text = (
                "❌ <b>No /img5 credits left!</b>\n\n"
                "📸 Daily free: <b>2/day</b> (resets midnight)\n"
                "👑 Ask owner: /addcredits5 (owner only)"
            )
            if edit_msg:
                await edit_msg.edit_text(text, parse_mode="HTML")
            else:
                await msg_obj.reply_text(text, parse_mode="HTML")
            return

    username_str = f"@{u.username}" if u.username else (u.first_name or "User")
    style_label  = next((l for l, v in PRODIA_STYLES if v == style), style)
    aspect_label = next((l for _, v in [] or PRODIA_ASPECTS if v == aspect), aspect.upper())

    wait_text = (
        f"✨ <b>Generating Your Image...</b>\n"
        f"『────────────────────』\n"
        f"✦ 𝗠𝗼𝗱𝗲𝗹  │ <code>FLUX.2</code>\n"
        f"✦ 𝗣𝗿𝗼𝗺𝗽𝘁 │ <code>{prompt[:50]}{'...' if len(prompt)>50 else ''}</code>\n"
        f"✦ 𝗦𝘁𝘆𝗹𝗲  │ {style_label}\n"
        f"✦ 𝗔𝘀𝗽𝗲𝗰𝘁 │ {aspect.upper()}\n"
        f"✦ 𝗧𝗶𝗺𝗲   │ 5–30s\n"
        f"❖ 𝗥𝗲𝗾𝘂𝗲𝘀𝘁𝗲𝗱 𝗯𝘆 : <b>{username_str}</b>\n"
        f"『────────────────────』\n"
        f"<i>🖌 Crafting your exclusive creation...</i>"
    )

    if edit_msg:
        wait_msg = await edit_msg.edit_text(wait_text, parse_mode="HTML")
    else:
        wait_msg = await msg_obj.reply_text(wait_text, parse_mode="HTML")

    start_time = time.time()
    try:
        enc_prompt = urllib.parse.quote_plus(prompt.strip())
        url = f"{PRODIA_API_BASE}?prompt={enc_prompt}&style={style}&aspect={aspect}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=90)) as r:
                resp_json = await r.json(content_type=None)

        image_url = resp_json.get("image_url")
        if not image_url:
            err = resp_json.get("error") or resp_json.get("message") or str(resp_json)[:200]
            try: await wait_msg.delete()
            except: pass
            await msg_obj.reply_text(f"❌ <b>Generation failed</b>\n<code>{err}</code>", parse_mode="HTML")
            return

        time_taken = int(time.time() - start_time)
        dims = resp_json.get("dimensions", "—")

        if not is_owner:
            await deduct_model_credit(u.id, "img5_credits")
            credits_left = await get_model_credits(u.id, "img5_credits")
            credits_line = f"📸 Credits Left • <b>{credits_left}</b> remaining today"
        else:
            credits_line = "👑 Owner Access • Unlimited"

        caption = (
            f"✨ <b>Image Generated!</b>\n"
            f"╭━━━━━━━━━━━━━━━━━━╮\n"
            f"│ 👤 User » {username_str}\n"
            f"│ 🎭 Style » {style_label}\n"
            f"│ 🖼 Aspect » {aspect.upper()} ({dims})\n"
            f"│ 📝 Prompt » {prompt[:55]}{'...' if len(prompt)>55 else ''}\n"
            f"│ ⚡ Time » {time_taken}s\n"
            f"╰━━━━━━━━━━━━━━━━━━╯\n"
            f"{credits_line}\n\n"
            f"🔁 <b>Regenerate or change style/aspect:</b>"
        )

        try: await wait_msg.delete()
        except: pass

        regen_kb = kb_img5_regen(prompt, style, aspect)
        await msg_obj.reply_photo(
            photo=image_url,
            caption=caption,
            parse_mode="HTML",
            api_kwargs={"reply_markup": regen_kb},
        )

    except asyncio.TimeoutError:
        try: await wait_msg.delete()
        except: pass
        await msg_obj.reply_text("❌ Timed out (90s). Generation failed, try again!")
    except Exception as e:
        try: await wait_msg.delete()
        except: pass
        await msg_obj.reply_text(f"❌ Generation failed: {e}")


async def cmd_img5(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if not is_group(update):
        await update.message.reply_text("❌ Groups only!"); return
    if not ctx.args:
        await update.message.reply_text(
            "🎨 <b>AI Image Generator</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Usage: <code>/img5 your prompt here</code>\n\n"
            "✦ 12 art styles to pick from\n"
            "✦ Square / Portrait / Landscape\n"
            "✦ Regenerate with diff style/aspect\n"
            "✦ 2 tokens/day (free)\n\n"
            "Example: <code>/img5 a cyberpunk city at night</code>",
            parse_mode="HTML"
        ); return

    prompt = " ".join(ctx.args).strip()
    import base64, json as _j
    # Encode prompt in base64 so full prompt survives in callback_data
    p_enc = base64.b64encode(prompt[:40].encode()).decode()

    rows = []
    for i in range(0, len(PRODIA_STYLES), 2):
        row = []
        for label, val in PRODIA_STYLES[i:i+2]:
            row.append({"text": label, "callback_data": f"i5s:{val}:{p_enc}", "style": "primary"})
        rows.append(row)
    rows.append([{"text": "❌ Cancel", "callback_data": "i5_cancel", "style": "danger"}])
    style_kb = _j.dumps({"inline_keyboard": rows})

    await update.message.reply_text(
        f"🎨 <b>Step 1 — Pick a Style</b>\n\n"
        f"📝 Prompt: <code>{prompt[:60]}{'...' if len(prompt)>60 else ''}</code>\n\n"
        f"Choose an art style:",
        parse_mode="HTML",
        api_kwargs={"reply_markup": style_kb},
    )



# ══════════════════════════════════════════════════════════════════
#  /img6 — AI Image Generator
# ══════════════════════════════════════════════════════════════════

def kb_img6_regen(prompt: str) -> str:
    """Post-gen keyboard for /img6."""
    import json as _j
    safe_p = prompt[:40]
    return _j.dumps({"inline_keyboard": [
        [
            {"text": "🔁 Regenerate",     "callback_data": f"i6_regen:{safe_p}", "style": "success"},
            {"text": "❌ Done",            "callback_data": "i6_done",             "style": "danger"},
        ],
    ]})

def kb_img6_reply(request_id: str, question: str) -> str:
    """Keyboard when duck.ai asks a follow-up — Yes / No / Custom reply."""
    import json as _j
    safe_id = request_id[:20]
    return _j.dumps({"inline_keyboard": [
        [
            {"text": "✅ Yes",  "callback_data": f"i6_ans:yes:{safe_id}", "style": "success"},
            {"text": "❌ No",   "callback_data": f"i6_ans:no:{safe_id}",  "style": "danger"},
        ],
        [{"text": "💬 Type Custom Reply", "callback_data": f"i6_custom:{safe_id}", "style": "primary"}],
        [{"text": "🚫 Cancel",            "callback_data": "i6_done",              "style": "danger"}],
    ]})


async def _ddg_poll(request_id: str, endpoint: str = "image") -> dict:
    """
    Poll DDG result endpoint until done/needs_reply/error/timeout.
    Returns the final result dict.
    """
    import aiohttp
    url = f"{DDG_API_BASE}/{endpoint}/result"
    elapsed = 0
    await asyncio.sleep(DDG_POLL_WAIT)
    elapsed += DDG_POLL_WAIT
    async with aiohttp.ClientSession() as session:
        while elapsed < DDG_POLL_MAX:
            try:
                async with session.post(url, json={"id": request_id},
                                        timeout=aiohttp.ClientTimeout(total=15)) as r:
                    data = await r.json(content_type=None)
                status = data.get("status", "")
                if status in ("done", "needs_reply", "error"):
                    return data
            except Exception:
                pass
            await asyncio.sleep(DDG_POLL_INT)
            elapsed += DDG_POLL_INT
    return {"status": "error", "error": "Timeout"}


async def _do_ddg_gen(msg_obj, u, prompt: str, wait_msg=None):
    """
    Trigger DDG /api/image, poll, send result with regen keyboard.
    msg_obj: the telegram Message to reply to.
    wait_msg: existing message to delete before sending result.
    """
    import aiohttp

    is_owner = (u.id == OWNER_ID)
    if not is_owner:
        credits = await get_model_credits(u.id, "img6_credits")
        if credits <= 0:
            text = (
                "❌ <b>No /img6 credits left!</b>\n\n"
                "📸 Daily free: <b>2/day</b> (resets midnight)\n"
                "👑 Ask owner: /addcredits6 (owner only)"
            )
            if wait_msg:
                try: await wait_msg.edit_text(text, parse_mode="HTML")
                except: await msg_obj.reply_text(text, parse_mode="HTML")
            else:
                await msg_obj.reply_text(text, parse_mode="HTML")
            return

    username_str = f"@{u.username}" if u.username else (u.first_name or "User")
    wait_text = (
        f"✨ <b>Generating Your Image...</b>\n"
        f"『────────────────────』\n"
        f"✦ 𝗠𝗼𝗱𝗲𝗹  │ <code>GPT Image 2</code>\n"
        f"✦ 𝗣𝗿𝗼𝗺𝗽𝘁 │ <code>{prompt[:50]}{'...' if len(prompt)>50 else ''}</code>\n"
        f"✦ 𝗧𝗶𝗺𝗲   │ 30–60s\n"
        f"❖ 𝗥𝗲𝗾𝘂𝗲𝘀𝘁𝗲𝗱 𝗯𝘆 : <b>{username_str}</b>\n"
        f"『────────────────────』\n"
        f"<i>🖌 Generating your image... please wait!</i>"
    )

    if wait_msg:
        try: wm = await wait_msg.edit_text(wait_text, parse_mode="HTML")
        except: wm = await msg_obj.reply_text(wait_text, parse_mode="HTML")
    else:
        wm = await msg_obj.reply_text(wait_text, parse_mode="HTML")

    start_time = time.time()
    try:
        # 1. Trigger
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{DDG_API_BASE}/image",
                json={"prompt": prompt},
                timeout=aiohttp.ClientTimeout(total=20)
            ) as r:
                trig = await r.json(content_type=None)

        request_id = trig.get("request_id")
        if not request_id:
            err = trig.get("error") or str(trig)[:200]
            try: await wm.delete()
            except: pass
            await msg_obj.reply_text(f"❌ <b>Generation failed:</b> <code>{err}</code>", parse_mode="HTML")
            return

        # Store state for needs_reply handling
        IMG6_STATE[u.id] = {"prompt": prompt, "request_id": request_id, "chat_id": msg_obj.chat_id}

        # 2. Poll
        result = await _ddg_poll(request_id, "image")
        time_taken = int(time.time() - start_time)

        try: await wm.delete()
        except: pass

        if result.get("status") == "needs_reply":
            question = result.get("text", "AI needs more info to continue.")
            await msg_obj.reply_text(
                f"❓ <b>AI is asking:</b>\n\n"
                f"<i>{question}</i>\n\n"
                f"Choose a reply:",
                parse_mode="HTML",
                api_kwargs={"reply_markup": kb_img6_reply(request_id, question)},
            )
            return

        if result.get("status") != "done":
            err = result.get("error", "Unknown error")
            await msg_obj.reply_text(f"❌ <b>Generation failed:</b> <code>{err}</code>", parse_mode="HTML")
            return

        images = result.get("images", [])
        if not images:
            await msg_obj.reply_text("❌ No images returned. Try again!", parse_mode="HTML")
            return

        if not is_owner:
            await deduct_model_credit(u.id, "img6_credits")
            credits_left = await get_model_credits(u.id, "img6_credits")
            credits_line = f"📸 Credits Left • <b>{credits_left}</b> remaining today"
        else:
            credits_line = "👑 Owner Access • Unlimited"

        result_type = result.get("type", "image")
        model_str   = result.get("model", "GPT Image 2")
        type_note   = " ⚠️ <i>(screenshot fallback)</i>" if result_type == "screenshot" else ""

        caption = (
            f"✨ <b>Image Generated!</b>{type_note}\n"
            f"╭━━━━━━━━━━━━━━━━━━╮\n"
            f"│ 👤 User » {username_str}\n"
            f"│ 🤖 Model » {model_str}\n"
            f"│ 📝 Prompt » {prompt[:55]}{'...' if len(prompt)>55 else ''}\n"
            f"│ ⚡ Time » {time_taken}s\n"
            f"╰━━━━━━━━━━━━━━━━━━╯\n"
            f"{credits_line}\n\n"
            f"🔁 <b>Regenerate or done:</b>"
        )

        regen_kb = kb_img6_regen(prompt)
        if len(images) == 1:
            await msg_obj.reply_photo(
                photo=images[0],
                caption=caption,
                parse_mode="HTML",
                api_kwargs={"reply_markup": regen_kb},
            )
        else:
            from telegram import InputMediaPhoto
            media = [InputMediaPhoto(media=img, caption=(caption if i == 0 else None),
                                     parse_mode="HTML") for i, img in enumerate(images)]
            await msg_obj.reply_media_group(media=media)
            await msg_obj.reply_text(
                "🔁 <b>Regenerate or done:</b>",
                parse_mode="HTML",
                api_kwargs={"reply_markup": regen_kb},
            )

    except asyncio.TimeoutError:
        try: await wm.delete()
        except: pass
        await msg_obj.reply_text("❌ Generation timed out. Try again!")
    except Exception as e:
        try: await wm.delete()
        except: pass
        await msg_obj.reply_text(f"❌ /img6 generation failed: {e}")


async def cmd_img6(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if not is_group(update):
        await update.message.reply_text("❌ Groups only!"); return
    if not ctx.args:
        await update.message.reply_text(
            "🦆 <b>AI Image Generator</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Usage: <code>/img6 your prompt here</code>\n\n"
            "✦ Powered by GPT Image 2\n"
            "✦ Multi-turn — bot handles follow-up questions\n"
            "✦ 2 tokens/day (free)\n"
            "✦ Wait time: 30–60s\n\n"
            "Example: <code>/img6 a neon samurai in the rain</code>",
            parse_mode="HTML"
        ); return

    prompt = " ".join(ctx.args).strip()
    IMG6_STATE[u.id] = {"prompt": prompt, "chat_id": update.effective_chat.id}
    await _do_ddg_gen(update.message, u, prompt)


async def cmd_addcredits6(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await _addcredits_model(update, ctx, "img6")


async def cmd_imgpro(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if not is_group(update):
        await update.message.reply_text("❌ Groups only!"); return
    if not ctx.args:
        await update.message.reply_text(
            "🖼️ Usage: <code>/imgpro your prompt</code>\n"
            "🤖 Model: <b>GPT IMAGE PRO</b> | 2 tokens/day\n"
            "⏳ 60s cooldown after each generation",
            parse_mode="HTML"
        ); return

    # Cooldown check
    now = time.time()
    last = IMGPRO_COOLDOWN.get(u.id, 0)
    elapsed = now - last
    if elapsed < IMGPRO_COOLDOWN_SEC and u.id != OWNER_ID:
        wait_secs = int(IMGPRO_COOLDOWN_SEC - elapsed) + 1
        await update.message.reply_text(
            f"⏳ <b>Cooldown Active!</b>\n\n"
            f"🕐 Wait <b>{wait_secs}s</b> before generating again with <b>GPT IMAGE PRO</b>.\n"
            f"This model takes 60–120s to generate, so cooldown keeps things fair!",
            parse_mode="HTML"
        ); return

    prompt = " ".join(ctx.args).strip()
    info = MODEL_INFO["imgpro"]
    table = info["table"]
    label = info["label"]
    model = info["model"]
    is_owner = (u.id == OWNER_ID)

    if not is_owner:
        credits = await get_model_credits(u.id, table)
        if credits <= 0:
            await update.message.reply_text(
                f"❌ <b>No credits left for {label}!</b>\n\n"
                f"📸 Daily free: <b>{MODEL_DAILY_FREE}/day</b> (resets midnight)\n"
                f"⚠️ These credits are NOT available in /shop\n"
                f"👑 Ask owner: /addcreditspro (owner only)",
                parse_mode="HTML"
            ); return

    username_str = f"@{u.username}" if u.username else (u.first_name or "User")

    wait_msg = await update.message.reply_text(
        f"✨ <b>Generating Your Image...</b>\n"
        f"『────────────────────』\n"
        f"✦ 𝗠𝗼𝗱𝗲𝗹  │ <code>{label}</code>\n"
        f"✦ 𝗣𝗿𝗼𝗺𝗽𝘁 │ <code>{prompt[:50]}{'...' if len(prompt)>50 else ''}</code>\n"
        f"✦ 𝗧𝗶𝗺𝗲   │ 60–120s\n"
        f"❖ 𝗞𝗲𝘆    │ <code>Fetching...</code>\n"
        f"『────────────────────』\n"
        f"<i>🖌 Crafting your exclusive creation... please wait!</i>",
        parse_mode="HTML"
    )

    # Set cooldown timestamp immediately after sending wait msg
    IMGPRO_COOLDOWN[u.id] = time.time()

    start_time = time.time()
    try:
        import aiohttp, urllib.parse
        clean_prompt = prompt.replace(",", " ").replace("  ", " ").strip()
        enc_prompt = urllib.parse.quote_plus(clean_prompt)
        url = f"https://zade-gpt2.vercel.app/api?gen={enc_prompt}&model={model}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=150)) as r:
                resp_json = await r.json(content_type=None)

        image_url = resp_json.get("image_url")
        if not image_url:
            err_msg = resp_json.get("error") or resp_json.get("message") or str(resp_json)[:200]
            try: await wait_msg.delete()
            except: pass
            await update.message.reply_text(
                f"❌ <b>Generation failed</b>\n<code>{err_msg}</code>\n\nTry a different prompt!",
                parse_mode="HTML"
            ); return

        time_taken = int(time.time() - start_time)
        key_used = resp_json.get("meta", {}).get("key_used")
        key_str  = f"Key:{key_used}" if key_used else "Key:—"

        if not is_owner:
            await deduct_model_credit(u.id, table)
            credits_left = await get_model_credits(u.id, table)
            credits_line = f"📸 Credits Left • <b>{credits_left}</b> remaining today"
        else:
            credits_line = "👑 Owner Access • Unlimited"

        caption = (
            f"✨ <b>Image Generated!</b>\n"
            f"╭━━━━━━━━━━━━━━━━━━╮\n"
            f"│ 👤 User » {username_str}\n"
            f"│ 🆔 ID » <code>{u.id}</code>\n"
            f"│ 🤖 Model » {label}\n"
            f"│ 🔑 Key » <b>{key_str}</b>\n"
            f"│ 📝 Prompt » {prompt[:60]}{'...' if len(prompt) > 60 else ''}\n"
            f"│ ⚡ Time » {time_taken}s\n"
            f"╰━━━━━━━━━━━━━━━━━━╯\n"
            f"{credits_line}"
        )

        try: await wait_msg.delete()
        except: pass
        await update.message.reply_photo(photo=image_url, caption=caption, parse_mode="HTML")

    except asyncio.TimeoutError:
        try: await wait_msg.delete()
        except: pass
        await update.message.reply_text("❌ Timed out (150s). This model is slow, try again later!")
    except Exception as e:
        try: await wait_msg.delete()
        except: pass
        await update.message.reply_text(f"❌ Image generation failed: {e}")


async def _addcredits_model(update, ctx, cmd_name):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Owner only."); return
    info = MODEL_INFO[cmd_name]
    if not ctx.args:
        await update.message.reply_text(f"Usage:\n/{cmd_name[-1:].join(['addcredits',''])} <amount> (reply)\n/addcredits{cmd_name[-1]} <user_id> <amount>"); return
    if len(ctx.args) >= 2 and ctx.args[0].lstrip('-').isdigit() and len(ctx.args[0]) >= 5:
        try: target_id, amount = int(ctx.args[0]), int(ctx.args[1])
        except: await update.message.reply_text("❌ Invalid format."); return
        await add_model_credits(target_id, info["table"], amount)
        await update.message.reply_text(f"✅ Added <b>{amount}</b> {info['label']} credits to <code>{target_id}</code>.", parse_mode="HTML")
    elif update.message.reply_to_message:
        try: amount = int(ctx.args[0])
        except: await update.message.reply_text("❌ Invalid amount."); return
        target = update.message.reply_to_message.from_user
        await add_model_credits(target.id, info["table"], amount)
        await update.message.reply_text(f"✅ Added <b>{amount}</b> {info['label']} credits to {mention(target)}.", parse_mode="HTML")
    else:
        await update.message.reply_text("Reply to a user or provide user_id.")

async def cmd_addcredits2(update, ctx): await _addcredits_model(update, ctx, "img2")
async def cmd_addcredits3(update, ctx): await _addcredits_model(update, ctx, "img3")
async def cmd_addcredits4(update, ctx): await _addcredits_model(update, ctx, "img4")
async def cmd_addcredits5(update, ctx): await _addcredits_model(update, ctx, "img5")
async def cmd_addcreditspro(update, ctx): await _addcredits_model(update, ctx, "imgpro")


async def _do_img_gen(update: Update, u, prompt: str, style: str):
    """Core image generation logic — shared by /img and /img_<style> commands."""
    is_owner = (u.id == OWNER_ID)
    if not is_owner:
        credits = await get_img_credits(u.id)
        if credits <= 0:
            await update.message.reply_text(
                f"❌ <b>No image credits left!</b>\n\n"
                f"📸 Daily free: {IMG_DAILY_FREE}/day (resets midnight)\n"
                f"🛒 Buy more from /shop\n"
                f"👑 Ask owner for credits via /addcredits",
                parse_mode="HTML"
            ); return

    if not prompt:
        await update.message.reply_text("❌ Prompt can't be empty!"); return

    style_display = style.replace("_", " ").title()
    username_str = f"@{u.username}" if u.username else (u.first_name or "User")

    wait_msg = await update.message.reply_text(
        f"✨ <b>Generating Your Image...</b>\n"
        f"⚜️─────────────────────⚜️\n"
        f"✦ 𝗠𝗼𝗱𝗲𝗹  │ <code>/img</code>\n"
        f"✦ 𝗣𝗿𝗼𝗺𝗽𝘁 │ <code>{prompt[:50]}{'...' if len(prompt)>50 else ''}</code>\n"
        f"✦ 𝗧𝗶𝗺𝗲   │ 3–10s\n"
        f"❖ 𝗥𝗲𝗾𝘂𝗲𝘀𝘁𝗲𝗱 𝗯𝘆 : {username_str}\n"
        f"⚜️─────────────────────⚜️\n"
        f"<i>🖌Crafting your exclusive creation...</i>",
        parse_mode="HTML"
    )

    start_time = time.time()
    try:
        import aiohttp, urllib.parse, io
        clean_prompt = prompt.replace(",", " ").replace("  ", " ").strip()
        enc_prompt = urllib.parse.quote_plus(clean_prompt)
        url = f"https://zade-txt2img-api.vercel.app/text2img?prompt={enc_prompt}&model=flux&style={style}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as r:
                content_type = r.headers.get("Content-Type", "")
                raw = await r.read()

        # Check if API returned error (JSON/text) instead of image
        if "image" not in content_type:
            try:
                err_json = json.loads(raw.decode("utf-8", errors="replace"))
                err_msg = err_json.get("error") or err_json.get("message") or str(err_json)[:200]
            except Exception:
                err_msg = raw.decode("utf-8", errors="replace")[:200]
            try: await wait_msg.delete()
            except: pass
            await update.message.reply_text(
                f"❌ <b>Generation failed</b>\n<code>{err_msg}</code>\n\nTry a different prompt or style!",
                parse_mode="HTML"
            ); return

        # Guard: bytes that look like text/JSON
        if raw[:1] in (b'{', b'[', b'E', b'I') and len(raw) < 500:
            err_msg = raw.decode("utf-8", errors="replace")[:200]
            try: await wait_msg.delete()
            except: pass
            await update.message.reply_text(
                f"❌ <b>Generation failed:</b> <code>{err_msg}</code>",
                parse_mode="HTML"
            ); return

        time_taken = int(time.time() - start_time)

        if not is_owner:
            await deduct_img_credit(u.id)
            credits_left = await get_img_credits(u.id)
            credits_line = f"📸 Credits Left • <b>{credits_left}</b> remaining"
        else:
            credits_line = "👑 Owner Access • Unlimited"

        username_str = f"@{u.username}" if u.username else (u.first_name or "User")

        caption = (
            f"✨ <b>Image Generated Successfully</b>\n"
            f"╭━━━━━━━━━━━━━━━━━━╮\n"
            f"│ 👤 User » {username_str}\n"
            f"│ 🆔 ID » <code>{u.id}</code>\n"
            f"│ 🎭 Style » {style_display}\n"
            f"│ 📝 Prompt » {prompt[:60]}{'...' if len(prompt) > 60 else ''}\n"
            f"│ ⚡ Generated In » {time_taken}s\n"
            f"╰━━━━━━━━━━━━━━━━━━╯\n"
            f"{credits_line}"
        )

        try: await wait_msg.delete()
        except: pass
        await update.message.reply_photo(
            photo=io.BytesIO(raw),
            caption=caption,
            parse_mode="HTML"
        )

    except asyncio.TimeoutError:
        try: await wait_msg.delete()
        except: pass
        await update.message.reply_text("❌ Timed out. API slow, try again!")
    except Exception as e:
        try: await wait_msg.delete()
        except: pass
        await update.message.reply_text(f"❌ Image generation failed: {e}")


async def cmd_img(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if not is_group(update):
        await update.message.reply_text("❌ /img works in groups only!"); return

    if not ctx.args:
        await update.message.reply_text(
            f"🎨 <b>AI Image Generator</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"<b>Commands:</b>\n"
            f"<code>/img</code>  — Flux styles (5 tokens/day)\n"
            f"<code>/img2</code> — GPT Image 2 (2 tokens/day)\n"
            f"<code>/img3</code> — Nano Banana 2 (2 tokens/day)\n"
            f"<code>/img4</code> — Flux Dev (2 tokens/day)\n"
            f"<code>/img5</code> — Seedream V4 (2 tokens/day)\n"
            f"<code>/imgpro</code> — GPT IMAGE PRO (2 tokens/day, 60s cooldown)\n\n"
            f"<b>Usage:</b>\n"
            f"<code>/img a lion in the forest</code>\n"
            f"<code>/img2 a futuristic city</code>\n"
            f"<code>/img_manga a samurai warrior</code>\n\n"
            f"⚠️ /img2–/img5 tokens NOT available in /shop\n"
            f"📋 Use /styles to see all {len(IMG_STYLES)} styles for /img",
            parse_mode="HTML"
        ); return

    prompt = " ".join(ctx.args).strip()
    await _do_img_gen(update, u, prompt, "all")


async def cmd_img_style(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handler for /img_<style> commands — e.g. /img_manga, /img_pixel_art"""
    u = update.effective_user
    if not is_group(update):
        await update.message.reply_text("❌ /img_* works in groups only!"); return

    # Extract style from command text e.g. /img_manga → manga
    cmd_text = update.message.text.split()[0].lstrip("/").split("@")[0]  # e.g. "img_manga"
    style = cmd_text[4:]  # strip "img_"

    if style not in IMG_STYLES:
        await update.message.reply_text(
            f"❌ Unknown style <code>{style}</code>.\nUse /styles to see all available styles.",
            parse_mode="HTML"
        ); return

    if not ctx.args:
        await update.message.reply_text(
            f"🎨 <b>Style: {style}</b>\n\nUsage: <code>/{cmd_text} your prompt here</code>",
            parse_mode="HTML"
        ); return

    prompt = " ".join(ctx.args).strip()
    await _do_img_gen(update, u, prompt, style)

async def cmd_styles(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Show all available image styles."""
    cols = []
    for i in range(0, len(IMG_STYLES), 3):
        row = " · ".join(f"<code>{s}</code>" for s in IMG_STYLES[i:i+3])
        cols.append(row)
    await update.message.reply_text(
        f"🎨 <b>All Image Styles ({len(IMG_STYLES)} total)</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        + "\n".join(cols) +
        f"\n\n<b>Usage:</b> <code>/img_manga your prompt</code> · <code>/img_pixel_art a castle</code>",
        parse_mode="HTML"
    )

async def cmd_addcredits(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Owner gives image credits to a user. /addcredits <amount> (reply) or /addcredits <userid> <amount>"""
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Owner only."); return
    if not ctx.args:
        await update.message.reply_text("Usage:\n/addcredits <amount> (reply to user)\n/addcredits <user_id> <amount>"); return

    if len(ctx.args) >= 2 and ctx.args[0].lstrip('-').isdigit() and len(ctx.args[0]) >= 5:
        try:
            target_id = int(ctx.args[0])
            amount    = int(ctx.args[1])
        except:
            await update.message.reply_text("❌ Invalid format."); return
        await add_img_credits(target_id, amount)
        await update.message.reply_text(
            f"✅ Added <b>{amount} image credits</b> to user <code>{target_id}</code>.",
            parse_mode="HTML"
        )
    elif update.message.reply_to_message:
        try: amount = int(ctx.args[0])
        except: await update.message.reply_text("❌ Invalid amount."); return
        target = update.message.reply_to_message.from_user
        await add_img_credits(target.id, amount)
        await update.message.reply_text(
            f"✅ Added <b>{amount} image credits</b> to {mention(target)}.",
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text("Usage:\n/addcredits <amount> (reply to user)\n/addcredits <user_id> <amount>")

async def cmd_imgcredits(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if u.id == OWNER_ID:
        await update.message.reply_text("👑 You're the owner — unlimited image generation!"); return
    credits = await get_img_credits(u.id)
    await update.message.reply_text(
        f"🎨 <b>Image Credits</b>\n\n"
        f"📸 Credits available: <b>{credits}</b>\n"
        f"🔄 Daily free: <b>{IMG_DAILY_FREE}/day</b> (resets at midnight)\n"
        f"🛒 Buy more from /shop\n\n"
        f"Extra purchased credits carry over to next day!",
        parse_mode="HTML"
    )

# ══════════════════════════════════════════════════════════════════
#  BROADCAST (owner)
# ══════════════════════════════════════════════════════════════════
async def cmd_broadcast(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Owner only."); return
    if not ctx.args:
        await update.message.reply_text("Usage: /broadcast <message>"); return
    msg = " ".join(ctx.args)
    async with aiosqlite.connect(DB_PATH) as d:
        async with d.execute("SELECT user_id FROM users WHERE started_bot=1") as c:
            uids = [r[0] for r in await c.fetchall()]
    ok, fail = 0, 0
    for uid in uids:
        try:
            await ctx.bot.send_message(
                uid,
                f"╔══════════════════════╗\n"
                f"║  📢  <b>ANNOUNCEMENT</b>  ║\n"
                f"╚══════════════════════╝\n\n"
                f"{msg}\n\n"
                f"  — <i>Zade Bot</i>",
                parse_mode="HTML"
            )
            ok += 1
        except:
            fail += 1
        await asyncio.sleep(0.05)
    await update.message.reply_text(f"✅ Broadcast sent!\n\n✅ Success: {ok}\n❌ Failed: {fail}")

# ══════════════════════════════════════════════════════════════════
#  NEW MEMBER HANDLER
# ══════════════════════════════════════════════════════════════════
async def handle_new_member(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        if member.is_bot:
            continue
        await set_group_join(member.id, update.effective_chat.id)
        user = await get_user(member.id, member.username, member.first_name)
        if not user["started_bot"]:
            await update.message.reply_text(
                f"👋 Welcome {mention(member)}!\n\n"
                f"To use <b>{BOT_NAME} Bot</b>, please start me in private first:\n"
                f"👉 @{ctx.bot.username}\n\n"
                f"Then use <code>/daily</code> to claim your starting funds!",
                parse_mode="HTML"
            )

# ══════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════
async def post_init(app):
    await init_db()

async def cmd_set_account(update, ctx):
    global BING_ACCOUNT
    u = update.effective_user
    if u.id != OWNER_ID:
        await update.message.reply_text("❌ Owner only."); return
    if not ctx.args or ctx.args[0] not in ("0", "1", "2"):
        await update.message.reply_text(
            "⚙️ <b>Bing Account Selector</b>\n\n"
            "/set 0 — 🔄 Auto-rotate (6h)\n"
            "/set 1 — 👤 Account 1 (fixed)\n"
            "/set 2 — 👤 Account 2 (fixed)\n\n"
            f"Current: <b>{'Auto-rotate' if BING_ACCOUNT == 0 else f'Account {BING_ACCOUNT}'}</b>",
            parse_mode="HTML"
        ); return
    BING_ACCOUNT = int(ctx.args[0])
    labels = {0: "🔄 Auto-rotate (6h)", 1: "👤 Account 1", 2: "👤 Account 2"}
    await update.message.reply_text(
        f"✅ <b>Bing account set to: {labels[BING_ACCOUNT]}</b>\n"
        f"All /img2 /img3 /img4 will use this now.",
        parse_mode="HTML"
    )


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

    handlers = [
        ("start",          cmd_start),
        ("help",           cmd_help),
        # Economy
        ("daily",          cmd_daily),
        ("bal",            cmd_bal),
        ("give",           cmd_give),
        ("rob",            cmd_rob),
        ("kill",           cmd_kill),
        ("revive",         cmd_revive),
        ("protect",        cmd_protect),
        ("check",          cmd_check),
        ("lb",             cmd_lb),
        ("toprich",        cmd_toprich),
        ("topkill",        cmd_topkill),
        ("pay",            cmd_pay),
        ("addbal",         cmd_addbal),
        ("dedbal",         cmd_dedbal),
        ("taxbal",         cmd_taxbal),
        ("withdrawtax",    cmd_withdrawtax),
        ("xpshop",         cmd_xpshop),
        # Shop
        ("shop",           cmd_shop),
        ("inv",            cmd_inv),
        ("use",            cmd_use),
        # Image Gen
        ("img",            cmd_img),
        ("img2",           cmd_img2),
        ("img3",           cmd_img3),
        ("img4",           cmd_img4),
        ("img5",           cmd_img5),
        ("img6",           cmd_img6),
        ("imgpro",         cmd_imgpro),
        ("styles",         cmd_styles),
        ("imgcredits",     cmd_imgcredits),
        ("addcredits",     cmd_addcredits),
        ("addcredits2",    cmd_addcredits2),
        ("addcredits3",    cmd_addcredits3),
        ("addcredits4",    cmd_addcredits4),
        ("addcredits5",    cmd_addcredits5),
        ("addcredits6",    cmd_addcredits6),
        ("addcreditspro",  cmd_addcreditspro),
        ("slap",           cmd_slap),
        ("hug",            cmd_hug),
        ("kiss",           cmd_kiss),
        ("punch",          cmd_punch),
        ("bite",           cmd_bite),
        ("love",           cmd_love),
        ("look",           cmd_look),
        ("crush",          cmd_crush),
        ("murder",         cmd_murder),
        ("pat",            cmd_pat),
        ("poke",           cmd_poke),
        ("tickle",         cmd_tickle),
        ("wave",           cmd_wave),
        ("wink",           cmd_wink),
        ("cry",            cmd_cry),
        ("laugh",          cmd_laugh),
        ("dance",          cmd_dance),
        ("cuddle",         cmd_cuddle),
        ("highfive",       cmd_highfive),
        ("throw",          cmd_throw),
        # Coupon
        ("create_coupon",  cmd_create_coupon),
        ("coupon",         cmd_coupon),
        ("del_coupon",     cmd_del_coupon),
        ("status",         cmd_status),
        ("claim",          cmd_claim),
        # Utility
        ("tr",             cmd_tr),
        ("tts",            cmd_tts),
        ("voices",         cmd_voices),
        ("set_tts",        cmd_set_tts),
        ("admins",         cmd_admins),
        ("owner",          cmd_owner),
        ("details",        cmd_details),
        ("setsticker",     cmd_setsticker),
        # Owner
        ("set",            cmd_set_account),
        ("panel",          cmd_panel),
        ("genid",          cmd_genid),
        ("clone",          cmd_clone),
        ("broadcast",      cmd_broadcast),
    ]

    for cmd, fn in handlers:
        app.add_handler(CommandHandler(cmd, fn))

    # Register /img_<style> commands for all 31 styles
    for _style in IMG_STYLES:
        app.add_handler(CommandHandler(f"img_{_style}", cmd_img_style))

    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_new_member))
    # Clone DM flow MUST be registered before sticker trigger (higher priority)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, cmd_clone_msg))
    # Sticker trigger — groups only so it never blocks DM clone flow
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS, handle_sticker_trigger))

    print(f"⚡ {BOT_NAME} Bot running!")
    app.run_polling()

if __name__ == "__main__":
    main()
