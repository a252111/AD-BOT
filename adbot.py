from highrise import BaseBot, User, Position
from highrise.__main__ import BotDefinition
from asyncio import sleep, create_task, CancelledError
from urllib.parse import urlparse, parse_qs
import asyncio
import os
import re
import json
import logging
from datetime import datetime, timedelta
import random
import aiohttp

# إعداد التسجيل (Logging)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# الإعدادات الافتراضية
CONFIG_FILE = "bot_config.json"
DEFAULT_CONFIG = {
    "host_usernames": ["rqtm"],
    "admin_usernames": ["rqtm"],
    "vip_usernames": [],
    "banned_users": [],
    "teleport_locations": {
        "vip": {"x": 14.5, "y": 16.75, "z": 5.5},
        "vip1": {"x": 14.5, "y": 16.75, "z": 5.5},
        "dj": {"x": 9.5, "y": 10.75, "z": 10.5}
    },
    "start_position": dict(START_POSITION),
    "language": "ar",
    "welcome_message": "✨ أهلاً وسهلاً {username} ❤️ نورتنا!\n🕺 استخدم الأرقام (1-256) أو أسماء الحركات للرقص!\n👑 تم تطوير البوت بواسطة @RQTM 😉\n 🚀",
    "announcement_interval": 300,
    "announcement_message": "لاستئجار البوت، راسلوا @RQTM!"
}

# الإعدادات كلها موجودة في ملف settings.py
from settings import (
    QUIZ_TIMEOUT,
    QUIZ_SCORES_FILE,
    QUIZ_COLOR_QUESTION,
    QUIZ_COLOR_ANSWER,
    QUIZ_EMOTE_THINK,
    QUIZ_EMOTE_HAPPY,
    QUIZ_EMOTE_SAD,
    QUIZ_INTROS,
    QUIZ_CORRECT,
    QUIZ_TIMEOUT_MSG,
    QUIZ_QUESTIONS,
    QUIZ_DEFAULT_ROUNDS,
    START_POSITION,
    ROOM_ID,
    API_TOKEN,
)

