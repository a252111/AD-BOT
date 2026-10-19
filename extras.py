# -*- coding: utf-8 -*-
"""
extras.py — الوحدة اللي يستوردها adbot.py

تحتوي على:
  - cfg / safe_event / atomic_write_json  (دوال مساعدة)
  - ExtrasMixin:
      * المساعدة بالهمس والخاص (!help)
      * دعوات الزوار (visitors.json)
      * الألعاب: !scramble !speed !mathal !guess/!g !rps !dice !luck !love
"""

import asyncio
import functools
import hashlib
import inspect
import json
import logging
import os
import random
import re
import time
from asyncio import CancelledError, create_task, sleep
from datetime import datetime, timezone

import aiohttp

import settings as _settings
from help_texts import HELP_MENU, HELP_PAGES, HELP_ALIASES, HELP_TRIGGERS

logger = logging.getLogger("AdvancedBot")


# =====================================================================
#  دوال مساعدة
# =====================================================================
def cfg(name, default=None):
    """يقرأ إعداداً من settings.py، ولو ماكو يرجع القيمة الافتراضية.
    ممكن تتجاوزه بمتغير بيئة بنفس الاسم (مثلاً VISITOR_INVITES_ENABLED=0)."""
    env = os.getenv(name)
    if env is not None:
        if isinstance(default, bool):
            return env.strip().lower() in ("1", "true", "yes", "on", "نعم")
        if isinstance(default, int) and not isinstance(default, bool):
            try:
                return int(env)
            except ValueError:
                return default
        return env
    return getattr(_settings, name, default)