class AdvancedBot(BaseBot):
    def __init__(self):
        super().__init__()
        self.load_config()
        self.active_users = {}
        self.user_dances = {}
        self.dance_tasks = {}
        self.user_positions = {}
        self.user_scores = {}
        self.user_id = None
        self.announcement_task = None
        self.score_update_task = None
        self.loopchat_task = None
        self.frozen_users = {}
        self.party_dances = {}
        self.quiz_task = None
        self.quiz_current = None
        self.quiz_session = {}
        self.quiz_think_task = None
        self.bot_emote_name = None
        self.quiz_scores = {}
        self.load_quiz_scores()
        self.commands = {
            "!help": self.cmd_help,
            "!spam": self.cmd_spam,
            "!tele": self.cmd_tele,
            "!heart": self.cmd_heart,
            "!clap": self.cmd_clap,
            "!wink": self.cmd_wink,
            "!wave": self.cmd_wave,
            "!thumbs": self.cmd_thumbs,
            "!wallet": self.cmd_wallet,
            "!set": self.cmd_set,
            "!setstart": self.cmd_setstart,
            "!tip": self.cmd_tip,
            "!vip": self.cmd_vip,
            "!vip1": self.cmd_vip1,
            "!dj": self.cmd_dj,
            "!down": self.cmd_down,
            "!ban": self.cmd_ban,
            "!unban": self.cmd_unban,
            "!dancechain": self.cmd_dancechain,
            "!addtele": self.cmd_addtele,
            "!deltele": self.cmd_deltele,
            "!item set": self.cmd_set_item,
            "!welcome": self.cmd_welcome,
            "!addadmin": self.cmd_addadmin,
            "!removeadmin": self.cmd_removeadmin,
            "!addhost": self.cmd_addhost,
            "!removehost": self.cmd_removehost,
            "!listadd": self.cmd_listadd,
            "!freeze": self.cmd_freeze,
            "!unfreeze": self.cmd_unfreeze,
            "!party": self.cmd_party,
            "!partys": self.cmd_partys,
            "!emotebot": self.cmd_emotebot,
            "!emote": self.cmd_emote_link,
            "!loopchat": self.cmd_loopchat,
            "!quiz": self.cmd_quiz,
            "!مسابقة": self.cmd_quiz,
            "!quizstop": self.cmd_quizstop,
            "!ايقاف_المسابقة": self.cmd_quizstop,
            "!top": self.cmd_top,
            "!المتصدرين": self.cmd_top
        }
        self.emotes = {
            "1": "idle_zombie",
            "2": "idle_layingdown2",
            "3": "idle_layingdown",
            "4": "idle-sleep",
            "5": "idle-sad",
            "6": "idle-posh",
            "7": "idle-loop-tired",
            "8": "idle-loop-tapdance",
            "9": "idle-loop-sitfloor",
            "10": "idle-loop-shy",
            "11": "idle-loop-sad",
            "12": "idle-loop-happy",
            "13": "idle-loop-annoyed",
            "14": "idle-loop-aerobics",
            "15": "idle-lookup",
            "16": "idle-hero",
            "17": "idle-floorsleeping",
            "18": "idle-enthusiastic",
            "19": "idle-dance-swinging",
            "20": "idle-dance-headbobbing",
            "21": "idle-angry",
            "22": "emote-yes",
            "23": "emote-wings",
            "24": "emote-wave",
            "25": "emote-tired",
            "26": "emote-think",
            "27": "emote-theatrical",
            "28": "emote-tapdance",
            "29": "emote-superrun",
            "30": "emote-superpunch",
            "31": "emote-sumo",
            "32": "emote-suckthumb",
            "33": "emote-splitsdrop",
            "34": "emote-snowball",
            "35": "emote-snowangel",
            "36": "emote-shy",
            "37": "emote-secrethandshake",
            "38": "emote-sad",
            "39": "emote-ropepull",
            "40": "emote-roll",
            "41": "emote-rofl",
            "42": "emote-robot",
            "43": "emote-rainbow",
            "44": "emote-proposing",
            "45": "emote-peekaboo",
            "46": "emote-peace",
            "47": "emote-panic",
            "48": "emote-no",
            "49": "emote-ninjarun",
            "50": "emote-nightfever",
            "51": "emote-monster_fail",
            "52": "emote-model",
            "53": "emote-lust",
            "54": "emote-levelup",
            "55": "emote-laughing2",
            "56": "emote-laughing",
            "57": "emote-kiss",
            "58": "emote-kicking",
            "59": "emote-jumpb",
            "60": "emote-gravity",
            "61": "emote-judochop",
            "62": "emote-jetpack",
            "63": "emote-hugyourself",
            "64": "emote-hot",
            "65": "emote-hero",
            "66": "emote-hello",
            "67": "emote-headball",
            "68": "emote-harlemshake",
            "69": "emote-happy",
            "70": "emote-handstand",
            "71": "emote-greedy",
            "72": "emote-graceful",
            "73": "emote-gordonshuffle",
            "74": "emote-ghost-idle",
            "75": "emote-gangnam",
            "76": "emote-frollicking",
            "77": "emote-fainting",
            "78": "emote-fail2",
            "79": "emote-fail1",
            "80": "emote-exasperatedb",
            "81": "emote-exasperated",
            "82": "emote-elbowbump",
            "83": "emote-disco",
            "84": "emote-disappear",
            "85": "emote-deathdrop",
            "86": "emote-death2",
            "87": "emote-death",
            "88": "emote-dab",
            "89": "emote-curtsy",
            "90": "emote-confused",
            "91": "emote-cold",
            "92": "emote-charging",
            "93": "emote-bunnyhop",
            "94": "emote-bow",
            "95": "emote-boo",
            "96": "emote-baseball",
            "97": "emote-apart",
            "98": "emoji-thumbsup",
            "99": "emoji-there",
            "100": "emoji-sneeze",
            "101": "emoji-smirking",
            "102": "emoji-sick",
            "103": "emoji-scared",
            "104": "emoji-punch",
            "105": "emoji-pray",
            "106": "emoji-poop",
            "107": "emoji-naughty",
            "108": "emoji-mind-blown",
            "109": "emoji-lying",
            "110": "emoji-halo",
            "111": "emoji-hadoken",
            "112": "emoji-give-up",
            "113": "emoji-gagging",
            "114": "emoji-flex",
            "115": "emoji-dizzy",
            "116": "emoji-cursing",
            "117": "emoji-crying",
            "118": "emoji-clapping",
            "119": "emoji-celebrate",
            "120": "emoji-arrogance",
            "121": "emoji-angry",
            "122": "dance-voguehands",
            "123": "dance-tiktok8",
            "124": "dance-tiktok2",
            "125": "dance-spiritual",
            "126": "dance-smoothwalk",
            "127": "dance-singleladies",
            "128": "dance-shoppingcart",
            "129": "dance-russian",
            "130": "dance-robotic",
            "131": "dance-pennywise",
            "132": "dance-orangejustice",
            "133": "dance-metal",
            "134": "dance-martial-artist",
            "135": "dance-macarena",
            "136": "dance-handsup",
            "137": "dance-duckwalk",
            "138": "dance-breakdance",
            "139": "dance-blackpink",
            "140": "dance-aerobics",
            "141": "emote-hyped",
            "142": "dance-jinglebell",
            "143": "idle-nervous",
            "144": "idle-toilet",
            "145": "emote-attention",
            "146": "sit-open",
            "147": "emote-astronaut",
            "148": "dance-zombie",
            "149": "emoji-ghost",
            "150": "emote-hearteyes",
            "151": "emote-swordfight",
            "152": "emote-timejump",
            "153": "emote-snake",
            "154": "emote-heartfingers",
            "155": "emote-heartshape",
            "156": "emote-hug",
            "157": "emote-lagughing",
            "158": "emoji-eyeroll",
            "159": "emote-embarrassed",
            "160": "emote-float",
            "161": "emote-telekinesis",
            "162": "dance-sexy",
            "163": "emote-puppet",
            "164": "idle-fighter",
            "165": "dance-pinguin",
            "166": "dance-creepypuppet",
            "167": "emote-sleigh",
            "168": "emote-maniac",
            "169": "emote-energyball",
            "170": "idle_singing",
            "171": "emote-frog",
            "172": "emote-superpose",
            "173": "emote-cute",
            "174": "dance-tiktok9",
            "175": "dance-weird",
            "176": "dance-tiktok10",
            "177": "emote-pose7",
            "178": "emote-pose8",
            "179": "idle-dance-casual",
            "180": "emote-pose1",
            "181": "emote-pose3",
            "182": "emote-pose5",
            "183": "emote-cutey",
            "184": "emote-punkguitar",
            "185": "emote-zombierun",
            "186": "dance-jinglebell",
            "187": "emote-gravity",
            "188": "dance-icecream",
            "189": "dance-wrong",
            "190": "idle-uwu",
            "191": "idle-dance-tiktok4",
            "192": "emote-shy2",
            "193": "dance-anime",
            "194": "dance-kawai",
            "195": "idle-wild",
            "196": "emote-iceskating",
            "197": "emote-pose6",
            "198": "emote-celebrationstep",
            "199": "emote-creepycute",
            "200": "emote-frustrated",
            "201": "emote-pose10",
            "202": "sit-relaxed",
            "203": "emote-stargaze",
            "204": "emote-slap",
            "205": "emote-boxer",
            "206": "emote-headblowup",
            "207": "emote-kawaiigogo",
            "208": "emote-repose",
            "209": "idle-dance-tiktok7",
            "210": "emote-shrink",
            "211": "emote-pose9",
            "212": "emote-teleporting",
            "213": "dance-touch",
            "214": "idle-guitar",
            "215": "emote-gift",
            "216": "dance-employee",
            "217": "emote-kissing",
            "218": "dance-tiktok11",
            "219": "emote-cutesalute",
            "220": "emote-salute",
            "221": "idle-floorsleeping2",
            "222": "dance-floss",
            "223": "dance-tiktok11",
            "224": "dance-tiktok12",
            "225": "dance-tiktok13",
            "226": "emote-spiderman",
            "227": "dance-breakdance",
            "228": "dance-twerk",
            "229": "idle-space",
            "230": "sit-idle-cute",
            "231": "dance-true-heart",
            "232": "dance-griddy",
            "233": "dance-ballet",
            "234": "dance-freshprince",
            "235": "emote-idle-daydreaming",
            "236": "emote-graceful",
            "237": "dance-spiritual",
            "238": "dance-popularvibe",
            "239": "sit-idle-laidBack",
            "240": "dance-martial-artist",
            "241": "dance-swagbounce",
            "242": "emote-lust",
            "243": "dance-woah",
            "244": "dance-mine",
            "245": "emote-blowkisses",
            "246": "emote-hero",
            "247": "dance-shuffle",
            "248": "emote-knocking-screen",
            "249": "emote-alice-shrink",
            "250": "emote-threadexchange-star",
            "251": "emote-inside-out",
            "252": "emote-collab-photo-right",
            "253": "emote-afk-idle",
            "254": "emote-meditate-idle",
            "255": "emote-sixseve-noimg",
            "256": "emote-sixseven",
            "١": "idle_zombie",
            "٢": "idle_layingdown2",
            "٣": "idle_layingdown",
            "٤": "idle-sleep",
            "٥": "idle-sad",
            "٦": "idle-posh",
            "٧": "idle-loop-tired",
            "٨": "idle-loop-tapdance",
            "٩": "idle-loop-sitfloor",
            "١٠": "idle-loop-shy",
            "١١": "idle-loop-sad",
            "١٢": "idle-loop-happy",
            "١٣": "idle-loop-annoyed",
            "١٤": "idle-loop-aerobics",
            "١٥": "idle-lookup",
            "١٦": "idle-hero",
            "١٧": "idle-floorsleeping",
            "١٨": "idle-enthusiastic",
            "١٩": "idle-dance-swinging",
            "٢٠": "idle-dance-headbobbing",
            "٢١": "idle-angry",
            "٢٢": "emote-yes",
            "٢٣": "emote-wings",
            "٢٤": "emote-wave",
            "٢٥": "emote-tired",
            "٢٦": "emote-think",
            "٢٧": "emote-theatrical",
            "٢٨": "emote-tapdance",
            "٢٩": "emote-superrun",
            "٣٠": "emote-superpunch",
            "٣١": "emote-sumo",
            "٣٢": "emote-suckthumb",
            "٣٣": "emote-splitsdrop",
            "٣٤": "emote-snowball",
            "٣٥": "emote-snowangel",
            "٣٦": "emote-shy",
            "٣٧": "emote-secrethandshake",
            "٣٨": "emote-sad",
            "٣٩": "emote-ropepull",
            "٤٠": "emote-roll",
            "٤١": "emote-rofl",
            "٤٢": "emote-robot",
            "٤٣": "emote-rainbow",
            "٤٤": "emote-proposing",
            "٤٥": "emote-peekaboo",
            "٤٦": "emote-peace",
            "٤٧": "emote-panic",
            "٤٨": "emote-no",
            "٤٩": "emote-ninjarun",
            "٥٠": "emote-nightfever",
            "٥١": "emote-monster_fail",
            "٥٢": "emote-model",
            "٥٣": "emote-lust",
            "٥٤": "emote-levelup",
            "٥٥": "emote-laughing2",
            "٥٦": "emote-laughing",
            "٥٧": "emote-kiss",
            "٥٨": "emote-kicking",
            "٥٩": "emote-jumpb",
            "٦٠": "emote-gravity",
            "٦١": "emote-judochop",
            "٦٢": "emote-jetpack",
            "٦٣": "emote-hugyourself",
            "٦٤": "emote-hot",
            "٦٥": "emote-hero",
            "٦٦": "emote-hello",
            "٦٧": "emote-headball",
            "٦٨": "emote-harlemshake",
            "٦٩": "emote-happy",
            "٧٠": "emote-handstand",
            "٧١": "emote-greedy",
            "٧٢": "emote-graceful",
            "٧٣": "emote-gordonshuffle",
            "٧٤": "emote-ghost-idle",
            "٧٥": "emote-gangnam",
            "٧٦": "emote-frollicking",
            "٧٧": "emote-fainting",
            "٧٨": "emote-fail2",
            "٧٩": "emote-fail1",
            "٨٠": "emote-exasperatedb",
            "٨١": "emote-exasperated",
            "٨٢": "emote-elbowbump",
            "٨٣": "emote-disco",
            "٨٤": "emote-disappear",
            "٨٥": "emote-deathdrop",
            "٨٦": "emote-death2",
            "٨٧": "emote-death",
            "٨٨": "emote-dab",
            "٨٩": "emote-curtsy",
            "٩٠": "emote-confused",
            "٩١": "emote-cold",
            "٩٢": "emote-charging",
            "٩٣": "emote-bunnyhop",
            "٩٤": "emote-bow",
            "٩٥": "emote-boo",
            "٩٦": "emote-baseball",
            "٩٧": "emote-apart",
            "٩٨": "emoji-thumbsup",
            "٩٩": "emoji-there",
            "١٠٠": "emoji-sneeze",
            "١٠١": "emoji-smirking",
            "١٠٢": "emoji-sick",
            "١٠٣": "emoji-scared",
            "١٠٤": "emoji-punch",
            "١٠٥": "emoji-pray",
            "١٠٦": "emoji-poop",
            "١٠٧": "emoji-naughty",
            "١٠٨": "emoji-mind-blown",
            "١٠٩": "emoji-lying",
            "١١٠": "emoji-halo",
            "١١١": "emoji-hadoken",
            "١١٢": "emoji-give-up",
            "١١٣": "emoji-gagging",
            "١١٤": "emoji-flex",
            "١١٥": "emoji-dizzy",
            "١١٦": "emoji-cursing",
            "١١٧": "emoji-crying",
            "١١٨": "emoji-clapping",
            "١١٩": "emoji-celebrate",
            "١٢٠": "emoji-arrogance",
            "١٢١": "emoji-angry",
            "١٢٢": "dance-voguehands",
            "١٢٣": "dance-tiktok8",
            "١٢٤": "dance-tiktok2",
            "١٢٥": "dance-spiritual",
            "١٢٦": "dance-smoothwalk",
            "١٢٧": "dance-singleladies",
            "١٢٨": "dance-shoppingcart",
            "١٢٩": "dance-russian",
            "١٣٠": "dance-robotic",
            "١٣١": "dance-pennywise",
            "١٣٢": "dance-orangejustice",
            "١٣٣": "dance-metal",
            "١٣٤": "dance-martial-artist",
            "١٣٥": "dance-macarena",
            "١٣٦": "dance-handsup",
            "١٣٧": "dance-duckwalk",
            "١٣٨": "dance-breakdance",
            "١٣٩": "dance-blackpink",
            "١٤٠": "dance-aerobics",
            "١٤١": "emote-hyped",
            "١٤٢": "dance-jinglebell",
            "١٤٣": "idle-nervous",
            "١٤٤": "idle-toilet",
            "١٤٥": "emote-attention",
            "١٤٦": "sit-open",
            "١٤٧": "emote-astronaut",
            "١٤٨": "dance-zombie",
            "١٤٩": "emoji-ghost",
            "١٥٠": "emote-hearteyes",
            "١٥١": "emote-swordfight",
            "١٥٢": "emote-timejump",
            "١٥٣": "emote-snake",
            "١٥٤": "emote-heartfingers",
            "١٥٥": "emote-heartshape",
            "١٥٦": "emote-hug",
            "١٥٧": "emote-lagughing",
            "١٥٨": "emoji-eyeroll",
            "١٥٩": "emote-embarrassed",
            "١٦٠": "emote-float",
            "١٦١": "emote-telekinesis",
            "١٦٢": "dance-sexy",
            "١٦٣": "emote-puppet",
            "١٦٤": "idle-fighter",
            "١٦٥": "dance-pinguin",
            "١٦٦": "dance-creepypuppet",
            "١٦٧": "emote-sleigh",
            "١٦٨": "emote-maniac",
            "١٦٩": "emote-energyball",
            "١٧٠": "idle_singing",
            "١٧١": "emote-frog",
            "١٧٢": "emote-superpose",
            "١٧٣": "emote-cute",
            "١٧٤": "dance-tiktok9",
            "١٧٥": "dance-weird",
            "١٧٦": "dance-tiktok10",
            "١٧٧": "emote-pose7",
            "١٧٨": "emote-pose8",
            "١٧٩": "idle-dance-casual",
            "١٨٠": "emote-pose1",
            "١٨١": "emote-pose3",
            "١٨٢": "emote-pose5",
            "١٨٣": "emote-cutey",
            "١٨٤": "emote-punkguitar",
            "١٨٥": "emote-zombierun",
            "١٨٦": "dance-jinglebell",
            "١٨٧": "emote-gravity",
            "١٨٨": "dance-icecream",
            "١٨٩": "dance-wrong",
            "١٩٠": "idle-uwu",
            "١٩١": "idle-dance-tiktok4",
            "١٩٢": "emote-shy2",
            "١٩٣": "dance-anime",
            "١٩٤": "dance-kawai",
            "١٩٥": "idle-wild",
            "١٩٦": "emote-iceskating",
            "١٩٧": "emote-pose6",
            "١٩٨": "emote-celebrationstep",
            "١٩٩": "emote-creepycute",
            "٢٠٠": "emote-frustrated",
            "٢٠١": "emote-pose10",
            "٢٠٢": "sit-relaxed",
            "٢٠٣": "emote-stargaze",
            "٢٠٤": "emote-slap",
            "٢٠٥": "emote-boxer",
            "٢٠٦": "emote-headblowup",
            "٢٠٧": "emote-kawaiigogo",
            "٢٠٨": "emote-repose",
            "٢٠٩": "idle-dance-tiktok7",
            "٢١٠": "emote-shrink",
            "٢١١": "emote-pose9",
            "٢١٢": "emote-teleporting",
            "٢١٣": "dance-touch",
            "٢١٤": "idle-guitar",
            "٢١٥": "emote-gift",
            "٢١٦": "dance-employee",
            "٢١٧": "emote-kissing",
            "٢١٨": "dance-tiktok11",
            "٢١٩": "emote-cutesalute",
            "٢٢٠": "emote-salute",
            "٢٢١": "idle-floorsleeping2",
            "٢٢٢": "dance-floss",
            "٢٢٣": "dance-tiktok11",
            "٢٢٤": "dance-tiktok12",
            "٢٢٥": "dance-tiktok13",
            "٢٢٦": "emote-spiderman",
            "٢٢٧": "dance-breakdance",
            "٢٢٨": "dance-twerk",
            "٢٢٩": "idle-space",
            "٢٣٠": "sit-idle-cute",
            "٢٣١": "dance-true-heart",
            "٢٣٢": "dance-griddy",
            "٢٣٣": "dance-ballet",
            "٢٣٤": "dance-freshprince",
            "٢٣٥": "emote-idle-daydreaming",
            "٢٣٦": "emote-graceful",
            "٢٣٧": "dance-spiritual",
            "٢٣٨": "dance-popularvibe",
            "٢٣٩": "sit-idle-laidBack",
            "٢٤٠": "dance-martial-artist",
            "٢٤١": "dance-swagbounce",
            "٢٤٢": "emote-lust",
            "٢٤٣": "dance-woah",
            "٢٤٤": "dance-mine",
            "٢٤٥": "emote-blowkisses",
            "٢٤٦": "emote-hero",
            "٢٤٧": "dance-shuffle",
            "٢٤٨": "emote-knocking-screen",
            "٢٤٩": "emote-alice-shrink",
            "٢٥٠": "emote-threadexchange-star",
            "٢٥١": "emote-inside-out",
            "٢٥٢": "emote-collab-photo-right",
            "٢٥٣": "emote-afk-idle",
            "٢٥٤": "emote-meditate-idle",
            "٢٥٥": "emote-sixseve-noimg",
            "٢٥٦": "emote-sixseven",
            "zombie": "idle_zombie",
            "relaxed": "idle_layingdown2",
            "attentive": "idle_layingdown",
            "sleepy": "idle-sleep",
            "poutyFace": "idle-sad",
            "posh": "idle-posh",
            "tiredloop": "idle-loop-tired",
            "tapLoop": "idle-loop-tapdance",
            "sit": "idle-loop-sitfloor",
            "shy": "idle-loop-shy",
            "bummed": "idle-loop-sad",
            "chillin'": "idle-loop-happy",
            "annoyed": "idle-loop-annoyed",
            "aerobics": "idle-loop-aerobics",
            "ponder": "idle-lookup",
            "heropose": "idle-hero",
            "cozynap": "idle-floorsleeping",
            "enthused": "idle-enthusiastic",
            "boogieswing": "idle-dance-swinging",
            "feelthebeat": "idle-dance-headbobbing",
            "irritated": "idle-angry",
            "yes": "emote-yes",
            "ibelieveIcanfly": "emote-wings",
            "theWave": "emote-wave",
            "tired": "emote-tired",
            "think": "emote-think",
            "theatrical": "emote-theatrical",
            "tapdance": "emote-tapdance",
            "superrun": "emote-superrun",
            "superPunch": "emote-superpunch",
            "sumofight": "emote-sumo",
            "thumbSuck": "emote-suckthumb",
            "splitsdrop": "emote-splitsdrop",
            "snowballFight": "emote-snowball",
            "snowAngel": "emote-snowangel",
            "shyemote": "emote-shy",
            "secrehandshake": "emote-secrethandshake",
            "sad": "emote-sad",
            "ropepull": "emote-ropepull",
            "roll": "emote-roll",
            "rofl": "emote-rofl",
            "robot": "emote-robot",
            "rainbow": "emote-rainbow",
            "proposing": "emote-proposing",
            "peekaboo": "emote-peekaboo",
            "peace": "emote-peace",
            "panic": "emote-panic",
            "no": "emote-no",
            "ninjarun": "emote-ninjarun",
            "nightfever": "emote-nightfever",
            "monsterfail": "emote-monster_fail",
            "model": "emote-model",
            "flirtywave": "emote-lust",
            "levelUp": "emote-levelup",
            "amused": "emote-laughing2",
            "laugh": "emote-laughing",
            "kiss": "emote-kiss",
            "superKick": "emote-kicking",
            "jump": "emote-jumpb",
            "gravity": "emote-gravity",
            "judochop": "emote-judochop",
            "imaginaryjetpack": "emote-jetpack",
            "hugyourself": "emote-hugyourself",
            "sweating": "emote-hot",
            "heroentrance": "emote-hero",
            "hello": "emote-hello",
            "headball": "emote-headball",
            "harlemShake": "emote-harlemshake",
            "happy": "emote-happy",
            "handstand": "emote-handstand",
            "greedyEmote": "emote-greedy",
            "graceful": "emote-graceful",
            "moonwalk": "emote-gordonshuffle",
            "ghostfloat": "emote-ghost-idle",
            "gangnamstyle": "emote-gangnam",
            "frolic": "emote-frollicking",
            "faint": "emote-fainting",
            "clumsy": "emote-fail2",
            "fall": "emote-fail1",
            "facePalm": "emote-exasperatedb",
            "exasperated": "emote-exasperated",
            "elbowBump": "emote-elbowbump",
            "disco": "emote-disco",
            "blastOff": "emote-disappear",
            "faintDrop": "emote-deathdrop",
            "collapse": "emote-death2",
            "revival": "emote-death",
            "dab": "emote-dab",
            "curtsy": "emote-curtsy",
            "confusion": "emote-confused",
            "cold": "emote-cold",
            "charging": "emote-charging",
            "bunnyHop": "emote-bunnyhop",
            "bow": "emote-bow",
            "boo": "emote-boo",
            "homerun": "emote-baseball",
            "fallingapart": "emote-apart",
            "thumbsup": "emoji-thumbsup",
            "point": "emoji-there",
            "sneeze": "emoji-sneeze",
            "smirk": "emoji-smirking",
            "sick": "emoji-sick",
            "gasp": "emoji-scared",
            "punch": "emoji-punch",
            "pray": "emoji-pray",
            "stinky": "emoji-poop",
            "naughty": "emoji-naughty",
            "mindBlown": "emoji-mind-blown",
            "lying": "emoji-lying",
            "levitate": "emoji-halo",
            "fireball Lunge": "emoji-hadoken",
            "giveup": "emoji-give-up",
            "tummy Ache": "emoji-gagging",
            "flex": "emoji-flex",
            "stunned": "emoji-dizzy",
            "cursing Emote": "emoji-cursing",
            "sob": "emoji-crying",
            "clap": "emoji-clapping",
            "raiseTheRoof": "emoji-celebrate",
            "arrogance": "emoji-arrogance",
            "angry": "emoji-angry",
            "VogueHands": "dance-voguehands",
            "SavageDance": "dance-tiktok8",
            "DontStartNow": "dance-tiktok2",
            "YogaFlow": "dance-spiritual",
            "Smoothwalk": "dance-smoothwalk",
            "RingonIt": "dance-singleladies",
            "Let's Go Shopping": "dance-shoppingcart",
            "russian Dance": "dance-russian",
            "tobotic": "dance-robotic",
            "penny's Dance": "dance-pennywise",
            "orange Juice Dance": "dance-orangejustice",
            "rockout": "dance-metal",
            "karate": "dance-martial-artist",
            "macarena": "dance-macarena",
            "handsintheair": "dance-handsup",
            "duckealk": "dance-duckwalk",
            "Breakdance": "dance-breakdance",
            "kpop": "dance-blackpink",
            "PushUps": "dance-aerobics",
            "Hyped": "emote-hyped",
            "Jinglebell": "dance-jinglebell",
            "Nervous": "idle-nervous",
            "Toilet": "idle-toilet",
            "Attention": "emote-attention",
            "laidback": "sit-open",
            "Astronaut": "emote-astronaut",
            "DanceZombie": "dance-zombie",
            "ghost": "emoji-ghost",
            "HeartEyes": "emote-hearteyes",
            "Swordfight": "emote-swordfight",
            "TimeJump": "emote-timejump",
            "Snake": "emote-snake",
            "HeartFingers": "emote-heartfingers",
            "Heart Shape": "emote-heartshape",
            "hug": "emote-hug",
            "Laugh": "emote-lagughing",
            "Eyeroll": "emoji-eyeroll",
            "Embarrassed": "emote-embarrassed",
            "float": "emote-float",
            "Telekinesis": "emote-telekinesis",
            "Sexydance": "dance-sexy",
            "Puppet": "emote-puppet",
            "Fighter idle": "idle-fighter",
            "Penguindance": "dance-pinguin",
            "Creepypuppet": "dance-creepypuppet",
            "Sleigh": "emote-sleigh",
            "Maniac": "emote-maniac",
            "EnergyBall": "emote-energyball",
            "Singing": "idle_singing",
            "Frog": "emote-frog",
            "Superpose": "emote-superpose",
            "Cute": "emote-cute",
            "TikTok9": "dance-tiktok9",
            "Weird": "dance-weird",
            "TikTok10": "dance-tiktok10",
            "pose7": "emote-pose7",
            "pose8": "emote-pose8",
            "casualDance": "idle-dance-casual",
            "pose1": "emote-pose1",
            "pose3": "emote-pose3",
            "pose5": "emote-pose5",
            "Cutey": "emote-cutey",
            "PunkGuitar": "emote-punkguitar",
            "zombieru": "emote-zombierun",
            "fashionista": "dance-jinglebell",
            "icecream": "dance-icecream",
            "wrong": "dance-wrong",
            "uwu": "idle-uwu",
            "TikTok4": "idle-dance-tiktok4",
            "advancedshy": "emote-shy2",
            "anime": "dance-anime",
            "kawaii": "dance-kawai",
            "Scritchy": "idle-wild",
            "iceskating": "emote-iceskating",
            "surpriseBig": "emote-pose6",
            "celebrationStep": "emote-celebrationstep",
            "creepycute": "emote-creepycute",
            "frustrated": "emote-frustrated",
            "pose10": "emote-pose10",
            "relaxedsit": "sit-relaxed",
            "stargazing": "emote-stargaze",
            "slap": "emote-slap",
            "boxer": "emote-boxer",
            "headBlowup": "emote-headblowup",
            "kawaiiGoGo": "emote-kawaiigogo",
            "repose": "emote-repose",
            "tiktok7": "idle-dance-tiktok7",
            "shrink": "emote-shrink",
            "ditzyPose": "emote-pose9",
            "teleporting": "emote-teleporting",
            "touch": "dance-touch",
            "airuitar": "idle-guitar",
            "thisIs For You": "emote-gift",
            "pushit": "dance-employee",
            "sweetSmooch": "emote-kissing",
            "tiktok11": "dance-tiktok11",
            "cutesalute": "emote-cutesalute",
            "relaxing": "idle-floorsleeping2",
            "attention": "emote-salute",
            "floss": "dance-floss",
            "rest": "sit-idle-cute",
            "aliceshrink": "emote-alice-shrink",
            "threadexchangestar": "emote-threadexchange-star",
            "insideout": "emote-inside-out",
            "collabphoto": "emote-collab-photo-right",
            "afk": "emote-afk-idle",
            "meditate": "emote-meditate-idle",
            "sixseven": "emote-sixseven"
        }

        self.emote_durations = {
            "idle_zombie": 28.754937,
            "idle_layingdown2": 21.546653,
            "idle_layingdown": 24.585168,
            "idle-sleep": 22.620446,
            "idle-sad": 24.377214,
            "idle-posh": 21.851256,
            "idle-loop-tired": 21.959007,
            "idle-loop-tapdance": 6.261593,
            "idle-loop-sitfloor": 22.321055,
            "idle-loop-shy": 16.47449,
            "idle-loop-sad": 6.052999,
            "idle-loop-happy": 18.798322,
            "idle-loop-annoyed": 17.058522,
            "idle-loop-aerobics": 8.507535,
            "idle-lookup": 22.339865,
            "idle-hero": 21.877099,
            "idle-floorsleeping": 13.935264,
            "idle-enthusiastic": 15.941537,
            "idle-dance-swinging": 13.198551,
            "idle-dance-headbobbing": 25.367458,
            "idle-angry": 25.427848,
            "emote-yes": 2.565001,
            "emote-wings": 13.134487,
            "emote-wave": 2.690873,
            "emote-tired": 4.61063,
            "emote-think": 3.691104,
            "emote-theatrical": 8.591869,
            "emote-tapdance": 11.057294,
            "emote-superrun": 6.273226,
            "emote-superpunch": 3.751054,
            "emote-sumo": 10.868834,
            "emote-suckthumb": 4.185944,
            "emote-splitsdrop": 4.46931,
            "emote-snowball": 5.230467,
            "emote-snowangel": 6.218627,
            "emote-shy": 4.477567,
            "emote-secrethandshake": 3.879024,
            "emote-sad": 5.411073,
            "emote-ropepull": 8.769656,
            "emote-roll": 3.560517,
            "emote-rofl": 6.314731,
            "emote-robot": 7.607362,
            "emote-rainbow": 2.813373,
            "emote-proposing": 4.27888,
            "emote-peekaboo": 3.629867,
            "emote-peace": 5.755004,
            "emote-panic": 2.850966,
            "emote-no": 2.703034,
            "emote-ninjarun": 4.754721,
            "emote-nightfever": 15.0,
            "emote-monster_fail": 15.0,
            "emote-model": 15.0,
            "emote-lust": 15.0,
            "emote-levelup": 15.0,
            "emote-laughing2": 15.0,
            "emote-laughing": 15.0,
            "emote-kiss": 15.0,
            "emote-kicking": 15.0,
            "emote-jumpb": 15.0,
            "emote-gravity": 15.0,
            "emote-judochop": 15.0,
            "emote-jetpack": 15.0,
            "emote-hugyourself": 15.0,
            "emote-hot": 15.0,
            "emote-hero": 15.0,
            "emote-hello": 15.0,
            "emote-headball": 15.0,
            "emote-harlemshake": 15.0,
            "emote-happy": 15.0,
            "emote-handstand": 15.0,
            "emote-greedy": 15.0,
            "emote-graceful": 15.0,
            "emote-gordonshuffle": 15.0,
            "emote-ghost-idle": 15.0,
            "emote-gangnam": 15.0,
            "emote-frollicking": 15.0,
            "emote-fainting": 15.0,
            "emote-fail2": 15.0,
            "emote-fail1": 15.0,
            "emote-exasperatedb": 15.0,
            "emote-exasperated": 15.0,
            "emote-elbowbump": 15.0,
            "emote-disco": 15.0,
            "emote-disappear": 15.0,
            "emote-deathdrop": 15.0,
            "emote-death2": 15.0,
            "emote-death": 15.0,
            "emote-dab": 15.0,
            "emote-curtsy": 15.0,
            "emote-confused": 15.0,
            "emote-cold": 15.0,
            "emote-charging": 15.0,
            "emote-bunnyhop": 15.0,
            "emote-bow": 15.0,
            "emote-boo": 15.0,
            "emote-baseball": 15.0,
            "emote-apart": 15.0,
            "emoji-thumbsup": 15.0,
            "emoji-there": 15.0,
            "emoji-sneeze": 15.0,
            "emoji-smirking": 15.0,
            "emoji-sick": 15.0,
            "emoji-scared": 15.0,
            "emoji-punch": 15.0,
            "emoji-pray": 15.0,
            "emoji-poop": 15.0,
            "emoji-naughty": 15.0,
            "emoji-mind-blown": 15.0,
            "emoji-lying": 15.0,
            "emoji-halo": 15.0,
            "emoji-hadoken": 15.0,
            "emoji-give-up": 15.0,
            "emoji-gagging": 15.0,
            "emoji-flex": 15.0,
            "emoji-dizzy": 15.0,
            "emoji-cursing": 15.0,
            "emoji-crying": 15.0,
            "emoji-clapping": 15.0,
            "emoji-celebrate": 15.0,
            "emoji-arrogance": 15.0,
            "emoji-angry": 15.0,
            "dance-voguehands": 15.0,
            "dance-tiktok8": 15.0,
            "dance-tiktok2": 15.0,
            "dance-spiritual": 15.0,
            "dance-smoothwalk": 15.0,
            "dance-singleladies": 15.0,
            "dance-shoppingcart": 15.0,
            "dance-russian": 15.0,
            "dance-robotic": 15.0,
            "dance-pennywise": 15.0,
            "dance-orangejustice": 15.0,
            "dance-metal": 15.0,
            "dance-martial-artist": 15.0,
            "dance-macarena": 15.0,
            "dance-handsup": 15.0,
            "dance-duckwalk": 15.0,
            "dance-breakdance": 15.0,
            "dance-blackpink": 15.0,
            "dance-aerobics": 15.0,
            "emote-hyped": 15.0,
            "dance-jinglebell": 15.0,
            "idle-nervous": 15.0,
            "idle-toilet": 15.0,
            "emote-attention": 15.0,
            "sit-open": 15.0,
            "emote-astronaut": 15.0,
            "dance-zombie": 15.0,
            "emoji-ghost": 15.0,
            "emote-hearteyes": 15.0,
            "emote-swordfight": 15.0,
            "emote-timejump": 15.0,
            "emote-snake": 15.0,
            "emote-heartfingers": 15.0,
            "emote-heartshape": 15.0,
            "emote-hug": 15.0,
            "emote-lagughing": 15.0,
            "emoji-eyeroll": 15.0,
            "emote-embarrassed": 15.0,
            "emote-float": 15.0,
            "emote-telekinesis": 15.0,
            "dance-sexy": 15.0,
            "emote-puppet": 15.0,
            "idle-fighter": 15.0,
            "dance-pinguin": 15.0,
            "dance-creepypuppet": 15.0,
            "emote-sleigh": 15.0,
            "emote-maniac": 15.0,
            "emote-energyball": 15.0,
            "idle_singing": 15.0,
            "emote-frog": 15.0,
            "emote-superpose": 15.0,
            "emote-cute": 15.0,
            "dance-tiktok9": 15.0,
            "dance-weird": 15.0,
            "dance-tiktok10": 15.0,
            "emote-pose7": 15.0,
            "emote-pose8": 15.0,
            "idle-dance-casual": 15.0,
            "emote-pose1": 15.0,
            "emote-pose3": 15.0,
            "emote-pose5": 15.0,
            "emote-cutey": 15.0,
            "emote-punkguitar": 15.0,
            "emote-zombierun": 15.0,
            "dance-icecream": 15.0,
            "dance-wrong": 15.0,
            "idle-uwu": 15.0,
            "idle-dance-tiktok4": 15.0,
            "emote-shy2": 15.0,
            "dance-anime": 15.0,
            "dance-kawai": 15.0,
            "idle-wild": 15.0,
            "emote-iceskating": 15.0,
            "emote-pose6": 15.0,
            "emote-celebrationstep": 15.0,
            "emote-creepycute": 15.0,
            "emote-frustrated": 15.0,
            "emote-pose10": 15.0,
            "sit-relaxed": 15.0,
            "emote-stargaze": 15.0,
            "emote-slap": 15.0,
            "emote-boxer": 15.0,
            "emote-headblowup": 15.0,
            "emote-kawaiigogo": 15.0,
            "emote-repose": 15.0,
            "idle-dance-tiktok7": 15.0,
            "emote-shrink": 15.0,
            "emote-pose9": 15.0,
            "emote-teleporting": 15.0,
            "dance-touch": 15.0,
            "idle-guitar": 15.0,
            "emote-gift": 15.0,
            "dance-employee": 15.0,
            "emote-kissing": 15.0,
            "dance-tiktok11": 15.0,
            "dance-tiktok12": 15.0,
            "dance-tiktok13": 15.0,
            "emote-cutesalute": 15.0,
            "emote-salute": 15.0,
            "dance-floss": 11.0,
            "emote-dead": 6.0,
            "emote-alice-shrink": 15.0,
            "emote-threadexchange-star": 15.0,
            "emote-inside-out": 15.0,
            "emote-collab-photo-right": 15.0,
            "emote-afk-idle": 15.0,
            "emote-meditate-idle": 15.0,
            "emote-sixseve-noimg": 15.0,
            "emote-sixseven": 15.0
        }

    def is_host(self, username: str) -> bool:
        """يتحقق مما إذا كان المستخدم يملك رتبة Host (أعلى مستوى صلاحيات، أعلى من المشرف وVIP) أم لا."""
        return username.lower() in [h.lower() for h in self.config.get("host_usernames", [])]

    def load_config(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                # إضافة المفاتيح الجديدة (مثل host_usernames) إلى الإعدادات القديمة
                # التي قد تكون محفوظة مسبقًا على السيرفر ولا تحتوي على هذا المفتاح
                for key, value in DEFAULT_CONFIG.items():
                    if key not in self.config:
                        self.config[key] = value.copy() if isinstance(value, (list, dict)) else value
                logger.info("تم تحميل الإعدادات بنجاح.")
            else:
                logger.info("ملف الإعدادات غير موجود، سيتم استخدام الإعدادات الافتراضية...")
                self.config = DEFAULT_CONFIG
                self.save_config()
        except json.JSONDecodeError as e:
            logger.error(f"خطأ في بنية JSON لملف الإعدادات: {e}")
            self.config = DEFAULT_CONFIG
            self.save_config()
        except Exception as e:
            logger.error(f"خطأ في تحميل الإعدادات: {e}")
            self.config = DEFAULT_CONFIG
            self.save_config()

        # توحيد أسماء المستخدمين إلى أحرف صغيرة (المقارنات في الأوامر تتم بأحرف صغيرة)
        # ونسخ القوائم حتى لا يتم تعديل DEFAULT_CONFIG مباشرة
        for list_key in ("host_usernames", "admin_usernames", "vip_usernames", "banned_users"):
            seen = []
            for name in self.config.get(list_key, []):
                name = str(name).lower()
                if name not in seen:
                    seen.append(name)
            self.config[list_key] = seen

        # المالك الأساسي يجب أن يكون دائمًا Host
        if "rqtm" not in self.config["host_usernames"]:
            self.config["host_usernames"].append("rqtm")

        # 🛡️ تأكد دائمًا من أن الـ Host موجودون أيضًا في قائمة المشرفين
        # (الـ Host يملك تلقائيًا جميع صلاحيات المشرف)
        for host in self.config.get("host_usernames", []):
            if host not in self.config["admin_usernames"]:
                self.config["admin_usernames"].append(host)

    def save_config(self):
        try:
            config_to_save = self.config.copy()
            config_to_save["host_usernames"] = list(config_to_save["host_usernames"])
            config_to_save["admin_usernames"] = list(config_to_save["admin_usernames"])
            config_to_save["vip_usernames"] = list(config_to_save["vip_usernames"])
            config_to_save["banned_users"] = list(config_to_save["banned_users"])
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=4, ensure_ascii=False)
            logger.info("تم حفظ الإعدادات بنجاح.")
        except Exception as e:
            logger.error(f"خطأ في حفظ الإعدادات: {e}")

    def get_message(self, key, **kwargs):
        messages = {
            "ar": {
                "welcome": self.config["welcome_message"],
                "invalid_command": "❌ أمر غير معروف! اكتب !help لعرض الأوامر.",
                "no_permission": "ليس لديك صلاحية لاستخدام هذا الأمر!",
                "user_not_found": "المستخدم {username} غير متصل.",
                "invalid_format": "صيغة غير صحيحة: {format}",
                "teleport_success": "تم نقل @{username} إلى {location}!",
                "teleport_error": "خطأ في النقل: {error}",
                "heart_success": "تم إرسال {count} قلب بنفسجي إلى @{username}!",
                "heart_all_success": "تم إرسال {count} تفاعلاً إلى {count} مستخدمين!",
                "clap_success": "تم إرسال {count} تصفيق إلى @{username}!",
                "wink_success": "تم إرسال {count} غمزة إلى @{username}!",
                "wave_success": "تم إرسال {count} تحية إلى @{username}!",
                "thumbs_success": "تم إرسال {count} إعجاب إلى @{username}!",
                "wallet_error": "خطأ في جلب الرصيد: {error}",
                "tip_success": "تم إرسال {amount} من الذهب إلى @{username}.",
                "tip_all_success": "تم إرسال {amount} من الذهب إلى {count} مستخدمين!",
                "ban_success": "تم حظر @{username}!",
                "unban_success": "تم إلغاء حظر @{username} بنجاح!",
                "unban_not_banned": "المستخدم @{username} غير موجود في قائمة الحظر.",
                "dancechain_success": "تم تشغيل سلسلة الرقص للمستخدم @{username}!",
                "addtele_success": "تم حفظ الموقع {location}!",
                "deltele_success": "تم حذف الموقع {location} بنجاح!",
                "deltele_not_found": "الموقع {location} غير موجود!",
                "deltele_protected": "لا يمكن حذف الموقع الافتراضي {location}!",
                "set_item_success": "تم تغيير مظهر البوت إلى عناصر @{username}!",
                "listadd_empty": "قائمة المشرفين فارغة.",
                "listadd_success": "قائمة المشرفين ({count}):\n{admin_list}",
                "freeze_success": "تم تجميد المستخدم @{username}!",
                "unfreeze_success": "تم إلغاء تجميد @{username}!",
                "unfreeze_not_frozen": "المستخدم @{username} غير مجمّد!",
                "party_success": "تم تفعيل الرقصة رقم {dance_number} للمستخدم @{username}!",
                "party_all_success": "تم تفعيل الرقصة رقم {dance_number} لـ {count} مستخدمين!",
                "partys_success": "تم إيقاف الرقص الإجباري للمستخدم @{username}!",
                "partys_not_dancing": "المستخدم @{username} ليس في وضع الرقص الإجباري!"
            }
        }
        lang = self.config.get("language", "ar")
        return messages.get(lang, messages["ar"])[key].format(**kwargs)

    async def cleanup_tasks(self):
        try:
            for username, task in self.dance_tasks.items():
                if not task.done():
                    task.cancel()
                try:
                    await task
                except CancelledError:
                    pass
            self.dance_tasks.clear()
            self.user_dances.clear()
            self.party_dances.clear()

            if self.quiz_task and not self.quiz_task.done():
                self.quiz_task.cancel()
            self.quiz_task = None
            self.quiz_current = None
            if self.quiz_think_task and not self.quiz_think_task.done():
                self.quiz_think_task.cancel()
            self.quiz_think_task = None
            
            for username, task in self.frozen_users.items():
                if not task.done():
                    task.cancel()
                try:
                    await task
                except CancelledError:
                    pass
            self.frozen_users.clear()
            
            if self.announcement_task and not self.announcement_task.done():
                self.announcement_task.cancel()
                try:
                    await self.announcement_task
                except CancelledError:
                    pass
                self.announcement_task = None
            if self.score_update_task and not self.score_update_task.done():
                self.score_update_task.cancel()
                try:
                    await self.score_update_task
                except CancelledError:
                    pass
                self.score_update_task = None
            logger.info("تم إلغاء جميع المهام غير المتزامنة.")
        except Exception as e:
            logger.error(f"خطأ في إلغاء المهام: {e}")

    async def on_start(self, session_metadata):
        logger.info("تم اتصال البوت بنجاح.")
        self.user_id = getattr(session_metadata, "user_id", None)
        if not self.user_id:
            logger.error("لم يتم العثور على معرّف البوت في session_metadata.")
            await self.highrise.chat("❌ تعذر العثور على معرّف البوت.")
            return

        try:
            sp = self.config.get("start_position", START_POSITION)
            dest = Position(x=sp["x"], y=sp["y"], z=sp["z"])
            await self.highrise.teleport(user_id=self.user_id, dest=dest)
            await self.highrise.chat("تم نقل البوت إلى الموقع الابتدائي!")
            logger.info("تم نقل البوت إلى الموقع الأولي.")
        except Exception as e:
            logger.error(f"خطأ في النقل الأولي: {e}")
            await self.highrise.chat(f"خطأ في النقل الأولي: {e}")

        await self.sync_room_users()
        self.announcement_task = create_task(self.announcement_loop())
        self.score_update_task = create_task(self.score_update_loop())

    async def on_user_join(self, user: User, position: Position):
        username = user.username.lower()
        if username in self.config["banned_users"]:
            try:
                await self.highrise.moderate_room(user.id, "kick")
                logger.info(f"تم طرد المستخدم المحظور {user.username} تلقائيًا.")
            except Exception as e:
                logger.error(f"خطأ في طرد {user.username}: {e}")
            return
        self.active_users[username] = user
        self.user_positions[username] = position
        self.user_scores[username] = self.user_scores.get(username, 0) + 10
        await self.highrise.chat(self.get_message("welcome", username=user.username))
        logger.info(f"المستخدم {user.username} (ID: {user.id}) دخل الغرفة. الموقع: {position}")

    async def on_user_leave(self, user: User, position: Position | None = None):
        username = user.username.lower()
        self.active_users.pop(username, None)
        self.user_positions.pop(username, None)
        if username in self.dance_tasks:
            self.dance_tasks[username].cancel()
            self.dance_tasks.pop(username, None)
            self.user_dances.pop(username, None)
            self.party_dances.pop(username, None)
        if username in self.frozen_users:
            self.frozen_users[username].cancel()
            self.frozen_users.pop(username, None)
        await self.highrise.chat(f"@{user.username} غادر الغرفة.")
        logger.info(f"المستخدم {user.username} (ID: {user.id}) غادر الغرفة. الموقع: {position}")

    async def sync_room_users(self):
        try:
            room_users = await self.highrise.get_room_users()
            current_users = {user_data[0].username.lower(): user_data for user_data in room_users.content}
            
            for username in list(self.active_users.keys()):
                if username not in current_users:
                    self.active_users.pop(username, None)
                    self.user_positions.pop(username, None)
                    if username in self.dance_tasks:
                        self.dance_tasks[username].cancel()
                        self.dance_tasks.pop(username, None)
                    if username in self.frozen_users:
                        self.frozen_users[username].cancel()
                        self.frozen_users.pop(username, None)
                    logger.info(f"تم حذف المستخدم {username} من القوائم (مزامنة).")
            
            for username, user_data in current_users.items():
                self.active_users[username] = user_data[0]
                self.user_positions[username] = user_data[1]
            
            logger.info(f"تمت مزامنة المستخدمين. عدد المستخدمين: {len(self.active_users)}. المستخدمون: {[user.username for user in self.active_users.values()]}")
            await self.highrise.chat(f"{len(self.active_users)} مستخدمين في الغرفة.")
        except Exception as e:
            logger.error(f"خطأ في مزامنة المستخدمين: {e}", exc_info=True)
            await self.highrise.chat("تعذر التعرف على مستخدمي الغرفة.")

    async def announcement_loop(self):
        try:
            while True:
                await sleep(self.config["announcement_interval"])
                await self.highrise.chat(self.config["announcement_message"])
                logger.info("تم إرسال رسالة الإعلان.")
        except CancelledError:
            logger.info("تم إلغاء مهمة الإعلانات.")
        except Exception as e:
            logger.error(f"خطأ في حلقة الإعلانات: {e}")

    async def score_update_loop(self):
        try:
            while True:
                await sleep(300)
                for username in self.active_users:
                    self.user_scores[username] = self.user_scores.get(username, 0) + 5
                logger.info("تم تحديث نقاط المستخدمين.")
        except CancelledError:
            logger.info("تم إلغاء مهمة تحديث النقاط.")
        except Exception as e:
            logger.error(f"خطأ في حلقة تحديث النقاط: {e}")

    async def on_user_move(self, user: User, position: Position):
        username = user.username.lower()
        self.user_positions[username] = position
        if username in self.config["admin_usernames"]:
            logger.info(f"تحرك المشرف {user.username} إلى الموقع x={position.x}, y={position.y}, z={position.z}.")
        if username in self.frozen_users:
            try:
                original_position = self.user_positions.get(username)
                if original_position:
                    await self.highrise.teleport(user_id=user.id, dest=original_position)
                    logger.info(f"تمت إعادة المستخدم المجمّد {username} إلى الموقع الأولي x={original_position.x}, y={original_position.y}, z={original_position.z}.")
            except Exception as e:
                logger.error(f"خطأ في إعادة {username} إلى موقع التجميد: {e}")

    async def on_chat(self, user: User, message: str):
        username = user.username.lower()
        msg = message.strip()
        msg_lower = msg.lower()
        
        # التحقق مما إذا كانت الرسالة خاصة أم عامة
        # في Highrise، تصل الرسائل الخاصة عادةً عبر قناة (channel) خاصة
        # لكن يمكننا التعرف عليها بفحص النمط (pattern)
        
        try:
            self.user_scores[username] = self.user_scores.get(username, 0) + 2

            # 🧠 فحص جواب مسابقة المعلومات قبل أي شيء (حتى لا يتحول الجواب إلى رقصة)
            if (self.quiz_current and self.quiz_current["winner"] is None
                    and not msg.startswith("!")
                    and self.quiz_norm(msg) in self.quiz_current["answers"]):
                self.quiz_current["winner"] = user.username
                entry = self.quiz_scores.setdefault(username, {"name": user.username, "points": 0})
                entry["name"] = user.username
                entry["points"] += 1
                self.quiz_session[username] = self.quiz_session.get(username, 0) + 1
                self.save_quiz_scores()
                self.quiz_current["event"].set()
                return

            if msg_lower in self.emotes:
                await self.start_dance(user, self.emotes[msg_lower])
            elif msg_lower in ["stop", "ستوب", "توقف", "قف"]:
                await self.stop_dance(user)
            elif msg_lower in ["المطور", "مطور", "creature", "creator", "مالك", "مطور البوت", "صاحب البوت"]:
                await self.highrise.chat("👑 مطوّر هذا البوت: @RQTM 👑")
            elif msg_lower.startswith("!"):
                parts = msg.split()
                parts_lower = [p.lower() for p in parts]
                cmd = parts_lower[0] if len(parts_lower) == 1 else ("!item set" if parts_lower[0] == "!item" else parts_lower[0])
                if cmd in self.commands:
                    await self.commands[cmd](user, parts)
                else:
                    await self.highrise.chat(self.get_message("invalid_command"))
        except Exception as e:
            logger.error(f"خطأ في on_chat من {username}: {e}")

    async def on_message(self, user_id: str, text: str, message_id: str) -> None:
        logger.info(f"📥 رسالة خاصة جديدة من المستخدم [{user_id}]: {text}")
        
        # ⛔ منع الرد على رسائل البوت نفسه
        if user_id == self.user_id:
            return

        # 👑 نص دعائي لتعريف مميزات البوت مع معلومات الإيجار
        auto_reply = (
            "أهلاً بك يا عزيزي! ❤️\n\n"
            "🤖 أنا بوت متطور ومتكامل لإدارة الغرفة والارتقاء بها!\n\n"
            "✨ **بعض مميزاتي الرائعة:**\n"
            "🔹 يحتوي على ٢٥٦ رقصة جذابة تعمل بتكرار دائم وبدون أي تأخير ولو لثانية واحدة! 💃\n"
            "🔹 نظام ترحيب ذكي وتلقائي بمجرد دخول اللاعبين 🚪\n"
            "🔹 ميزة الرقص الجماعي والحفلة التلقائية لجميع أعضاء الغرفة 🕺\n"
            "🔹 أمان عالٍ وإدارة كاملة للمشرفين وأوامر خاصة 🛠️\n"
            "🔹 استضافة على مدار ٢٤ ساعة وبدون انقطاع على سيرفرات قوية ⚡\n\n"
            "🤝 **شروط الإيجار:**\n"
            "لاستئجار هذا البوت الرائع لغرفتك، يرجى مراسلة الحساب التالي الآن:\n"
            "👉 @RQTM 👈"
        )
        
        try:
            # ✉️ إرسال الرد مباشرة إلى الرسائل الخاصة (Inbox) للمستخدم
            await self.highrise.send_message(user_id, auto_reply)
        except Exception as e:
            logger.error(f"خطأ في إرسال الرد التلقائي على الرسالة الخاصة: {e}")

    async def on_tip(self, sender: User, receiver: User, tip):
        try:
            # فحص بنية كائن tip للتأكد من وجود الخاصية amount
            amount = getattr(tip, "amount", 0)
            await self.highrise.chat(f"@{sender.username} أرسل {amount} من الذهب إلى @{receiver.username}!")
            self.user_scores[sender.username.lower()] = self.user_scores.get(sender.username.lower(), 0) + amount
            logger.info(f"المستخدم {sender.username} أرسل {amount} ذهب إلى {receiver.username}.")
        except Exception as e:
            logger.error(f"خطأ في معالجة الإكرامية من {sender.username} إلى {receiver.username}: {e}")
            await self.highrise.chat(f"خطأ في معالجة الإكرامية من @{sender.username} إلى @{receiver.username}: {e}")

    async def start_dance(self, user: User, emote: str):
        username = user.username.lower()
        await self.stop_dance(user)
        self.user_dances[username] = emote
        duration = self.emote_durations.get(emote, 15.0)
        # ⚡ ضمان تنفيذ الرقصة كاملة: بدلاً من النقص، نضيف ثانية واحدة إلى المدة
        # حتى لو كانت المدة المسجلة أقل قليلاً من الواقع، لا تنقطع الرقصة أبدًا في المنتصف
        sleep_time = duration + 1.0

        async def dance_loop():
            try:
                while self.user_dances.get(username) == emote:
                    await self.highrise.send_emote(emote, user.id)
                    await sleep(sleep_time)
            except CancelledError:
                logger.info(f"تم إلغاء مهمة الرقص للمستخدم {username}.")
            except Exception as e:
                logger.error(f"خطأ في حلقة الرقص للمستخدم {username}: {e}")

        task = create_task(dance_loop())
        self.dance_tasks[username] = task
        logger.info(f"بدأ المستخدم {username} الرقص {emote}.")

    async def stop_dance(self, user: User):
        username = user.username.lower()
        if username in self.party_dances and self.party_dances[username][1]:
            await self.highrise.chat(f"@{username} لا يمكنك إيقاف الرقص الإجباري! فقط المشرف يستطيع إيقافه بالأمر !partys.")
            logger.info(f"حاول المستخدم {username} إيقاف الرقص الإجباري لكنه غير مسموح.")
            return
        if username in self.dance_tasks:
            self.user_dances.pop(username, None)
            self.party_dances.pop(username, None)
            self.dance_tasks[username].cancel()
            self.dance_tasks.pop(username, None)
            
        
            
           

    async def cmd_emote_link(self, user: User, parts: list):
        """
        !emote <الرابط> - تشغيل أي رقصة مباشرة من رابط high.rs، دون الحاجة إلى
        إضافتها يدويًا إلى قائمة self.emotes.
        مثال: !emote https://high.rs/item?id=emote-alice-shrink&type=emote
        """
        if len(parts) < 2:
            await self.highrise.chat("⚠️ يرجى إدخال رابط الرقصة بعد الأمر.\nمثال: !emote https://high.rs/item?id=emote-xxx&type=emote")
            return

        link = parts[1].strip()
        emote_id = None
        try:
            if link.startswith("http://") or link.startswith("https://"):
                parsed = urlparse(link)
                query = parse_qs(parsed.query)
                emote_id = query.get("id", [None])[0]
            elif link.startswith("id=") or "id=" in link:
                # حالة نسخ الجزء id=... فقط، دون الرابط كاملاً
                query = parse_qs(link)
                emote_id = query.get("id", [None])[0]
            else:
                # حالة إرسال المستخدم معرّف الرقصة فقط دون الرابط
                emote_id = link
        except Exception as e:
            logger.error(f"خطأ في تحليل رابط !emote من {user.username}: {e}")
            emote_id = None

        if not emote_id:
            await self.highrise.chat("❌ الرابط غير صالح! يجب أن يحتوي على id=...")
            logger.info(f"رابط غير صالح لـ !emote من {user.username}: {link}")
            return

        # اختبار تشغيل الرقصة قبل تثبيتها على وضع التكرار، لنخبرك فورًا إذا كان المعرّف خاطئًا
        try:
            await self.highrise.send_emote(emote_id, user.id)
        except Exception as e:
            await self.highrise.chat(f"❌ فشل تشغيل الرقصة [{emote_id}]. ربما المعرّف خاطئ أو أن هذا العنصر ليس رقصة.")
            logger.error(f"خطأ في تشغيل !emote للرقصة {emote_id} من {user.username}: {e}")
            return

        await self.start_dance(user, emote_id)
        await self.highrise.chat(f"✅ بدأت الرقصة [{emote_id}] وتم تثبيتها! للإيقاف اكتب: stop")
        logger.info(f"شغّل المستخدم {user.username} الرقصة المخصصة {emote_id} عبر الرابط.")

    # ====================== مسابقة المعلومات ======================
    @staticmethod
    def quiz_norm(text: str) -> str:
        """توحيد النص (حذف التشكيل، توحيد الهمزات والتاء المربوطة والياء، حذف المسافات وأل التعريف)."""
        text = str(text).lower().strip()
        text = re.sub("[\u0610-\u061a\u064b-\u065f\u0670\u0640\u200c]", "", text)
        mapping = {
            "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
            "ى": "ي", "ئ": "ي", "ؤ": "و", "ة": "ه",
            "\u06af": "ك", "\u0686": "ك", "\u06a9": "ك",  # حروف الكاف المنقوطة في اللهجة العراقية -> ك
            "\u067e": "ب", "\u06cc": "ي",
        }
        text = "".join(mapping.get(ch, ch) for ch in text)
        text = re.sub(r"[\s\u060c\u061f?!.,;:'\"()\-]+", "", text)
        if text.startswith("ال") and len(text) > 3:
            text = text[2:]
        return text

    def load_quiz_scores(self):
        try:
            if os.path.exists(QUIZ_SCORES_FILE):
                with open(QUIZ_SCORES_FILE, "r", encoding="utf-8") as f:
                    self.quiz_scores = json.load(f)
        except Exception as e:
            logger.error(f"خطأ في تحميل نقاط المسابقة: {e}")
            self.quiz_scores = {}

    def save_quiz_scores(self):
        try:
            with open(QUIZ_SCORES_FILE, "w", encoding="utf-8") as f:
                json.dump(self.quiz_scores, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"خطأ في حفظ نقاط المسابقة: {e}")

    async def bot_play_emote(self, emote: str):
        """تشغيل حركة مرة وحدة على البوت نفسه."""
        try:
            await self.highrise.send_emote(emote, self.user_id)
        except Exception as e:
            logger.error(f"خطأ في تشغيل حركة البوت {emote}: {e}")

    async def quiz_think_loop(self):
        """يكرر حركة التفكير طول ما السؤال مفتوح."""
        try:
            while True:
                await self.bot_play_emote(QUIZ_EMOTE_THINK)
                await sleep(self.emote_durations.get(QUIZ_EMOTE_THINK, 4.0) + 0.5)
        except CancelledError:
            pass

    async def stop_quiz_think(self):
        if self.quiz_think_task and not self.quiz_think_task.done():
            self.quiz_think_task.cancel()
            try:
                await self.quiz_think_task
            except CancelledError:
                pass
        self.quiz_think_task = None

    def start_bot_emote_loop(self, emote_name: str):
        """حلقة رقص البوت المستمرة (!emotebot)."""
        if self.user_id in self.dance_tasks:
            self.dance_tasks[self.user_id].cancel()
            self.dance_tasks.pop(self.user_id, None)
        self.bot_emote_name = emote_name
        sleep_time = self.emote_durations.get(emote_name, 15.0) + 1.0

        async def new_emote_loop():
            try:
                while True:
                    await self.highrise.send_emote(emote_name, self.user_id)
                    await sleep(sleep_time)
            except CancelledError:
                logger.info("تم إلغاء رقصة البوت المستمرة.")
            except Exception as e:
                logger.error(f"خطأ في رقصة البوت المستمرة: {e}")

        self.dance_tasks[self.user_id] = create_task(new_emote_loop())

    async def run_quiz(self, rounds: int):
        self.quiz_session = {}
        # إيقاف رقصة البوت المستمرة مؤقتًا حتى ما تتعارض مع حركات المسابقة
        resume_emote = self.bot_emote_name
        if self.user_id in self.dance_tasks:
            self.dance_tasks[self.user_id].cancel()
            self.dance_tasks.pop(self.user_id, None)
        try:
            await self.highrise.chat(random.choice(QUIZ_INTROS).format(rounds=rounds))
            await sleep(4)
            questions = random.sample(QUIZ_QUESTIONS, rounds)
            for number, (question, answers) in enumerate(questions, 1):
                event = asyncio.Event()
                self.quiz_current = {
                    "answers": {self.quiz_norm(a) for a in answers},
                    "event": event,
                    "winner": None,
                }
                await self.highrise.chat(f"{QUIZ_COLOR_QUESTION}🧠 السؤال {number}/{rounds}: {question}\n⏳ عدكم {QUIZ_TIMEOUT} ثانية!")
                # 🤔 البوت يفكر طول ما ينتظر الجواب
                self.quiz_think_task = create_task(self.quiz_think_loop())
                try:
                    await asyncio.wait_for(event.wait(), timeout=QUIZ_TIMEOUT)
                    winner = self.quiz_current["winner"]
                    points = self.quiz_scores.get(winner.lower(), {}).get("points", 1)
                    await self.stop_quiz_think()
                    await self.bot_play_emote(QUIZ_EMOTE_HAPPY)  # 🤩 حماس
                    await self.highrise.chat(QUIZ_COLOR_ANSWER + random.choice(QUIZ_CORRECT).format(user=winner, points=points))
                except asyncio.TimeoutError:
                    await self.stop_quiz_think()
                    await self.bot_play_emote(QUIZ_EMOTE_SAD)  # 😢 حزن
                    await self.highrise.chat(QUIZ_COLOR_ANSWER + random.choice(QUIZ_TIMEOUT_MSG).format(answer=answers[0]))
                finally:
                    self.quiz_current = None
                    await self.stop_quiz_think()
                await sleep(4)

            if self.quiz_session:
                ranking = sorted(
                    self.quiz_session.items(),
                    key=lambda item: item[1],
                    reverse=True,
                )[:3]
                medals = ["🥇", "🥈", "🥉"]
                lines = ["🏆 خلصت المسابقة! النتيجة:"]
                for index, (name, pts) in enumerate(ranking):
                    display = self.quiz_scores.get(name, {}).get("name", name)
                    lines.append(f"{medals[index]} @{display} - {pts} نقطة")
                lines.append("عاشت إيديكم كلكم! 👏")
                await self.highrise.chat("\n".join(lines))
            else:
                await self.highrise.chat("😅 خلصت المسابقة وماكو أحد جاوب ولا سؤال! المرة الجاية ركزوا شوية.")
        except CancelledError:
            raise
        except Exception as e:
            logger.error(f"خطأ في المسابقة: {e}")
        finally:
            self.quiz_current = None
            await self.stop_quiz_think()
            # إرجاع رقصة البوت المستمرة إذا كانت شغالة قبل المسابقة
            if resume_emote:
                self.start_bot_emote_loop(resume_emote)

    async def cmd_quiz(self, user: User, parts: list):
        if user.username.lower() not in self.config["admin_usernames"]:
            await self.highrise.chat(self.get_message("no_permission"))
            return
        if self.quiz_task and not self.quiz_task.done():
            await self.highrise.chat("⚠️ المسابقة شغالة هسه! اكتب !quizstop إذا تريد توقفها.")
            return
        rounds = QUIZ_DEFAULT_ROUNDS
        if len(parts) > 1:
            try:
                rounds = int(parts[1])
            except ValueError:
                await self.highrise.chat(self.get_message("invalid_format", format="!quiz [العدد]"))
                return
        rounds = max(1, min(rounds, len(QUIZ_QUESTIONS)))
        self.quiz_task = create_task(self.run_quiz(rounds))
        logger.info(f"بدأ {user.username} مسابقة من {rounds} أسئلة.")

    async def cmd_quizstop(self, user: User, parts: list):
        if user.username.lower() not in self.config["admin_usernames"]:
            await self.highrise.chat(self.get_message("no_permission"))
            return
        if self.quiz_task and not self.quiz_task.done():
            self.quiz_task.cancel()
            self.quiz_current = None
            await self.stop_quiz_think()
            await self.highrise.chat("🛑 انوقفت المسابقة. نشوفكم بجولة ثانية! 👋")
        else:
            await self.highrise.chat("ماكو مسابقة شغالة هسه.")

    async def cmd_top(self, user: User, parts: list):
        if not self.quiz_scores:
            await self.highrise.chat("📊 للحين ماكو أحد عنده نقاط، اطلبوا من المشرف يبدي مسابقة! 🧠")
            return
        ranking = sorted(self.quiz_scores.values(), key=lambda e: e["points"], reverse=True)[:5]
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        lines = ["🏆 متصدرين المسابقة:"]
        for index, entry in enumerate(ranking):
            lines.append(f"{medals[index]} @{entry['name']} - {entry['points']} نقطة")
        await self.highrise.chat("\n".join(lines))

    async def cmd_help(self, user: User, parts: list):
        help_text = (
            "أوامر البوت:\n"
            "1-6 - تشغيل رقصة\n"
            "stop - إيقاف الرقص\n"
            "!help - عرض المساعدة\n"
            "!spam العدد الرسالة - إرسال رسائل سبام\n"
            "!tele @username [vip|vip1|dj|موقع_مخصص] - نقل المستخدم\n"
            "!tele to @username - الانتقال إلى المستخدم\n"
            "!tele me @username - نقل المستخدم إلى المشرف\n"
            "!tele me all - نقل الجميع إلى المشرف\n"
            "!heart العدد @username - إرسال قلب بنفسجي\n"
            "!heart all - قلب بنفسجي للجميع\n"
            "!clap العدد @username - إرسال clap\n"
            "!clap all - clap للجميع\n"
            "!wink العدد @username - إرسال wink\n"
            "!wink all - wink للجميع\n"
            "!wave العدد @username - إرسال wave\n"
            "!wave all - wave للجميع\n"
            "!thumbs العدد @username - إرسال thumbs-up\n"
            "!thumbs all - thumbs-up للجميع\n"
            "!wallet - عرض رصيد البوت\n"
            "!set - نقل البوت إلى المشرف\n"
            "!setstart - حفظ مكانك كنقطة بداية دائمة للبوت\n"
            "!item set @username - تغيير مظهر البوت إلى عناصر المستخدم\n"
            "!tip <العدد> all - إكرامية للجميع\n"
            "!vip - الانتقال إلى VIP\n"
            "!vip1 - الانتقال إلى VIP1\n"
            "!dj - الانتقال إلى DJ\n"
            "!down - الانتقال إلى الأسفل\n"
            "!ban @username - حظر المستخدم\n"
            "!unban @username - إلغاء حظر المستخدم\n"
            "!dancechain - تشغيل سلسلة الرقص\n"
            "!addtele اسم_الموقع - حفظ موقع جديد\n"
            "!deltele اسم_الموقع - حذف موقع النقل\n"
            "!welcome الرسالة - تعيين رسالة الترحيب\n"
            "!addadmin @username - إضافة مشرف (Host فقط)\n"
            "!removeadmin @username - حذف مشرف (Host فقط)\n"
            "!emotebot اسم/رقم_الرقصة - تغيير رقصة البوت المستمرة (للمشرفين فقط)\n"
            "!emote رابط_الرقصة - تشغيل أي رقصة من رابط high.rs (دون الحاجة لإضافتها مسبقًا)\n"
            "!loopchat الرسالة - تعيين رسالة البوت المتكررة/السبام (للمشرفين فقط)\n"
            "!listadd - عرض قائمة المشرفين\n"
            "!freeze @username - تجميد المستخدم\n"
            "!unfreeze @username - إلغاء تجميد المستخدم\n"
            "!party @username رقم - تشغيل رقص إجباري للمستخدم\n"
            "!party all رقم - تشغيل الرقص للجميع\n"
            "!partys @username - إيقاف الرقص الإجباري للمستخدم\n"
            "!quiz [العدد] - بدء مسابقة المعلومات (للمشرفين)\n"
            "!quizstop - إيقاف المسابقة (للمشرفين)\n"
            "!top - عرض المتصدرين\n\n"
            "📩 لمزيد من المعلومات راسل @RQTM!"
        )
        for chunk in [help_text[i:i+200] for i in range(0, len(help_text), 200)]:
            await self.highrise.chat(chunk)
        logger.info(f"طلب {user.username} المساعدة.")

    async def cmd_spam(self, user: User, parts: list):
        if user.username.lower() not in self.config["admin_usernames"]:
            await self.highrise.chat(self.get_message("no_permission"))
            logger.info(f"المستخدم {user.username} لا يملك الصلاحية لتنفيذ !spam.")
            return

        parts = [p.lower() for p in parts]
        if len(parts) < 2 or not parts[1].isdigit():
            await self.highrise.chat(self.get_message("invalid_format", format="!spam العدد الرسالة"))
            logger.info(f"صيغة غير صحيحة للأمر !spam من قبل {user.username}.")
            return

        try:
            count = int(parts[1])
            spam_message = " ".join(parts[2:]) if len(parts) > 2 else "رسالة سبام تجريبية!"
            if count < 1 or count > 100:
                await self.highrise.chat("يجب أن يكون عدد الرسائل بين 1 و100.")
                logger.info(f"عدد الرسائل غير صالح ({count}) أدخله {user.username}.")
                return

            for _ in range(count):
                await self.highrise.chat(spam_message)
                await sleep(2.0)
            logger.info(f"تم إرسال {count} رسالة سبام بواسطة {user.username}: {spam_message}")
            await self.highrise.chat(f"تم إرسال {count} رسالة سبام!")
        except Exception as e:
            await self.highrise.chat(f"خطأ في إرسال رسائل السبام: {str(e)}")
            logger.error(f"خطأ في cmd_spam لـ {user.username}: {str(e)}")

    async def cmd_tele(self, user: User, parts: list):
        if user.username.lower() not in self.config["admin_usernames"]:
            await self.highrise.chat(self.get_message("no_permission"))
            logger.info(f"المستخدم {user.username} لا يملك الصلاحية لتنفيذ !tele.")
            return

        parts = [p.lower() for p in parts]
        
        if len(parts) == 3 and parts[1].startswith("@"):
            target_username = parts[1][1:].lower()
            location = parts[2]
            target_user = self.active_users.get(target_username)
            if not target_user:
                await self.highrise.chat(self.get_message("user_not_found", username=target_username))
                logger.info(f"لم يتم العثور على المستخدم المستهدف {target_username} (طلب {user.username}).")
                return
            if location not in self.config["teleport_locations"]:
                await self.highrise.chat(f"الموقع {location} غير موجود!")
                logger.info(f"لم يتم العثور على الموقع {location} (طلب {user.username}) للنقل.")
                return
            try:
                dest_data = self.config["teleport_locations"][location]
                dest = Position(x=dest_data["x"], y=dest_data["y"], z=dest_data["z"])
                await self.highrise.teleport(user_id=target_user.id, dest=dest)
                await self.highrise.chat(self.get_message("teleport_success", username=target_user.username, location=location.upper()))
                logger.info(f"تم نقل المستخدم {target_username} إلى {location}.")
            except Exception as e:
                await self.highrise.chat(self.get_message("teleport_error", error=str(e)))
                logger.error(f"خطأ في نقل {target_username} إلى {location}: {e}")

        elif len(parts) == 3 and parts[1] == "to" and parts[2].startswith("@"):
            target_username = parts[2][1:].lower()
            target_user = self.active_users.get(target_username)
            if not target_user:
                await self.highrise.chat(self.get_message("user_not_found", username=target_username))
                logger.info(f"لم يتم العثور على المستخدم المستهدف {target_username} (طلب {user.username}).")
                return
            try:
                position = self.user_positions.get(target_username)
                if position:
                    await self.highrise.teleport(user_id=user.id, dest=position)
                    await self.highrise.chat(f"تم نقل @{user.username} إلى مكان @{target_user.username}.")
                    logger.info(f"تم نقل المستخدم {user.username} إلى مكان {target_username}.")
                else:
                    await self.highrise.chat("موقع المستخدم غير متاح.")
                    logger.info(f"موقع {target_username} غير متاح لنقل {user.username}.")
            except Exception as e:
                await self.highrise.chat(self.get_message("teleport_error", error=str(e)))
                logger.error(f"خطأ في الانتقال إلى {target_username}: {e}")

        elif len(parts) == 3 and parts[1] == "me" and parts[2].startswith("@"):
            target_username = parts[2][1:].lower()
            target_user = self.active_users.get(target_username)
            if not target_user:
                await self.highrise.chat(self.get_message("user_not_found", username=target_username))
                logger.info(f"لم يتم العثور على المستخدم المستهدف {target_username} (طلب {user.username}).")
                return
            try:
                position = self.user_positions.get(user.username.lower())
                if position:
                    await self.highrise.teleport(user_id=target_user.id, dest=position)
                    await self.highrise.chat(f"تم نقل @{target_user.username} إلى مكان @{user.username}.")
                    logger.info(f"تم نقل المستخدم {target_username} إلى مكان {user.username}.")
                else:
                    await self.highrise.chat("موقعك غير متاح.")
                    logger.info(f"موقع {user.username} غير متاح لنقل {target_username}.")
            except Exception as e:
                await self.highrise.chat(self.get_message("teleport_error", error=str(e)))
                logger.error(f"خطأ في نقل {target_username} إلى {user.username}: {e}")

        elif len(parts) == 3 and parts[1] == "me" and parts[2] == "all":
            admin_position = self.user_positions.get(user.username.lower())
            if not admin_position:
                await self.highrise.chat("موقعك غير متاح.")
                logger.info(f"موقع {user.username} غير متاح لنقل جميع المستخدمين.")
                return
            try:
                successful_teleports = 0
                for username, target_user in self.active_users.items():
                    if target_user.id == user.id or target_user.id == self.user_id:
                        continue
                    if username not in self.active_users:
                        logger.info(f"أصبح المستخدم {username} غير متصل أثناء النقل.")
                        continue
                    try:
                        await self.highrise.teleport(user_id=target_user.id, dest=admin_position)
                        successful_teleports += 1
                        await sleep(0.5)
                    except Exception as e:
                        logger.error(f"خطأ في نقل {username} إلى {user.username}: {e}")
                await self.highrise.chat(f"تم نقل {successful_teleports} مستخدم إلى مكان @{user.username}.")
                logger.info(f"تم نقل {successful_teleports} مستخدم إلى مكان {user.username}.")
            except Exception as e:
                await self.highrise.chat(self.get_message("teleport_error", error=str(e)))
                logger.error(f"خطأ في نقل جميع المستخدمين إلى {user.username}: {e}")

        else:
            await self.highrise.chat(self.get_message("invalid_format", format="!tele @username [الموقع] أو !tele to @username أو !tele me @username أو !tele me all"))
            logger.info(f"صيغة غير صحيحة للأمر !tele من قبل {user.username}.")

    async def cmd_heart(self, user: User, parts: list):
        parts = [p.lower() for p in parts]
        
        if parts[0] == "!heart" and len(parts) == 2 and parts[1] == "all":
            if user.username.lower() not in self.config["admin_usernames"]:
                await self.highrise.chat(self.get_message("no_permission"))
                return
            try:
                active_users = list(self.active_users.items())
                active_users_count = len([u for u in active_users if u[1].id != self.user_id])
                if active_users_count == 0:
                    await self.highrise.chat("لا يوجد مستخدمون متصلون في الغرفة!")
                    return
                reaction_id = "heart"
                successful_hearts = 0
                for username, target_user in active_users:
                    if target_user.id == self.user_id:
                        continue
                    if username not in self.active_users:
                        logger.info(f"أصبح المستخدم {username} غير متصل أثناء إرسال القلوب.")
                        continue
                    try:
                        await self.highrise.react(reaction_id, target_user.id)
                        successful_hearts += 1
                        await sleep(0.5)
                    except Exception as e:
                        await self.highrise.chat(f"خطأ في إرسال قلب بنفسجي إلى @{target_user.username}: {e}")
                        logger.error(f"خطأ في إرسال قلب إلى {target_user.username}: {e}")
                if successful_hearts > 0:
                    await self.highrise.chat(self.get_message("heart_all_success", count=successful_hearts))
                    logger.info(f"تم إرسال قلب بنفسجي إلى {successful_hearts} مستخدم.")
                else:
                    await self.highrise.chat("لم يتم إرسال أي قلب بنجاح.")
            except Exception as e:
                await self.highrise.chat(f"خطأ في تنفيذ الأمر: {e}")
                logger.error(f"خطأ في إرسال القلوب للجميع: {e}")
            return

        if len(parts) != 3:
            await self.highrise.chat(self.get_message("invalid_format", format="!heart العدد @username أو !heart all"))
            return

        try:
            count = int(parts[1])
            if count < 1 or count > 100:
                await self.highrise.chat(f"@{user.username}: يجب أن يكون العدد بين 1 و100.")
                return
        except ValueError:
            await self.highrise.chat(f"@{user.username}: العدد غير صالح.")
            return

        target_username = parts[2].lstrip('@').lower()
        target_user = next((u for u in self.active_users.values() if u.username.lower() == target_username), None)

        if not target_user:
            await self.highrise.chat(self.get_message("user_not_found", username=target_username))
            return

        try:
            reaction_id = "heart"
            for _ in range(count):
                if target_user.username.lower() not in self.active_users:
                    await self.highrise.chat(f"أصبح المستخدم @{target_user.username} غير متصل ولم يتم إرسال القلوب.")
                    logger.info(f"أصبح المستخدم {target_user.username} غير متصل أثناء إرسال القلوب.")
                    return
                await self.highrise.react(reaction_id, target_user.id)
                await sleep(0.5)
            await self.highrise.chat(self.get_message("heart_success", count=count, username=target_user.username))
            logger.info(f"تم إرسال {count} قلب بنفسجي إلى {target_user.username}.")
        except Exception as e:
            await self.highrise.chat(f"خطأ في إرسال القلب البنفسجي: {e}")
            logger.error(f"خطأ في إرسال قلب إلى {target_username}: {e}")

    async def cmd_clap(self, user: User, parts: list):
        parts = [p.lower() for p in parts]
        
        if parts[0] == "!clap" and len(parts) == 2 and parts[1] == "all":
            if user.username.lower() not in self.config["admin_usernames"]:
                await self.highrise.chat(self.get_message("no_permission"))
                return
            try:
                active_users = list(self.active_users.items())
                active_users_count = len([u for u in active_users if u[1].id != self.user_id])
                if active_users_count == 0:
                    await self.highrise.chat("لا يوجد مستخدمون متصلون في الغرفة!")
                    return
                reaction_id = "clap"
                successful_reactions = 0
                for username, target_user in active_users:
                    if target_user.id == self.user_id:
                        continue
                    if username not in self.active_users:
                        logger.info(f"أصبح المستخدم {username} غير متصل أثناء إرسال clap.")
                        continue
                    try:
                        await self.highrise.react(reaction_id, target_user.id)
                        successful_reactions += 1
                        await sleep(0.5)
                    except Exception as e:
                        await self.highrise.chat(f"خطأ في إرسال clap إلى @{target_user.username}: {e}")
                        logger.error(f"خطأ في إرسال clap إلى {target_user.username}: {e}")
                if successful_reactions > 0:
                    await self.highrise.chat(self.get_message("heart_all_success", count=successful_reactions))
                    logger.info(f"تم إرسال Clap إلى {successful_reactions} مستخدم.")
                else:
                    await self.highrise.chat("لم يتم إرسال أي تصفيق بنجاح.")
            except Exception as e:
                await self.highrise.chat(f"خطأ في تنفيذ الأمر: {e}")
                logger.error(f"خطأ في إرسال clap للجميع: {e}")
            return

        if len(parts) != 3:
            await self.highrise.chat(self.get_message("invalid_format", format="!clap العدد @username أو !clap all"))
            return

        try:
            count = int(parts[1])
            if count < 1 or count > 100:
                await self.highrise.chat(f"@{user.username}: يجب أن يكون العدد بين 1 و100.")
                return
        except ValueError:
            await self.highrise.chat(f"@{user.username}: العدد غير صالح.")
            return

        target_username = parts[2].lstrip('@').lower()
        target_user = next((u for u in self.active_users.values() if u.username.lower() == target_username), None)

        if not target_user:
            await self.highrise.chat(self.get_message("user_not_found", username=target_username))
            return

        try:
            reaction_id = "clap"
            for _ in range(count):
                if target_user.username.lower() not in self.active_users:
                    await self.highrise.chat(f"أصبح المستخدم @{target_user.username} غير متصل ولم يتم إرسال clap.")
                    logger.info(f"أصبح المستخدم {target_user.username} غير متصل أثناء إرسال clap.")
                    return
                await self.highrise.react(reaction_id, target_user.id)
                await sleep(0.5)
            await self.highrise.chat(self.get_message("clap_success", count=count, username=target_user.username))
            logger.info(f"تم إرسال {count} clap إلى {target_user.username}.")
        except Exception as e:
            await self.highrise.chat(f"خطأ في إرسال clap: {e}")
            logger.error(f"خطأ في إرسال clap إلى {target_username}: {e}")

    async def cmd_wink(self, user: User, parts: list):
        parts = [p.lower() for p in parts]
        
        if parts[0] == "!wink" and len(parts) == 2 and parts[1] == "all":
            if user.username.lower() not in self.config["admin_usernames"]:
                await self.highrise.chat(self.get_message("no_permission"))
                return
            try:
                active_users = list(self.active_users.items())
                active_users_count = len([u for u in active_users if u[1].id != self.user_id])
                if active_users_count == 0:
                    await self.highrise.chat("لا يوجد مستخدمون متصلون في الغرفة!")
                    return
                reaction_id = "wink"
                successful_reactions = 0
                for username, target_user in active_users:
                    if target_user.id == self.user_id:
                        continue
                    if username not in self.active_users:
                        logger.info(f"أصبح المستخدم {username} غير متصل أثناء إرسال wink.")
                        continue
                    try:
                        await self.highrise.react(reaction_id, target_user.id)
                        successful_reactions += 1
                        await sleep(0.5)
                    except Exception as e:
                        await self.highrise.chat(f"خطأ في إرسال wink إلى @{target_user.username}: {e}")
                        logger.error(f"خطأ في إرسال wink إلى {target_user.username}: {e}")
                if successful_reactions > 0:
                    await self.highrise.chat(self.get_message("heart_all_success", count=successful_reactions))
                    logger.info(f"تم إرسال Wink إلى {successful_reactions} مستخدم.")
                else:
                    await self.highrise.chat("لم يتم إرسال أي غمزة بنجاح.")
            except Exception as e:
                await self.highrise.chat(f"خطأ في تنفيذ الأمر: {e}")
                logger.error(f"خطأ في إرسال wink للجميع: {e}")
            return

        if len(parts) != 3:
            await self.highrise.chat(self.get_message("invalid_format", format="!wink العدد @username أو !wink all"))
            return

        try:
            count = int(parts[1])
            if count < 1 or count > 100:
                await self.highrise.chat(f"@{user.username}: يجب أن يكون العدد بين 1 و100.")
                return
        except ValueError:
            await self.highrise.chat(f"@{user.username}: العدد غير صالح.")
            return

        target_username = parts[2].lstrip('@').lower()
        target_user = next((u for u in self.active_users.values() if u.username.lower() == target_username), None)

        if not target_user:
            await self.highrise.chat(self.get_message("user_not_found", username=target_username))
            return

        try:
            reaction_id = "wink"
            for _ in range(count):
                if target_user.username.lower() not in self.active_users:
                    await self.highrise.chat(f"أصبح المستخدم @{target_user.username} غير متصل ولم يتم إرسال wink.")
                    logger.info(f"أصبح المستخدم {target_user.username} غير متصل أثناء إرسال wink.")
                    return
                await self.highrise.react(reaction_id, target_user.id)
                await sleep(0.5)
            await self.highrise.chat(self.get_message("wink_success", count=count, username=target_user.username))
            logger.info(f"تم إرسال {count} wink إلى {target_user.username}.")
        except Exception as e:
            await self.highrise.chat(f"خطأ في إرسال wink: {e}")
            logger.error(f"خطأ في إرسال wink إلى {target_username}: {e}")

    async def cmd_wave(self, user: User, parts: list):
        parts = [p.lower() for p in parts]
        
        if parts[0] == "!wave" and len(parts) == 2 and parts[1] == "all":
            if user.username.lower() not in self.config["admin_usernames"]:
                await self.highrise.chat(self.get_message("no_permission"))
                return
            try:
                active_users = list(self.active_users.items())
                active_users_count = len([u for u in active_users if u[1].id != self.user_id])
                if active_users_count == 0:
                    await self.highrise.chat("لا يوجد مستخدمون متصلون في الغرفة!")
                    return
                reaction_id = "wave"
                successful_reactions = 0
                for username, target_user in active_users:
                    if target_user.id == self.user_id:
                        continue
                    if username not in self.active_users:
                        logger.info(f"أصبح المستخدم {username} غير متصل أثناء إرسال wave.")
                        continue
                    try:
                        await self.highrise.react(reaction_id, target_user.id)
                        successful_reactions += 1
                        await sleep(0.5)
                    except Exception as e:
                        await self.highrise.chat(f"خطأ في إرسال wave إلى @{target_user.username}: {e}")
                        logger.error(f"خطأ في إرسال wave إلى {target_user.username}: {e}")
                if successful_reactions > 0:
                    await self.highrise.chat(self.get_message("heart_all_success", count=successful_reactions))
                    logger.info(f"تم إرسال Wave إلى {successful_reactions} مستخدم.")
                else:
                    await self.highrise.chat("لم يتم إرسال أي تحية بنجاح.")
            except Exception as e:
                await self.highrise.chat(f"خطأ في تنفيذ الأمر: {e}")
                logger.error(f"خطأ في إرسال wave للجميع: {e}")
            return

        if len(parts) != 3:
            await self.highrise.chat(self.get_message("invalid_format", format="!wave العدد @username أو !wave all"))
            return

        try:
            count = int(parts[1])
            if count < 1 or count > 100:
                await self.highrise.chat(f"@{user.username}: يجب أن يكون العدد بين 1 و100.")
                return
        except ValueError:
            await self.highrise.chat(f"@{user.username}: العدد غير صالح.")
            return

        target_username = parts[2].lstrip('@').lower()
        target_user = next((u for u in self.active_users.values() if u.username.lower() == target_username), None)

        if not target_user:
            await self.highrise.chat(self.get_message("user_not_found", username=target_username))
            return

        try:
            reaction_id = "wave"
            for _ in range(count):
                if target_user.username.lower() not in self.active_users:
                    await self.highrise.chat(f"أصبح المستخدم @{target_user.username} غير متصل ولم يتم إرسال wave.")
                    logger.info(f"أصبح المستخدم {target_user.username} غير متصل أثناء إرسال wave.")
                    return
                await self.highrise.react(reaction_id, target_user.id)
                await sleep(0.5)
            await self.highrise.chat(self.get_message("wave_success", count=count, username=target_user.username))
            logger.info(f"تم إرسال {count} wave إلى {target_user.username}.")
        except Exception as e:
            await self.highrise.chat(f"خطأ في إرسال wave: {e}")
            logger.error(f"خطأ في إرسال wave إلى {target_username}: {e}")

    async def cmd_thumbs(self, user: User, parts: list):
        parts = [p.lower() for p in parts]
        
        if parts[0] == "!thumbs" and len(parts) == 2 and parts[1] == "all":
            if user.username.lower() not in self.config["admin_usernames"]:
                await self.highrise.chat(self.get_message("no_permission"))
                return
            try:
                active_users = list(self.active_users.items())
                active_users_count = len([u for u in active_users if u[1].id != self.user_id])
                if active_users_count == 0:
                    await self.highrise.chat("لا يوجد مستخدمون متصلون في الغرفة!")
                    return
                reaction_id = "thumbs-up"
                successful_reactions = 0
                for username, target_user in active_users:
                    if target_user.id == self.user_id:
                        continue
                    if username not in self.active_users:
                        logger.info(f"أصبح المستخدم {username} غير متصل أثناء إرسال thumbs-up.")
                        continue
                    try:
                        await self.highrise.react(reaction_id, target_user.id)
                        successful_reactions += 1
                        await sleep(0.5)
                    except Exception as e:
                        await self.highrise.chat(f"خطأ في إرسال thumbs-up إلى @{target_user.username}: {e}")
                        logger.error(f"خطأ في إرسال thumbs-up إلى {target_user.username}: {e}")
                if successful_reactions > 0:
                    await self.highrise.chat(self.get_message("heart_all_success", count=successful_reactions))
                    logger.info(f"تم إرسال Thumbs-up إلى {successful_reactions} مستخدم.")
                else:
                    await self.highrise.chat("لم يتم إرسال أي إعجاب بنجاح.")
            except Exception as e:
                await self.highrise.chat(f"خطأ في تنفيذ الأمر: {e}")
                logger.error(f"خطأ في إرسال thumbs-up للجميع: {e}")
            return

        if len(parts) != 3:
            await self.highrise.chat(self.get_message("invalid_format", format="!thumbs العدد @username أو !thumbs all"))
            return

        try:
            count = int(parts[1])
            if count < 1 or count > 100:
                await self.highrise.chat(f"@{user.username}: يجب أن يكون العدد بين 1 و100.")
                return
        except ValueError:
            await self.highrise.chat(f"@{user.username}: العدد غير صالح.")
            return

        target_username = parts[2].lstrip('@').lower()
        target_user = next((u for u in self.active_users.values() if u.username.lower() == target_username), None)

        if not target_user:
            await self.highrise.chat(self.get_message("user_not_found", username=target_username))
            return

        try:
            reaction_id = "thumbs-up"
            for _ in range(count):
                if target_user.username.lower() not in self.active_users:
                    await self.highrise.chat(f"أصبح المستخدم @{target_user.username} غير متصل ولم يتم إرسال thumbs-up.")
                    logger.info(f"أصبح المستخدم {target_user.username} غير متصل أثناء إرسال thumbs-up.")
                    return
                await self.highrise.react(reaction_id, target_user.id)
                await sleep(0.5)
            await self.highrise.chat(self.get_message("thumbs_success", count=count, username=target_user.username))
            logger.info(f"تم إرسال {count} thumbs-up إلى {target_user.username}.")
        except Exception as e:
            await self.highrise.chat(f"خطأ في إرسال thumbs-up: {e}")
            logger.error(f"خطأ في إرسال thumbs-up إلى {target_username}: {e}")

    async def cmd_wallet(self, user: User, parts: list):
        if user.username.lower() not in self.config["admin_usernames"]:
            await self.highrise.chat(self.get_message("no_permission"))
            return

        try:
            wallet = await self.highrise.get_wallet()
            gold_amount = 0
            if hasattr(wallet, "content") and isinstance(wallet.content, list):
                for item in wallet.content:
                    if hasattr(item, "type") and item.type == "gold" and hasattr(item, "amount"):
                        gold_amount = item.amount
                        break
            else:
                logger.error("بنية wallet غير معروفة.")
                await self.highrise.chat("خطأ: تنسيق استجابة المحفظة غير معروف.")
                return
            
            await self.highrise.chat(f"رصيد الذهب للبوت: {gold_amount} ذهب")
            logger.info(f"رصيد البوت: {gold_amount} ذهب")
        except Exception as e:
            await self.highrise.chat(self.get_message("wallet_error", error=str(e)))
            logger.error(f"خطأ في جلب الرصيد: {e}")

    async def cmd_tip(self, user: User, parts: list):
        if user.username.lower() not in self.config["admin_usernames"]:
            await self.highrise.chat(self.get_message("no_permission"))
            return

        parts = [p.lower() for p in parts]
        if len(parts) != 3 or not parts[1].isdigit() or parts[2] != "all":
            await self.highrise.chat(self.get_message("invalid_format", format="!tip <العدد> all (العدد: 1، 5، 10، 50، 100)"))
            return

        try:
            tip_amount = int(parts[1])
            if tip_amount not in [1, 5, 10, 50, 100]:
                await self.highrise.chat("يجب أن تكون كمية الذهب 1 أو 5 أو 10 أو 50 أو 100.")
                return

            gold_bar_map = {
                1: "gold_bar_1",
                5: "gold_bar_5",
                10: "gold_bar_10",
                50: "gold_bar_50",
                100: "gold_bar_100"
            }
            gold_bar_item = gold_bar_map.get(tip_amount)
            if not gold_bar_item:
                await self.highrise.chat(f"القيمة {tip_amount} غير مدعومة.")
                return

            wallet = await self.highrise.get_wallet()
            gold_amount = 0
            if hasattr(wallet, "content") and isinstance(wallet.content, list):
                for item in wallet.content:
                    if hasattr(item, "type") and item.type == "gold" and hasattr(item, "amount"):
                        gold_amount = item.amount
                        break
            else:
                logger.error("بنية wallet غير معروفة.")
                await self.highrise.chat("خطأ: تنسيق استجابة المحفظة غير معروف.")
                return

            active_users = [u for u in self.active_users.values() if u.id != self.user_id]
            active_users_count = len(active_users)
            total_needed = tip_amount * active_users_count

            if gold_amount < total_needed:
                await self.highrise.chat(
                    f"رصيد البوت ({gold_amount} ذهب) غير كافٍ لإرسال {tip_amount} ذهب إلى {active_users_count} مستخدم."
                )
                return

            successful_tips = 0
            for target_user in active_users:
                if target_user.username.lower() not in self.active_users:
                    logger.info(f"أصبح المستخدم {target_user.username} غير متصل أثناء إرسال الإكرامية.")
                    continue
                try:
                    response = await self.highrise.tip_user(target_user.id, gold_bar_item)
                    if hasattr(response, "error"):
                        raise Exception(f"خطأ API: {response.error}")
                    successful_tips += 1
                    await self.highrise.chat(self.get_message("tip_success", amount=tip_amount, username=target_user.username))
                    logger.info(f"تم إرسال {tip_amount} ذهب إلى {target_user.username} بنجاح.")
                    await sleep(3.0)
                except Exception as e:
                    await self.highrise.chat(f"خطأ في إرسال الإكرامية إلى @{target_user.username}: {e}")
                    logger.error(f"خطأ في إرسال الإكرامية إلى {target_user.username}: {e}")

            if successful_tips > 0:
                await self.highrise.chat(self.get_message("tip_all_success", amount=tip_amount, count=successful_tips))
            else:
                await self.highrise.chat("لم يتم إرسال أي إكرامية بنجاح.")

            wallet = await self.highrise.get_wallet()
            gold_amount = 0
            if hasattr(wallet, "content") and isinstance(wallet.content, list):
                for item in wallet.content:
                    if hasattr(item, "type") and item.type == "gold" and hasattr(item, "amount"):
                        gold_amount = item.amount
                        break
            await self.highrise.chat(f"رصيد البوت الجديد: {gold_amount} ذهب")
            logger.info(f"رصيد البوت الجديد: {gold_amount} ذهب")

        except Exception as e:
            await self.highrise.chat(f"خطأ غير معروف: {e}")
            logger.error(f"خطأ في cmd_tip: {e}")

    async def cmd_set(self, user: User, parts: list):
        if user.username.lower() not in self.config["admin_usernames"]:
            await self.highrise.chat(self.get_message("no_permission"))
            return

        pos = self.user_positions.get(user.username.lower())
        if not pos:
            await self.highrise.chat(f"@{user.username}: موقعك غير معروف.")
            return
        try:
            await self.highrise.teleport(user_id=self.user_id, dest=pos)
            await self.highrise.chat(f"تم نقل البوت إلى موقع @{user.username}.")
            logger.info(f"تم نقل البوت إلى موقع {user.username}.")
        except Exception as e:
            await self.highrise.chat(f"خطأ في نقل البوت: {e}")
            logger.error(f"خطأ في cmd_set: {e}")

    async def cmd_setstart(self, user: User, parts: list):
        """!setstart - يحفظ مكانك الحالي كنقطة بداية دائمة للبوت (يروح لها كل ما يدخل الغرفة)."""
        if user.username.lower() not in self.config["admin_usernames"]:
            await self.highrise.chat(self.get_message("no_permission"))
            return
        pos = self.user_positions.get(user.username.lower())
        if not pos:
            await self.highrise.chat(f"@{user.username}: موقعك غير معروف.")
            return
        try:
            self.config["start_position"] = {"x": pos.x, "y": pos.y, "z": pos.z}
            self.save_config()
            await self.highrise.teleport(user_id=self.user_id, dest=pos)
            await self.highrise.chat("✅ تم حفظ مكانك كنقطة بداية للبوت!")
            logger.info(f"{user.username} حدد نقطة بداية البوت: {pos.x}, {pos.y}, {pos.z}")
        except Exception as e:
            await self.highrise.chat(f"خطأ في حفظ نقطة البداية: {e}")
            logger.error(f"خطأ في cmd_setstart: {e}")

    async def cmd_vip(self, user: User, parts: list):
        if user.username.lower() not in self.config["admin_usernames"]:
            await self.highrise.chat(self.get_message("no_permission"))
            return
        try:
            dest_data = self.config["teleport_locations"]["vip"]
            dest = Position(x=dest_data["x"], y=dest_data["y"], z=dest_data["z"])
            await self.highrise.teleport(user_id=user.id, dest=dest)
            await self.highrise.chat(self.get_message("teleport_success", username=user.username, location="VIP"))
            logger.info(f"تم نقل المستخدم {user.username} إلى VIP.")
        except Exception as e:
            await self.highrise.chat(self.get_message("teleport_error", error=str(e)))
            logger.error(f"خطأ في cmd_vip: {e}")

    async def cmd_vip1(self, user: User, parts: list):
        if user.username.lower() not in self.config["admin_usernames"]:
            await self.highrise.chat(self.get_message("no_permission"))
            return
        try:
            dest_data = self.config["teleport_locations"]["vip1"]
            dest = Position(x=dest_data["x"], y=dest_data["y"], z=dest_data["z"])
            await self.highrise.teleport(user_id=user.id, dest=dest)
            await self.highrise.chat(self.get_message("teleport_success", username=user.username, location="VIP1"))
            logger.info(f"تم نقل المستخدم {user.username} إلى VIP1.")
        except Exception as e:
            await self.highrise.chat(self.get_message("teleport_error", error=str(e)))
            logger.error(f"خطأ في cmd_vip1: {e}")

    async def cmd_dj(self, user: User, parts: list):
        if user.username.lower() not in self.config["admin_usernames"]:
            await self.highrise.chat(self.get_message("no_permission"))
            return
        try:
            dest_data = self.config["teleport_locations"]["dj"]
            dest = Position(x=dest_data["x"], y=dest_data["y"], z=dest_data["z"])
            await self.highrise.teleport(user_id=user.id, dest=dest)
            await self.highrise.chat(self.get_message("teleport_success", username=user.username, location="DJ"))
            logger.info(f"تم نقل المستخدم {user.username} إلى DJ.")
        except Exception as e:
            await self.highrise.chat(self.get_message("teleport_error", error=str(e)))
            logger.error(f"خطأ في cmd_dj: {e}")

    async def cmd_down(self, user: User, parts: list):
        try:
            dest = Position(x=2.0, y=0.5, z=1.5)
            await self.highrise.teleport(user_id=user.id, dest=dest)
            await self.highrise.chat(f"@{user.username} نزل إلى الأسفل.")
            logger.info(f"تم نقل المستخدم {user.username} إلى الإحداثيات x=2, y=0.5, z=1.5.")
        except Exception as e:
            await self.highrise.chat(self.get_message("teleport_error", error=str(e)))
            logger.error(f"خطأ في cmd_down: {e}")

    async def cmd_ban(self, user: User, parts: list):
        if user.username.lower() not in self.config["admin_usernames"]:
            await self.highrise.chat(self.get_message("no_permission"))
            return
        parts = [p.lower() for p in parts]
        if len(parts) != 2 or not parts[1].startswith("@"):
            await self.highrise.chat(self.get_message("invalid_format", format="!ban @username"))
            return
        target_username = parts[1][1:].lower()
        target_user = self.active_users.get(target_username)
        if not target_user:
            await self.highrise.chat(self.get_message("user_not_found", username=target_username))
            return
        self.config["banned_users"].append(target_username)
        self.save_config()
        await self.highrise.chat(self.get_message("ban_success", username=target_username))
        logger.info(f"تم حظر المستخدم {target_username} بواسطة {user.username}.")

    async def cmd_unban(self, user: User, parts: list):
        if user.username.lower() not in self.config["admin_usernames"]:
            await self.highrise.chat(self.get_message("no_permission"))
            logger.info(f"المستخدم {user.username} لا يملك الصلاحية لتنفيذ !unban.")
            return

        parts = [p.lower() for p in parts]
        if len(parts) != 2 or not parts[1].startswith("@"):
            await self.highrise.chat(self.get_message("invalid_format", format="!unban @username"))
            logger.info(f"صيغة غير صحيحة للأمر !unban من قبل {user.username}.")
            return

        target_username = parts[1][1:].lower()
        if target_username not in self.config["banned_users"]:
            await self.highrise.chat(self.get_message("unban_not_banned", username=target_username))
            logger.info(f"طلب {user.username} إلغاء حظر {target_username}، لكنه غير موجود في قائمة الحظر.")
            return

        try:
            self.config["banned_users"].remove(target_username)
            self.save_config()
            await self.highrise.chat(self.get_message("unban_success", username=target_username))
            logger.info(f"تم إلغاء حظر المستخدم {target_username} بواسطة {user.username}.")
        except Exception as e:
            await self.highrise.chat(f"خطأ في إلغاء حظر المستخدم @{target_username}: {str(e)}")
            logger.error(f"خطأ في cmd_unban لـ {target_username}: {str(e)}")

    async def cmd_dancechain(self, user: User, parts: list):
        dance_list = ["dance-tiktok8", "dance-blackpink", "dance-tiktok2"]
        for emote in dance_list:
            await self.highrise.send_emote(emote, user.id)
            await sleep(self.emote_durations.get(emote, 15.0))
        await self.highrise.chat(self.get_message("dancechain_success", username=user.username))
        logger.info(f"تم تشغيل سلسلة الرقص للمستخدم {user.username}.")

    async def cmd_addtele(self, user: User, parts: list):
        if user.username.lower() not in self.config["admin_usernames"]:
            await self.highrise.chat(self.get_message("no_permission"))
            return
        parts = [p.lower() for p in parts]
        if len(parts) != 2:
            await self.highrise.chat(self.get_message("invalid_format", format="!addtele اسم_الموقع"))
            return
        location_name = parts[1]
        pos = self.user_positions.get(user.username.lower())
        if not pos:
            await self.highrise.chat("موقعك غير معروف!")
            return
        self.config["teleport_locations"][location_name] = {"x": pos.x, "y": pos.y, "z": pos.z}
        self.save_config()
        await self.highrise.chat(self.get_message("addtele_success", location=location_name))
        logger.info(f"تمت إضافة الموقع {location_name} بواسطة {user.username}.")

    async def cmd_deltele(self, user: User, parts: list):
        if user.username.lower() not in self.config["admin_usernames"]:
            await self.highrise.chat(self.get_message("no_permission"))
            logger.info(f"المستخدم {user.username} لا يملك الصلاحية لتنفيذ !deltele.")
            return

        parts = [p.lower() for p in parts]
        if len(parts) != 2:
            await self.highrise.chat(self.get_message("invalid_format", format="!deltele اسم_الموقع"))
            logger.info(f"صيغة غير صحيحة للأمر !deltele من قبل {user.username}.")
            return

        location_name = parts[1]
        if location_name in ["vip", "vip1", "dj"]:
            await self.highrise.chat(self.get_message("deltele_protected", location=location_name))
            logger.info(f"حاول المستخدم {user.username} حذف الموقع الافتراضي {location_name}.")
            return

        if location_name not in self.config["teleport_locations"]:
            await self.highrise.chat(self.get_message("deltele_not_found", location=location_name))
            logger.info(f"طلب {user.username} حذف الموقع {location_name}، لكنه غير موجود.")
            return

        try:
            del self.config["teleport_locations"][location_name]
            self.save_config()
            await self.highrise.chat(self.get_message("deltele_success", location=location_name))
            logger.info(f"تم حذف الموقع {location_name} بواسطة {user.username}.")
        except Exception as e:
            await self.highrise.chat(f"خطأ في حذف الموقع {location_name}: {str(e)}")
            logger.error(f"خطأ في cmd_deltele لـ {location_name}: {str(e)}")

    async def cmd_set_item(self, user: User, parts: list):
        if user.username.lower() not in self.config["admin_usernames"]:
            await self.highrise.chat(self.get_message("no_permission"))
            logger.info(f"المستخدم {user.username} لا يملك الصلاحية لتنفيذ !item set.")
            return

        parts = [p.lower() for p in parts]
        if len(parts) != 3 or not parts[2].startswith("@"):
            await self.highrise.chat(self.get_message("invalid_format", format="!item set @username"))
            logger.info(f"صيغة غير صحيحة للأمر !item set من قبل {user.username}.")
            return

        target_username = parts[2][1:].lower()
        target_user = self.active_users.get(target_username)
        if not target_user:
            await self.highrise.chat(self.get_message("user_not_found", username=target_username))
            logger.info(f"لم يتم العثور على المستخدم المستهدف {target_username} (طلب {user.username}).")
            return

        try:
            outfit_response = await self.highrise.get_user_outfit(target_user.id)
            if not hasattr(outfit_response, "outfit") or not outfit_response.outfit:
                await self.highrise.chat(f"خطأ: بيانات المظهر لـ @{target_username} غير متاحة.")
                logger.error(f"بيانات المظهر لـ {target_username} غير متاحة.")
                return

            outfit_items = outfit_response.outfit
            await self.highrise.set_outfit(outfit_items)
            await self.highrise.chat(self.get_message("set_item_success", username=target_username))
            logger.info(f"تم تغيير مظهر البوت إلى عناصر {target_username}: {outfit_items}")
        except Exception as e:
            await self.highrise.chat(f"خطأ في تغيير مظهر البوت: {str(e)}")
            logger.error(f"خطأ في cmd_set_item لـ {target_username}: {str(e)}")

    async def cmd_welcome(self, user: User, parts: list):
        if user.username.lower() not in self.config["admin_usernames"]:
            await self.highrise.chat(self.get_message("no_permission"))
            logger.info(f"المستخدم {user.username} لا يملك الصلاحية لتنفيذ !welcome.")
            return

        parts = parts[:1] + ([" ".join(parts[1:])] if len(parts) > 1 else [])
        if len(parts) < 2:
            await self.highrise.chat(self.get_message("invalid_format", format="!welcome الرسالة"))
            logger.info(f"صيغة غير صحيحة للأمر !welcome من قبل {user.username}.")
            return

        welcome_message = parts[1]
        self.config["welcome_message"] = welcome_message
        self.save_config()
        await self.highrise.chat(f"تم تغيير رسالة الترحيب إلى '{welcome_message}'.")
        logger.info(f"قام {user.username} بتغيير رسالة الترحيب إلى '{welcome_message}'.")

    async def cmd_addadmin(self, user: User, parts: list):
        if not self.is_host(user.username):
            await self.highrise.chat("هذا الأمر متاح للـ Host فقط!")
            logger.info(f"حاول المستخدم {user.username} تنفيذ !addadmin لكن ليس لديه صلاحية.")
            return

        parts = [p.lower() for p in parts]
        if len(parts) != 2 or not parts[1].startswith("@"):
            await self.highrise.chat(self.get_message("invalid_format", format="!addadmin @username"))
            logger.info(f"صيغة غير صحيحة للأمر !addadmin من قبل {user.username}.")
            return

        target_username = parts[1][1:].lower()
        if target_username in self.config["admin_usernames"]:
            await self.highrise.chat(f"المستخدم @{target_username} مشرف بالفعل!")
            logger.info(f"طلب {user.username} إضافة {target_username} إلى المشرفين، لكنه مشرف بالفعل.")
            return

        try:
            self.config["admin_usernames"].append(target_username)
            self.save_config()
            await self.highrise.chat(f"تمت إضافة المستخدم @{target_username} إلى المشرفين بنجاح!")
            logger.info(f"تمت إضافة المستخدم {target_username} إلى المشرفين بواسطة {user.username}.")
        except Exception as e:
            await self.highrise.chat(f"خطأ في إضافة المشرف @{target_username}: {str(e)}")
            logger.error(f"خطأ في cmd_addadmin لـ {target_username}: {str(e)}")

    async def cmd_removeadmin(self, user: User, parts: list):
        if not self.is_host(user.username):
            await self.highrise.chat("هذا الأمر متاح للـ Host فقط!")
            logger.info(f"حاول المستخدم {user.username} تنفيذ !removeadmin لكن ليس لديه صلاحية.")
            return

        parts = [p.lower() for p in parts]
        if len(parts) != 2 or not parts[1].startswith("@"):
            await self.highrise.chat(self.get_message("invalid_format", format="!removeadmin @username"))
            logger.info(f"صيغة غير صحيحة للأمر !removeadmin من قبل {user.username}.")
            return

        target_username = parts[1][1:].lower()
        if target_username not in self.config["admin_usernames"]:
            await self.highrise.chat(f"المستخدم @{target_username} ليس في قائمة المشرفين!")
            logger.info(f"طلب {user.username} حذف {target_username} من المشرفين، لكنه غير موجود في القائمة.")
            return

        if self.is_host(target_username):
            await self.highrise.chat(f"❌ @{target_username} يملك رتبة Host ولا يمكن حذفه من المشرفين!")
            logger.info(f"تم رفض محاولة {user.username} حذف الـ Host {target_username} من المشرفين.")
            return

        if target_username == "rqtm":
            await self.highrise.chat("لا يمكنك حذف RQTM من المشرفين!")
            logger.info(f"تم رفض محاولة {user.username} حذف RQTM من المشرفين.")
            return

        try:
            self.config["admin_usernames"].remove(target_username)
            self.save_config()
            await self.highrise.chat(f"تم حذف المستخدم @{target_username} من المشرفين بنجاح!")
            logger.info(f"تم حذف المستخدم {target_username} من المشرفين بواسطة {user.username}.")
        except Exception as e:
            await self.highrise.chat(f"خطأ في حذف المشرف @{target_username}: {str(e)}")
            logger.error(f"خطأ في cmd_removeadmin لـ {target_username}: {str(e)}")

    async def cmd_addhost(self, user: User, parts: list):
        """⚠️ حصري: فقط المالك الأصلي للبوت (RQTM) يستطيع منح رتبة Host؛
        حتى بقية الـ Host لا يملكون صلاحية تنفيذ هذا الأمر."""
        if user.username.lower() != "rqtm":
            await self.highrise.chat("❌ وصول غير مصرح به!")
            logger.info(f"حاول المستخدم {user.username} تنفيذ !addhost لكن ليس لديه صلاحية.")
            return

        parts = [p.lower() for p in parts]
        if len(parts) != 2 or not parts[1].startswith("@"):
            await self.highrise.chat(self.get_message("invalid_format", format="!addhost @username"))
            logger.info(f"صيغة غير صحيحة للأمر !addhost من قبل {user.username}.")
            return

        target_username = parts[1][1:].lower()
        if target_username in self.config["host_usernames"]:
            await self.highrise.chat(f"المستخدم @{target_username} هو Host بالفعل!")
            return

        try:
            self.config["host_usernames"].append(target_username)
            if target_username not in self.config["admin_usernames"]:
                self.config["admin_usernames"].append(target_username)
            self.save_config()
            await self.highrise.chat(f"👑 أصبح المستخدم @{target_username} Host بنجاح!")
            logger.info(f"تم تعيين المستخدم {target_username} كـ Host بواسطة {user.username}.")
        except Exception as e:
            await self.highrise.chat(f"خطأ في إضافة الـ Host @{target_username}: {str(e)}")
            logger.error(f"خطأ في cmd_addhost لـ {target_username}: {str(e)}")

    async def cmd_removehost(self, user: User, parts: list):
        """⚠️ حصري: فقط المالك الأصلي للبوت (RQTM) يستطيع سحب رتبة Host."""
        if user.username.lower() != "rqtm":
            await self.highrise.chat("❌ وصول غير مصرح به!")
            logger.info(f"حاول المستخدم {user.username} تنفيذ !removehost لكن ليس لديه صلاحية.")
            return

        parts = [p.lower() for p in parts]
        if len(parts) != 2 or not parts[1].startswith("@"):
            await self.highrise.chat(self.get_message("invalid_format", format="!removehost @username"))
            logger.info(f"صيغة غير صحيحة للأمر !removehost من قبل {user.username}.")
            return

        target_username = parts[1][1:].lower()
        if target_username not in self.config["host_usernames"]:
            await self.highrise.chat(f"المستخدم @{target_username} ليس في قائمة الـ Host!")
            return

        if len(self.config["host_usernames"]) <= 1:
            await self.highrise.chat("❌ لا يمكن حذف آخر Host!")
            logger.info(f"تم رفض محاولة {user.username} حذف آخر Host ({target_username}).")
            return

        try:
            self.config["host_usernames"].remove(target_username)
            self.save_config()
            await self.highrise.chat(f"تم سحب رتبة Host من المستخدم @{target_username}.")
            logger.info(f"تم سحب رتبة Host من المستخدم {target_username} بواسطة {user.username}.")
        except Exception as e:
            await self.highrise.chat(f"خطأ في حذف الـ Host @{target_username}: {str(e)}")
            logger.error(f"خطأ في cmd_removehost لـ {target_username}: {str(e)}")

    async def cmd_listadd(self, user: User, parts: list):
        if user.username.lower() not in self.config["admin_usernames"]:
            await self.highrise.chat(self.get_message("no_permission"))
            logger.info(f"المستخدم {user.username} لا يملك الصلاحية لتنفيذ !listadd.")
            return

        try:
            if not self.config["admin_usernames"]:
                await self.highrise.chat(self.get_message("listadd_empty"))
                logger.info(f"قائمة المشرفين فارغة. الطلب من {user.username}.")
                return
            admin_list = [f"@{username}" for username in self.config["admin_usernames"]]
            await self.highrise.chat(self.get_message("listadd_success", count=len(admin_list), admin_list="\n".join(admin_list)))
            logger.info(f"طلب {user.username} قائمة المشرفين: {admin_list}")
        except Exception as e:
            await self.highrise.chat(f"خطأ في عرض قائمة المشرفين: {str(e)}")
            logger.error(f"خطأ في cmd_listadd: {str(e)}")

    async def cmd_freeze(self, user: User, parts: list):
        if user.username.lower() not in self.config["admin_usernames"]:
            await self.highrise.chat(self.get_message("no_permission"))
            logger.info(f"المستخدم {user.username} لا يملك الصلاحية لتنفيذ !freeze.")
            return

        parts = [p.lower() for p in parts]
        if len(parts) != 2 or not parts[1].startswith("@"):
            await self.highrise.chat(self.get_message("invalid_format", format="!freeze @username"))
            logger.info(f"صيغة غير صحيحة للأمر !freeze من قبل {user.username}.")
            return

        target_username = parts[1][1:].lower()
        target_user = self.active_users.get(target_username)
        if not target_user:
            await self.highrise.chat(self.get_message("user_not_found", username=target_username))
            logger.info(f"لم يتم العثور على المستخدم المستهدف {target_username} (طلب {user.username}).")
            return

        if target_username in self.frozen_users:
            await self.highrise.chat(f"المستخدم @{target_username} مجمّد بالفعل.")
            logger.info(f"طلب {user.username} تجميد {target_username}، لكنه مجمّد بالفعل.")
            return

        position = self.user_positions.get(target_username)
        if not position:
            await self.highrise.chat(f"موقع @{target_username} غير متاح.")
            logger.info(f"موقع {target_username} غير متاح للتجميد (طلب {user.username}).")
            return

        async def freeze_loop():
            try:
                while target_username in self.frozen_users:
                    if target_username not in self.active_users:
                        self.frozen_users.pop(target_username, None)
                        logger.info(f"أصبح المستخدم {target_username} غير متصل، تم إلغاء التجميد.")
                        break
                    await self.highrise.teleport(user_id=target_user.id, dest=position)
                    await sleep(1.0)
            except CancelledError:
                logger.info(f"تم إلغاء مهمة التجميد للمستخدم {target_username}.")
            except Exception as e:
                logger.error(f"خطأ في حلقة التجميد للمستخدم {target_username}: {e}")

        task = create_task(freeze_loop())
        self.frozen_users[target_username] = task
        await self.highrise.chat(self.get_message("freeze_success", username=target_username))
        logger.info(f"تم تجميد المستخدم {target_username} بواسطة {user.username}.")

    async def cmd_unfreeze(self, user: User, parts: list):
        if user.username.lower() not in self.config["admin_usernames"]:
            await self.highrise.chat(self.get_message("no_permission"))
            logger.info(f"المستخدم {user.username} لا يملك الصلاحية لتنفيذ !unfreeze.")
            return

        parts = [p.lower() for p in parts]
        if len(parts) != 2 or not parts[1].startswith("@"):
            await self.highrise.chat(self.get_message("invalid_format", format="!unfreeze @username"))
            logger.info(f"صيغة غير صحيحة للأمر !unfreeze من قبل {user.username}.")
            return

        target_username = parts[1][1:].lower()
        if target_username not in self.frozen_users:
            await self.highrise.chat(self.get_message("unfreeze_not_frozen", username=target_username))
            logger.info(f"طلب {user.username} إلغاء تجميد {target_username}، لكنه غير مجمّد.")
            return

        try:
            task = self.frozen_users.pop(target_username)
            task.cancel()
            await task
            await self.highrise.chat(self.get_message("unfreeze_success", username=target_username))
            logger.info(f"تم إلغاء تجميد المستخدم {target_username} بواسطة {user.username}.")
        except Exception as e:
            await self.highrise.chat(f"خطأ في إلغاء تجميد @{target_username}: {str(e)}")
            logger.error(f"خطأ في cmd_unfreeze لـ {target_username}: {str(e)}")

    async def cmd_party(self, user: User, parts: list):
        if user.username.lower() not in self.config["admin_usernames"]:
            await self.highrise.chat(self.get_message("no_permission"))
            logger.info(f"المستخدم {user.username} لا يملك الصلاحية لتنفيذ !party.")
            return

        parts = [p.lower() for p in parts]
        if len(parts) != 3 or (not parts[1].startswith("@") and parts[1] != "all") or not parts[2].isdigit():
            await self.highrise.chat(self.get_message("invalid_format", format="!party @username رقم أو !party all رقم"))
            logger.info(f"صيغة غير صحيحة للأمر !party من قبل {user.username}.")
            return

        dance_number = parts[2]
        if dance_number not in self.emotes:
            await self.highrise.chat(f"الرقصة رقم {dance_number} غير موجودة!")
            logger.info(f"الرقصة رقم {dance_number} غير صالحة (طلب {user.username}).")
            return

        emote = self.emotes[dance_number]
        duration = self.emote_durations.get(emote, 15.0)

        if parts[1] == "all":
            try:
                successful_dances = 0
                for username, target_user in self.active_users.items():
                    if target_user.id == self.user_id:
                        continue
                    if username not in self.active_users:
                        logger.info(f"أصبح المستخدم {username} غير متصل أثناء تشغيل الرقص.")
                        continue
                    await self.stop_dance(target_user)  # إيقاف الرقص السابق
                    self.party_dances[username] = (emote, False)  # False تعني رقصًا يمكن للمستخدم إيقافه
                    async def dance_loop(username=username, target_user=target_user):
                        # ملاحظة: تم تمرير username وtarget_user كقيم افتراضية
                        # حتى تحتفظ كل مهمة بقيمتها الخاصة وليس بالقيمة المشتركة للحلقة الخارجية
                        # (لتجنب خطأ late-binding closure في بايثون)
                        try:
                            while username in self.party_dances and self.party_dances[username][0] == emote:
                                if username not in self.active_users:
                                    self.party_dances.pop(username, None)
                                    logger.info(f"أصبح المستخدم {username} غير متصل، تم إيقاف الرقص.")
                                    break
                                await self.highrise.send_emote(emote, target_user.id)
                                await sleep(duration)
                        except CancelledError:
                            logger.info(f"تم إلغاء مهمة الرقص للمستخدم {username}.")
                        except Exception as e:
                            logger.error(f"خطأ في حلقة الرقص للمستخدم {username}: {e}")
                    task = create_task(dance_loop())
                    self.dance_tasks[username] = task
                    successful_dances += 1
                    await sleep(0.5)
                await self.highrise.chat(self.get_message("party_all_success", dance_number=dance_number, count=successful_dances))
                logger.info(f"تم تفعيل الرقصة رقم {dance_number} لـ {successful_dances} مستخدم بواسطة {user.username}.")
            except Exception as e:
                await self.highrise.chat(f"خطأ في تشغيل الرقص للجميع: {str(e)}")
                logger.error(f"خطأ في cmd_party all: {str(e)}")
        else:
            target_username = parts[1][1:].lower()
            target_user = self.active_users.get(target_username)
            if not target_user:
                await self.highrise.chat(self.get_message("user_not_found", username=target_username))
                logger.info(f"لم يتم العثور على المستخدم المستهدف {target_username} (طلب {user.username}).")
                return
            try:
                await self.stop_dance(target_user)  # إيقاف الرقص السابق
                self.party_dances[target_username] = (emote, True)  # True تعني رقصًا لا يمكن للمستخدم إيقافه
                async def dance_loop():
                    try:
                        while target_username in self.party_dances and self.party_dances[target_username][0] == emote:
                            if target_username not in self.active_users:
                                self.party_dances.pop(target_username, None)
                                logger.info(f"أصبح المستخدم {target_username} غير متصل، تم إيقاف الرقص.")
                                break
                            await self.highrise.send_emote(emote, target_user.id)
                            await sleep(duration)
                    except CancelledError:
                        logger.info(f"تم إلغاء مهمة الرقص للمستخدم {target_username}.")
                    except Exception as e:
                        logger.error(f"خطأ في حلقة الرقص للمستخدم {target_username}: {e}")
                task = create_task(dance_loop())
                self.dance_tasks[target_username] = task
                await self.highrise.chat(self.get_message("party_success", dance_number=dance_number, username=target_username))
                logger.info(f"تم تفعيل الرقصة رقم {dance_number} للمستخدم {target_username} بواسطة {user.username}.")
            except Exception as e:
                await self.highrise.chat(f"خطأ في تشغيل الرقص للمستخدم @{target_username}: {str(e)}")
                logger.error(f"خطأ في cmd_party لـ {target_username}: {str(e)}")

    async def cmd_partys(self, user: User, parts: list):
        if user.username.lower() not in self.config["admin_usernames"]:
            await self.highrise.chat(self.get_message("no_permission"))
            logger.info(f"المستخدم {user.username} لا يملك الصلاحية لتنفيذ !partys.")
            return

        parts = [p.lower() for p in parts]
        if len(parts) != 2 or not parts[1].startswith("@"):
            await self.highrise.chat(self.get_message("invalid_format", format="!partys @username"))
            logger.info(f"صيغة غير صحيحة للأمر !partys من قبل {user.username}.")
            return

        target_username = parts[1][1:].lower()
        if target_username not in self.party_dances:
            await self.highrise.chat(self.get_message("partys_not_dancing", username=target_username))
            logger.info(f"طلب {user.username} إيقاف رقص {target_username}، لكنه ليس في وضع الرقص الإجباري.")
            return

        try:
            await self.stop_dance(self.active_users[target_username])
            self.party_dances.pop(target_username, None)
            await self.highrise.chat(self.get_message("partys_success", username=target_username))
            logger.info(f"تم إيقاف الرقص الإجباري للمستخدم {target_username} بواسطة {user.username}.")
        except Exception as e:
            await self.highrise.chat(f"خطأ في إيقاف الرقص للمستخدم @{target_username}: {str(e)}")
            logger.error(f"خطأ في cmd_partys لـ {target_username}: {str(e)}")

    async def cmd_loopchat(self, user: User, parts: list):
        admins_lower = [admin.lower() for admin in self.config.get("admin_usernames", [])]
        if user.username.lower() not in admins_lower:
            await self.highrise.chat("❌ هذا الأمر مخصص لمشرفي البوت!")
            return

        if len(parts) < 2:
            await self.highrise.chat("⚠️ صيغة غير صحيحة! الاستخدام: !loopchat رسالتك")
            return

        # خذ كل النص بعد !loopchat
        loop_message = " ".join(parts[1:])
        
        # إذا كان loopchat يعمل حاليًا فألغِه
        if hasattr(self, 'loopchat_task') and self.loopchat_task:
            self.loopchat_task.cancel()
        
        await self.highrise.chat(f"✅ تم تفعيل وضع التكرار! الرسالة: {loop_message}")
        logger.info(f"تم تفعيل loopchat بواسطة {user.username}: {loop_message}")
        
        # بدء حلقة إرسال الرسائل
        async def loopchat_loop():
            try:
                while True:
                    await self.highrise.chat(loop_message)
                    await sleep(10.0)  # تكرار كل ١٠ ثوانٍ
            except CancelledError:
                logger.info("تم إلغاء loopchat.")
            except Exception as e:
                logger.error(f"خطأ في loopchat: {e}")
        
        self.loopchat_task = create_task(loopchat_loop())

    async def cmd_emotebot(self, user: User, parts: list):
        admins_lower = [admin.lower() for admin in self.config.get("admin_usernames", [])]
        if user.username.lower() not in admins_lower:
            await self.highrise.chat("❌ هذا الأمر مخصص لمشرفي البوت!")
            return

        if len(parts) < 2:
            await self.highrise.chat("⚠️ صيغة خاطئة! أدخل اسم الرقصة أو رقمها. مثال: !emotebot kpop")
            return

        input_emote = parts[1].strip().lower()

        # إيجاد الاسم الرسمي للرقصة من الرقم أو الاسم المستعار
        actual_emote_name = self.emotes.get(input_emote)
        
        if not actual_emote_name and input_emote in self.emotes.values():
            actual_emote_name = input_emote

        if not actual_emote_name:
            await self.highrise.chat("❌ لم يتم العثور على الرقصة أو الرقم في قائمة رقصات البوت!")
            return

        await self.highrise.chat(f"✅ تم ضبط رقصة البوت على التكرار الدائم (Loop): [{input_emote}]")
        logger.info(f"تم تغيير رقصة البوت المستمرة إلى {actual_emote_name} بواسطة {user.username}.")
        self.start_bot_emote_loop(actual_emote_name)

async def handle_ping(request):
    return aiohttp.web.Response(text="Bot is Alive!")

async def start_background_web_server():
    try:
        app = aiohttp.web.Application()
        app.router.add_get('/', handle_ping)
        runner = aiohttp.web.AppRunner(app)
        await runner.setup()
        port = int(os.getenv("PORT", 8080))
        site = aiohttp.web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        logger.info(f"تم تشغيل خادم الويب (Keep-Alive) على المنفذ {port}.")
    except Exception as e:
        logger.error(f"خطأ في تشغيل خادم الويب في الخلفية: {e}")
    
# ٢. الدالة الرئيسية لتشغيل البوت (نسخة مقاومة للأعطال ومزودة بمعالجة أخطاء المهام)
async def main():
    import os
    import asyncio
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer
    
    logger.info("جارٍ محاولة تحميل متغيرات البيئة...")
    room_id = os.getenv("ROOM_ID", ROOM_ID)
    api_token = os.getenv("API_TOKEN", API_TOKEN)
    
    if not room_id or not api_token:
        logger.error("لم يتم تعيين ROOM_ID أو API_TOKEN.")
        return
    
    logger.info(f"ROOM_ID: {room_id}")
    logger.info(f"API_TOKEN: {api_token}")

    # بنية خادم ويب داخلي وخفيف في بايثون
    class PingHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"Bot is Alive!")
        def log_message(self, format, *args):
            return

    def run_web_server():
        try:
            port = int(os.getenv("PORT", 8080))
            server = HTTPServer(('0.0.0.0', port), PingHandler)
            logger.info(f"تم تشغيل خادم الويب (Keep-Alive) على المنفذ {port}.")
            server.serve_forever()
        except Exception as e:
            logger.error(f"خطأ في تشغيل خادم الويب في الخلفية: {e}")

    # تشغيل خادم الويب في خيط منفصل تمامًا لتجنب التجمّد
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()

    # إعداد معالج الأخطاء العام لـ asyncio حتى لا تتسبب أي مهمة في تعطيل البوت
    def handle_exception(loop, context):
        msg = context.get("exception", context["message"])
        logger.error(f"فشلت مهمة في الخلفية لكن تمت السيطرة عليها: {msg}")

    try:
        loop = asyncio.get_running_loop()
        loop.set_exception_handler(handle_exception)
    except Exception as le:
        logger.error(f"خطأ في إعداد exception handler: {le}")

    max_reconnect_attempts = 10
    attempt = 0
    while attempt < max_reconnect_attempts:
        try:
            room_id = os.environ.get("ROOM_ID", room_id)
            bot_instance = AdvancedBot()
            bot_def = BotDefinition(room_id=room_id, api_token=api_token, bot=bot_instance)
            logger.info(f"جارٍ محاولة الاتصال بسيرفر Highrise... الغرفة: {room_id}")
            from highrise.__main__ import main as highrise_main
            await highrise_main([bot_def])
        except Exception as e:
            logger.error(f"انقطع اتصال WebSocket أو حدث خطأ: {e}")
            try:
                await bot_instance.cleanup_tasks()
            except Exception:
                pass
            attempt += 1
            logger.info(f"في انتظار إعادة الاتصال... المحاولة {attempt} من {max_reconnect_attempts}")
            await asyncio.sleep(6)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