def safe_event(func):
    """يغلّف أحداث البوت حتى لو صار خطأ بوحدة منها ما يوقع الاتصال."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except CancelledError:
            raise
        except Exception as e:
            logger.error(f"خطأ في الحدث {func.__name__}: {e!r}", exc_info=True)
    return wrapper


def atomic_write_json(path, data):
    """كتابة JSON بشكل آمن (ملف مؤقت ثم استبدال) حتى ما يتلف الملف عند الانقطاع."""
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.flush()
        try:
            os.fsync(f.fileno())
        except OSError:
            pass
    os.replace(tmp, path)


_DIACRITICS = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u0640]")


def _norm(text):
    """تطبيع النص العربي/الإنجليزي للمقارنة (تشكيل، ألف، ياء، تاء مربوطة، مسافات)."""
    t = (text or "").strip().lower()
    t = _DIACRITICS.sub("", t)
    t = t.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    t = t.replace("ى", "ي").replace("ة", "ه").replace("ؤ", "و").replace("ئ", "ي")
    t = re.sub(r"[^\w\s]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


# =====================================================================
#  محتوى الألعاب (يمكن تغييره من settings.py بنفس الأسماء)
# =====================================================================
DEFAULT_SCRAMBLE_WORDS = [
    "مدرسة", "حديقة", "سيارة", "طائرة", "مكتبة", "برتقال", "تفاحة", "كمبيوتر",
    "هاتف", "شجرة", "قطار", "مستشفى", "صحراء", "بحيرة", "فراشة", "دجاجة",
    "كتاب", "مطبخ", "نافذة", "ملعب", "عصفور", "زرافة", "سلحفاة", "ثعلب",
    "مدينة", "شمعة", "ساعة", "مفتاح", "حقيبة", "سفينة", "جزيرة", "بركان",
    "قهوة", "شوكولاتة", "بطيخ", "موزة", "دراجة", "مظلة", "قمر", "نجمة",
]

DEFAULT_SPEED_PHRASES = [
    "سبحان الله وبحمده",
    "الصبر مفتاح الفرج",
    "هايرايز احلى لعبة",
    "نورتوا الغرفة",
    "اسرع واحد يفوز",
    "الوقت من ذهب",
    "تحيا الغرفة",
    "ما شاء الله تبارك الله",
    "صباح الخير والسرور",
    "مساء النور والبهجة",
    "الف مبروك للفايز",
    "لا تنسى تبتسم",
    "العب بروح رياضية",
    "اكتب هذي الجملة بسرعة",
    "كل عام وانتم بخير",
]

DEFAULT_MATHAL = [
    ("العجلة من الشيطان والتأني من ___", "الرحمن"),
    ("الصديق وقت ___", "الضيق"),
    ("من جد ___", "وجد"),
    ("الوقت كالسيف إن لم تقطعه ___", "قطعك"),
    ("اطلبوا العلم من المهد إلى ___", "اللحد"),
    ("في الاتحاد ___", "قوة"),
    ("العقل السليم في الجسم ___", "السليم"),
    ("الحاجة أم ___", "الاختراع"),
    ("الجار قبل ___", "الدار"),
    ("درهم وقاية خير من قنطار ___", "علاج"),
    ("ما حك جلدك مثل ___", "ظفرك"),
    ("من زرع ___", "حصد"),
    ("الطيور على أشكالها ___", "تقع"),
    ("إذا كان الكلام من فضة فالسكوت من ___", "ذهب"),
    ("القناعة كنز لا ___", "يفنى"),
    ("رب أخ لك لم تلده ___", "أمك"),
    ("خير الكلام ما قل و___", "دل"),
    ("الصبر مفتاح ___", "الفرج"),
    ("لكل مجتهد ___", "نصيب"),
    ("الحلم سيد ___", "الأخلاق"),
]

RPS_ALIASES = {
    "حجر": "rock", "حجره": "rock", "rock": "rock", "r": "rock", "🪨": "rock", "✊": "rock",
    "ورقة": "paper", "ورقه": "paper", "paper": "paper", "p": "paper", "📄": "paper", "✋": "paper",
    "مقص": "scissors", "scissors": "scissors", "s": "scissors", "✂️": "scissors", "✌️": "scissors",
}
RPS_LABEL = {"rock": "حجر 🪨", "paper": "ورقة 📄", "scissors": "مقص ✂️"}
RPS_BEATS = {"rock": "scissors", "paper": "rock", "scissors": "paper"}

LUCK_LINES = [
    "🍀 حظك اليوم ممتاز! كل شي يمشي لصالحك",
    "🌟 يوم حلو ينتظرك، لا تخلي الفرصة تفوتك",
    "😎 حظك عادي اليوم، بس ابتسامتك تفرق",
    "🌧️ حظك تعبان شوي، خذ الأمور بهدوء",
    "🔥 طاقتك عالية اليوم، جرّب شي جديد",
    "💰 يوم مناسب للمفاجآت الحلوة",
    "🎯 ركّز بهدفك اليوم وراح توصل",
    "☕ خذ قهوتك وارتاح، اليوم يومك",
]


class ExtrasMixin:
    """ميزات إضافية للبوت. تستعمل خصائص AdvancedBot (config, highrise, active_users...)."""

    # ------------------------------------------------------------------
    #  تهيئة
    # ------------------------------------------------------------------
    def init_extras(self):
        self._bg_tasks = set()
        self.guess = None
        self.game_task = None
        self.game_current = None
        self.visitor_task = None
        self._hinted = set()
        self._game_cd = {}
        self.visitors = {}
        self.room_id = getattr(self, "room_id", None)
        self._load_visitors()

        extra = {
            "!scramble": self.cmd_scramble,
            "!speed": self.cmd_speed,
            "!mathal": self.cmd_mathal,
            "!guess": self.cmd_guess,
            "!g": self.cmd_g,
            "!rps": self.cmd_rps,
            "!dice": self.cmd_dice,
            "!luck": self.cmd_luck,
            "!love": self.cmd_love,
            # أسماء بديلة
            "!مساعدة": self.cmd_help,
            "!menu": self.cmd_help,
            "!اوامر": self.cmd_help,
            "!الاوامر": self.cmd_help,
            "!تخمين": self.cmd_guess,
            "!حظ": self.cmd_luck,
            "!حب": self.cmd_love,
        }
        for name, handler in extra.items():
            self.commands.setdefault(name, handler)

    # ------------------------------------------------------------------
    #  مهام الخلفية وتشغيل الأوامر
    # ------------------------------------------------------------------
    def spawn(self, coro):
        task = create_task(coro)
        self._bg_tasks.add(task)
        task.add_done_callback(self._bg_tasks.discard)
        return task

    async def run_command(self, cmd, handler, user, parts):
        try:
            await handler(user, parts)
        except CancelledError:
            raise
        except Exception as e:
            logger.error(f"خطأ في تنفيذ الأمر {cmd} من {getattr(user, 'username', '?')}: {e!r}", exc_info=True)

    # ------------------------------------------------------------------
    #  أدوات صغيرة
    # ------------------------------------------------------------------
    def _is_admin(self, user):
        return user.username.lower() in self.config.get("admin_usernames", [])

    def _busy(self):
        if self.quiz_task and not self.quiz_task.done():
            return "⚠️ المسابقة شغالة هسه، اصبروا لين تخلص!"
        if self.mafia or (self.mafia_task and not self.mafia_task.done()):
            return "⚠️ لعبة المافيا شغالة هسه، اصبروا لين تخلص!"
        if self.guess:
            return "⚠️ لعبة خمّن الرقم شغالة هسه!"
        if self.game_task and not self.game_task.done():
            return "⚠️ فيه لعبة شغالة هسه، اصبروا لين تخلص!"
        return None

    def _cooldown_ok(self, user, game):
        now = time.monotonic()
        key = (user.username.lower(), game)
        wait = cfg("GAME_COOLDOWN", 5)
        last = self._game_cd.get(key, 0)
        if now - last < wait:
            return False
        self._game_cd[key] = now
        return True

    def add_points(self, username, pts):
        key = username.lower()
        entry = self.quiz_scores.setdefault(key, {"name": username, "points": 0})
        entry["name"] = username
        entry["points"] += pts
        try:
            self.save_quiz_scores()
        except Exception as e:
            logger.error(f"تعذر حفظ النقاط: {e}")

    @staticmethod
    def _chunks(lines, limit=220):
        """يقسّم قائمة أسطر لرسائل أقصر من limit حرف."""
        out, cur = [], ""
        for line in lines:
            line = str(line)
            while len(line) > limit:
                if cur:
                    out.append(cur)
                    cur = ""
                out.append(line[:limit])
                line = line[limit:]
            if len(cur) + len(line) + 1 > limit and cur:
                out.append(cur)
                cur = line
            else:
                cur = f"{cur}\n{line}" if cur else line
        if cur:
            out.append(cur)
        return out

    async def _whisper_lines(self, user_id, lines):
        for chunk in self._chunks(lines):
            await self.highrise.send_whisper(user_id, chunk)
            await sleep(0.4)

    async def _dm(self, conversation_id, text, invite=False):
        """يرسل رسالة خاصة. يتأقلم مع اسم باراميتر النوع حسب نسخة الـ SDK."""
        kwargs = {}
        if invite:
            try:
                params = inspect.signature(self.highrise.send_message).parameters
            except (TypeError, ValueError):
                params = {}
            type_key = "message_type" if "message_type" in params else "type"
            kwargs[type_key] = "invite"
            kwargs["room_id"] = self.room_id
        return await self.highrise.send_message(conversation_id, text, **kwargs)

    # ------------------------------------------------------------------
    #  المساعدة (!help) بالهمس والخاص
    # ------------------------------------------------------------------
    def _help_page_key(self, text):
        t = (text or "").strip().lower()
        t = HELP_ALIASES.get(t, t)
        return t if t in HELP_PAGES else None

    def _is_help_trigger(self, text):
        return (text or "").strip().lower() in HELP_TRIGGERS

    async def cmd_help(self, user, parts):
        page = self._help_page_key(parts[1]) if len(parts) > 1 else None
        lines = HELP_PAGES[page] if page else HELP_MENU
        try:
            await self._whisper_lines(user.id, lines)
            if len(parts) <= 1:
                await self.highrise.chat(f"📩 @{user.username} أرسلت لك قائمة المساعدة بالهمس، شيّك الهمس!")
        except Exception as e:
            logger.error(f"تعذر إرسال المساعدة بالهمس إلى {user.username}: {e}")
            await self.highrise.chat(f"@{user.username} ما قدرت أهمس لك، راسلني خاص واكتب !help")
        logger.info(f"طلب {user.username} المساعدة.")

    async def on_whisper(self, user, message):
        """همس للبوت: !help أو 1/2/3 لفتح صفحات المساعدة."""
        try:
            if user.id == self.user_id:
                return
            text = (message or "").strip()
            page = self._help_page_key(text)
            if page:
                await self._whisper_lines(user.id, HELP_PAGES[page])
            elif self._is_help_trigger(text):
                await self._whisper_lines(user.id, HELP_MENU)
        except Exception as e:
            logger.error(f"خطأ في on_whisper: {e!r}", exc_info=True)

    async def on_message(self, user_id, conversation_id, is_new_conversation):
        """رسالة خاصة (Inbox): نسجل المحادثة للدعوات ونرد بالمساعدة أو بالتعريف بالبوت."""
        try:
            if user_id == self.user_id:
                return

            # 1) اقرأ آخر رسالة من المستخدم
            text = ""
            try:
                resp = await self.highrise.get_messages(conversation_id)
                msgs = getattr(resp, "messages", None) or []
                for m in msgs:
                    if getattr(m, "sender_id", None) != self.user_id:
                        text = getattr(m, "content", "") or ""
                        break
            except Exception as e:
                logger.warning(f"تعذر قراءة الرسالة الخاصة: {e}")

            # 2) سجّل معرّف المحادثة (يسمح بإرسال الدعوات لاحقاً)
            await self._remember_conversation(user_id, conversation_id)

            # 3) رد
            page = self._help_page_key(text)
            if page:
                for chunk in self._chunks(HELP_PAGES[page]):
                    await self._dm(conversation_id, chunk)
                return
            if self._is_help_trigger(text):
                for chunk in self._chunks(HELP_MENU):
                    await self._dm(conversation_id, chunk)
                return
            if is_new_conversation or not text:
                await self._dm(conversation_id, self._auto_reply_text())
        except Exception as e:
            logger.error(f"خطأ في on_message: {e!r}", exc_info=True)

    def _auto_reply_text(self):
        return (
            "أهلاً بك يا عزيزي! ❤️\n\n"
            "🤖 أنا بوت متطور لإدارة الغرفة: رقصات، ألعاب جماعية، مسابقات ومافيا!\n"
            "📩 اكتب !help لعرض قائمة المساعدة.\n\n"
            "🤝 لاستئجار البوت لغرفتك راسل: @RQTM"
        )

    # ------------------------------------------------------------------
    #  دعوات الزوار
    # ------------------------------------------------------------------
    def _visitor_path(self):
        return cfg("VISITOR_FILE", "visitors.json")

    def _load_visitors(self):
        path = self._visitor_path()
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    self.visitors = data
        except Exception as e:
            logger.error(f"تعذر تحميل ملف الزوار: {e}")
            self.visitors = {}

    def save_visitors(self):
        try:
            atomic_write_json(self._visitor_path(), self.visitors)
        except Exception as e:
            logger.error(f"تعذر حفظ ملف الزوار: {e}")

    def register_visitor(self, user, save=True):
        try:
            if user.id == self.user_id:
                return
            v = self.visitors.get(user.id)
            is_new = v is None
            if is_new:
                v = {
                    "username": user.username,
                    "first_seen": int(time.time()),
                    "conversation_id": None,
                    "last_invited": 0,
                    "hinted_at": 0,
                }
                self.visitors[user.id] = v
            v["username"] = user.username
            if is_new and save:
                self.save_visitors()
        except Exception as e:
            logger.error(f"خطأ في تسجيل الزائر: {e}")

    async def _remember_conversation(self, user_id, conversation_id):
        v = self.visitors.get(user_id)
        if v is None:
            username = None
            for u in self.active_users.values():
                if getattr(u, "id", None) == user_id:
                    username = u.username
                    break
            if not username:
                info = await self._web_user(user_id)
                username = (info or {}).get("username") or user_id
            v = {"username": username, "first_seen": int(time.time()),
                 "conversation_id": None, "last_invited": 0, "hinted_at": 0}
            self.visitors[user_id] = v
        v["conversation_id"] = conversation_id
        self.save_visitors()

    async def send_join_hint(self, user):
        """يهمس للزائر الجديد حتى يراسل البوت (شرط هايرايز لإرسال دعوات خاصة)."""
        try:
            if not cfg("VISITOR_INVITES_ENABLED", True) or user.id == self.user_id:
                return
            v = self.visitors.get(user.id) or {}
            if v.get("conversation_id") or user.id in self._hinted:
                return
            if time.time() - v.get("hinted_at", 0) < 86400:
                return
            self._hinted.add(user.id)
            await self.highrise.send_whisper(user.id, cfg("VISITOR_JOIN_HINT", ""))
            if user.id in self.visitors:
                self.visitors[user.id]["hinted_at"] = int(time.time())
                self.save_visitors()
        except Exception as e:
            logger.warning(f"تعذر إرسال تلميح الانضمام: {e}")

    async def _web_user(self, user_id):
        url = f"https://webapi.highrise.game/users/{user_id}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as r:
                    if r.status != 200:
                        return None
                    data = await r.json()
                    return data.get("user") or None
        except Exception:
            return None

    @staticmethod
    def _parse_time(value):
        if not value:
            return None
        try:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            return None

    async def visitor_invite_loop(self):
        interval = cfg("VISITOR_CHECK_INTERVAL", 600)
        window_min = cfg("VISITOR_ACTIVE_WINDOW_MIN", 30)
        max_per_cycle = cfg("VISITOR_MAX_PER_CYCLE", 20)
        try:
            while True:
                await sleep(interval)
                try:
                    await self._visitor_cycle(window_min, max_per_cycle)
                except CancelledError:
                    raise
                except Exception as e:
                    logger.error(f"خطأ في دورة دعوات الزوار: {e!r}", exc_info=True)
        except CancelledError:
            logger.info("تم إلغاء مهمة دعوات الزوار.")

    async def _visitor_cycle(self, window_min, max_per_cycle):
        now = time.time()
        in_room_ids = {getattr(u, "id", None) for u in self.active_users.values()}
        candidates = [
            (uid, v) for uid, v in self.visitors.items()
            if v.get("conversation_id")
            and uid not in in_room_ids
            and now - v.get("last_invited", 0) >= 86400
        ]
        random.shuffle(candidates)
        sent = 0
        for uid, v in candidates[:max_per_cycle]:
            info = await self._web_user(uid)
            last = self._parse_time((info or {}).get("last_online_in"))
            if not last:
                continue
            age_min = (datetime.now(timezone.utc) - last).total_seconds() / 60
            if age_min > window_min:
                continue
            try:
                text = cfg("VISITOR_INVITE_TEXT", "").format(username=v.get("username", ""))
                await self._dm(v["conversation_id"], text, invite=True)
                v["last_invited"] = int(now)
                sent += 1
            except Exception as e:
                logger.warning(f"تعذر إرسال دعوة إلى {v.get('username')}: {e}")
            await sleep(1.5)
        if sent:
            self.save_visitors()
            logger.info(f"تم إرسال {sent} دعوة زوار.")

    # ------------------------------------------------------------------
    #  ألعاب الجولات: !scramble !speed !mathal
    # ------------------------------------------------------------------
    def _parse_rounds(self, parts):
        rounds = cfg("GAME_DEFAULT_ROUNDS", 5)
        if len(parts) > 1:
            try:
                rounds = int(parts[1])
            except ValueError:
                return None
        return max(1, min(rounds, 20))

    async def _start_rounds(self, user, parts, kind):
        if not self._is_admin(user):
            await self.highrise.chat(self.get_message("no_permission"))
            return
        busy = self._busy()
        if busy:
            await self.highrise.chat(busy)
            return
        rounds = self._parse_rounds(parts)
        if rounds is None:
            await self.highrise.chat(self.get_message("invalid_format", format=f"!{kind} [العدد]"))
            return
        self.game_task = create_task(self._run_rounds(kind, rounds))
        logger.info(f"بدأ {user.username} لعبة {kind} من {rounds} جولات.")

    async def cmd_scramble(self, user, parts):
        await self._start_rounds(user, parts, "scramble")

    async def cmd_speed(self, user, parts):
        await self._start_rounds(user, parts, "speed")

    async def cmd_mathal(self, user, parts):
        await self._start_rounds(user, parts, "mathal")

    def _make_round(self, kind, used):
        if kind == "scramble":
            words = list(cfg("SCRAMBLE_WORDS", DEFAULT_SCRAMBLE_WORDS))
            pool = [w for w in words if w not in used] or words
            word = random.choice(pool)
            used.add(word)
            letters = list(word)
            scrambled = word
            for _ in range(10):
                random.shuffle(letters)
                scrambled = "".join(letters)
                if scrambled != word:
                    break
            shown = " ".join(letters)
            return (f"🔀 رتّب الحروف لتكوين كلمة: {shown}", {_norm(word)}, word,
                    cfg("SCRAMBLE_TIMEOUT", 30))
        if kind == "speed":
            phrases = list(cfg("SPEED_PHRASES", DEFAULT_SPEED_PHRASES))
            pool = [p for p in phrases if p not in used] or phrases
            phrase = random.choice(pool)
            used.add(phrase)
            return (f"⚡ أسرع واحد يكتب: {phrase}", {_norm(phrase)}, phrase,
                    cfg("SPEED_TIMEOUT", 15))
        items = list(cfg("MATHAL_ITEMS", DEFAULT_MATHAL))
        pool = [i for i in items if i[0] not in used] or items
        prompt, ans = random.choice(pool)
        used.add(prompt)
        return (f"📜 أكمل المثل: {prompt}", {_norm(ans)}, ans, cfg("MATHAL_TIMEOUT", 25))

    async def _run_rounds(self, kind, rounds):
        titles = {"scramble": "🔀 الكلمة المبعثرة", "speed": "⚡ الأسرع بالكتابة", "mathal": "📜 أكمل المثل"}
        scores = {}
        used = set()
        me = asyncio.current_task()
        try:
            await self.highrise.chat(f"{titles[kind]} — {rounds} جولات! جاوبوا بالشات 🎮")
            await sleep(3)
            for i in range(1, rounds + 1):
                question, answers, shown_answer, timeout = self._make_round(kind, used)
                ev = asyncio.Event()
                self.game_current = {"answers": answers, "winner": None, "event": ev}
                await self.highrise.chat(f"[{i}/{rounds}] {question}")
                try:
                    await asyncio.wait_for(ev.wait(), timeout=timeout)
                except asyncio.TimeoutError:
                    pass
                cur, self.game_current = self.game_current, None
                if cur and cur["winner"]:
                    w = cur["winner"]
                    scores[w] = scores.get(w, 0) + 1
                    await self.highrise.chat(f"🎉 @{w} جاوب صح! الجواب: {shown_answer}")
                else:
                    await self.highrise.chat(f"⏰ خلص الوقت! الجواب: {shown_answer}")
                await sleep(3)
            if scores:
                ranking = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
                text = " | ".join(f"@{n}: {p}" for n, p in ranking[:5])
                await self.highrise.chat(f"🏆 النتيجة النهائية: {text}")
            else:
                await self.highrise.chat("🏁 خلصت اللعبة ومحد جاوب! الله يعوضكم 😅")
        except CancelledError:
            raise
        finally:
            self.game_current = None
            if self.game_task is me:
                self.game_task = None

    async def game_on_chat(self, user, msg):
        """يفحص جواب لعبة الجولات. يرجع True إذا كان الجواب صحيح."""
        cur = self.game_current
        if not cur or cur["winner"] is not None or msg.startswith("!"):
            return False
        if _norm(msg) in cur["answers"]:
            cur["winner"] = user.username
            self.add_points(user.username, 1)
            cur["event"].set()
            return True
        return False

    # ------------------------------------------------------------------
    #  لعبة خمّن الرقم: !guess (يبدأها المشرف) و !g رقم
    # ------------------------------------------------------------------
    async def cmd_guess(self, user, parts):
        if len(parts) > 1 and parts[1].lstrip("-").isdigit():
            await self.cmd_g(user, parts)
            return
        if not self._is_admin(user):
            await self.highrise.chat(self.get_message("no_permission"))
            return
        busy = self._busy()
        if busy:
            await self.highrise.chat(busy)
            return
        top = cfg("GUESS_MAX", 100)
        secs = cfg("GUESS_TIME", 120)
        number = random.randint(1, top)
        self.guess = {"number": number, "task": None, "tries": {}}
        self.guess["task"] = create_task(self._guess_timer(secs))
        await self.highrise.chat(
            f"🔢 لعبة خمّن الرقم! أنا مفكر برقم من 1 إلى {top}. "
            f"جاوبوا بـ !g رقم — عندكم {secs} ثانية ⏳"
        )
        logger.info(f"بدأ {user.username} لعبة خمّن الرقم (الرقم {number}).")

    async def _guess_timer(self, secs):
        try:
            await sleep(secs)
            g = self.guess
            if g:
                self.guess = None
                await self.highrise.chat(f"⏰ خلص الوقت! الرقم كان {g['number']} 😅")
        except CancelledError:
            pass

    async def cmd_g(self, user, parts):
        g = self.guess
        if not g:
            return
        if len(parts) < 2 or not parts[1].lstrip("-").isdigit():
            await self.highrise.chat(self.get_message("invalid_format", format="!g رقم"))
            return
        n = int(parts[1])
        key = user.username.lower()
        g["tries"][key] = g["tries"].get(key, 0) + 1
        if n == g["number"]:
            tries = g["tries"][key]
            task = g.get("task")
            self.guess = None
            if task and task is not asyncio.current_task() and not task.done():
                task.cancel()
            pts = cfg("GUESS_WIN_POINTS", 3)
            self.add_points(user.username, pts)
            await self.highrise.chat(
                f"🎉 @{user.username} خمّن الرقم {n} صح بـ {tries} محاولة! +{pts} نقطة 🏆"
            )
        elif n < g["number"]:
            await self.highrise.chat(f"⬆️ @{user.username} الرقم أكبر من {n}")
        else:
            await self.highrise.chat(f"⬇️ @{user.username} الرقم أصغر من {n}")

    def stop_guess(self):
        """يوقف لعبة خمّن الرقم ولعبة الجولات. يرجع True إذا أوقف شي فعلاً."""
        stopped = False
        g = self.guess
        if g:
            task = g.get("task")
            if task and not task.done():
                task.cancel()
            self.guess = None
            stopped = True
        gt = self.game_task
        if gt and not gt.done():
            gt.cancel()
            stopped = True
        self.game_task = None
        self.game_current = None
        return stopped

    # ------------------------------------------------------------------
    #  ألعاب فردية: !rps !dice !luck !love
    # ------------------------------------------------------------------
    async def cmd_rps(self, user, parts):
        if not self._cooldown_ok(user, "rps"):
            return
        if len(parts) < 2 or parts[1].lower() not in RPS_ALIASES:
            await self.highrise.chat("✊ اكتب: !rps حجر | ورقة | مقص")
            return
        mine = RPS_ALIASES[parts[1].lower()]
        bot = random.choice(list(RPS_BEATS))
        if mine == bot:
            result = "تعادل 🤝"
        elif RPS_BEATS[mine] == bot:
            result = "فزت! 🎉"
        else:
            result = "خسرت 😅 فاز البوت"
        await self.highrise.chat(
            f"@{user.username} اخترت {RPS_LABEL[mine]} | البوت اختار {RPS_LABEL[bot]} — {result}"
        )

    async def cmd_dice(self, user, parts):
        if not self._cooldown_ok(user, "dice"):
            return
        a, b = random.randint(1, 6), random.randint(1, 6)
        if a > b:
            result = "فزت! 🎉"
        elif a < b:
            result = "خسرت 😅"
        else:
            result = "تعادل 🤝"
        await self.highrise.chat(f"🎲 @{user.username} نردك: {a} | نرد البوت: {b} — {result}")

    async def cmd_luck(self, user, parts):
        if not self._cooldown_ok(user, "luck"):
            return
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        seed = int(hashlib.sha256(f"{user.id}{today}".encode()).hexdigest(), 16)
        rnd = random.Random(seed)
        pct = rnd.randint(1, 100)
        line = rnd.choice(LUCK_LINES)
        await self.highrise.chat(f"🍀 @{user.username} حظك اليوم {pct}% — {line}")

    async def cmd_love(self, user, parts):
        if not self._cooldown_ok(user, "love"):
            return
        if len(parts) < 2:
            await self.highrise.chat("💘 اكتب: !love @اسم")
            return
        target = parts[1].lstrip("@")
        a, b = sorted([user.username.lower(), target.lower()])
        pct = int(hashlib.sha256(f"{a}|{b}".encode()).hexdigest(), 16) % 101
        if pct >= 80:
            note = "حب من النظرة الأولى 😍"
        elif pct >= 50:
            note = "فيه كيمياء حلوة 💕"
        elif pct >= 25:
            note = "صداقة جميلة 🙂"
        else:
            note = "الله يهديكم 😂"
        await self.highrise.chat(f"💘 نسبة الحب بين @{user.username} و @{target}: {pct}% — {note}")
