# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════╗
║          🤖 بوت تليجرام الاحترافي المتكامل V3.0          ║
║         Telegram Professional Bot - Full Featured        ║
╚══════════════════════════════════════════════════════════╝
"""

import os
import re
import sys
import json
import time
import random
import string
import asyncio
import logging
import hashlib
import threading
import subprocess
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional, Tuple, List, Dict, Any
from urllib.parse import urlparse

# Telegram imports
from telegram import (
    Update, Bot, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton, ChatPermissions, ChatMember,
    MessageEntity, InputMediaPhoto, InputMediaVideo, InputMediaDocument,
    InlineQueryResultArticle, InputTextMessageContent
)
from telegram.constants import ParseMode, ChatAction, ChatType
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler,
    CallbackQueryHandler, InlineQueryHandler, ChatMemberHandler,
    ConversationHandler, filters
)
from telegram.error import TelegramError, Forbidden, BadRequest

# =============================================
# ⚙️ CONFIGURATION & SETTINGS
# =============================================
class Config:
    """Central configuration class"""
    # Bot Core
    TOKEN = "8702640145:AAHyLv6r3xfyf9x-dptwim6_BrnJSbWYpmY"
    BOT_NAME = "الأسطورة"
    BOT_VERSION = "3.0.0"
    BOT_CREATOR = "@ZADC_Team"
    BOT_CHANNEL = "@ZADC_Channel"
    
    # Admin Settings
    ADMIN_PASS = "0658"
    OWNER_IDS = [123456789, 987654321]  # Can add multiple owners
    
    # File System
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    LOGS_DIR = os.path.join(BASE_DIR, "logs")
    TEMP_DIR = os.path.join(BASE_DIR, "temp")
    USERS_FILE = os.path.join(DATA_DIR, "users.json")
    GROUPS_FILE = os.path.join(DATA_DIR, "groups.json")
    BANS_FILE = os.path.join(DATA_DIR, "bans.json")
    STATS_FILE = os.path.join(DATA_DIR, "stats.json")
    SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
    
    # Limits
    MAX_VIDEO_SIZE = 200 * 1024 * 1024  # 200MB
    MAX_AUDIO_SIZE = 100 * 1024 * 1024  # 100MB
    MAX_MESSAGE_LENGTH = 4096
    RATE_LIMIT_SECONDS = 2
    
    # Emojis & Decorations
    EMOJIS = {
        'success': '✅', 'error': '❌', 'warning': '⚠️', 'info': 'ℹ️',
        'star': '⭐', 'crown': '👑', 'lock': '🔒', 'key': '🔑',
        'rocket': '🚀', 'fire': '🔥', 'heart': '❤️', 'broken': '💔',
        'robot': '🤖', 'ghost': '👻', 'alien': '👽', 'devil': '😈',
        'angel': '😇', 'clown': '🤡', 'skull': '💀', 'brain': '🧠'
    }
    
    # Colors for terminal
    COLORS = {
        'red': '\033[91m', 'green': '\033[92m', 'yellow': '\033[93m',
        'blue': '\033[94m', 'magenta': '\033[95m', 'cyan': '\033[96m',
        'white': '\033[97m', 'reset': '\033[0m', 'bold': '\033[1m'
    }

# Initialize config
config = Config()

# =============================================
# 🛡️ SECURITY & UTILITIES
# =============================================
class SecurityManager:
    """Handles all security related operations"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password with SHA256"""
        return hashlib.sha256(f"{password}_salt_ZADC_2024".encode()).hexdigest()
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return SecurityManager.hash_password(password) == hashed
    
    @staticmethod
    def generate_token(length: int = 32) -> str:
        """Generate secure random token"""
        return ''.join(random.choices(string.ascii_letters + string.digits + "!@#$%^&*", k=length))
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """Sanitize user input"""
        # Remove HTML tags
        text = re.sub(r'<[^>]*>', '', text)
        # Remove potential SQL injection
        text = text.replace("'", "''")
        # Remove control characters
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        return text.strip()

class Database:
    """Simple JSON-based database system"""
    
    @staticmethod
    def ensure_files():
        """Create necessary directories and files"""
        for directory in [config.DATA_DIR, config.LOGS_DIR, config.TEMP_DIR]:
            os.makedirs(directory, exist_ok=True)
        
        default_data = {
            config.USERS_FILE: {},
            config.GROUPS_FILE: {},
            config.BANS_FILE: [],
            config.STATS_FILE: {
                "total_users": 0,
                "total_groups": 0,
                "total_messages": 0,
                "commands_used": {},
                "daily_active": {},
                "start_date": datetime.now().isoformat()
            },
            config.SETTINGS_FILE: {
                "maintenance": False,
                "antispam": True,
                "max_warns": 3,
                "mute_duration": 3600
            }
        }
        
        for filepath, default in default_data.items():
            if not os.path.exists(filepath):
                Database.save(filepath, default)
    
    @staticmethod
    def load(filepath: str) -> Any:
        """Load data from JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    @staticmethod
    def save(filepath: str, data: Any):
        """Save data to JSON file"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def update_user(user_id: int, data: dict):
        """Update user data"""
        users = Database.load(config.USERS_FILE)
        if str(user_id) not in users:
            users[str(user_id)] = {
                "first_seen": datetime.now().isoformat(),
                "messages": 0,
                "warns": 0
            }
        users[str(user_id)].update(data)
        users[str(user_id)]["last_seen"] = datetime.now().isoformat()
        Database.save(config.USERS_FILE, users)
    
    @staticmethod
    def get_user(user_id: int) -> dict:
        """Get user data"""
        users = Database.load(config.USERS_FILE)
        return users.get(str(user_id), {})

class Decorations:
    """All decorative elements for messages"""
    
    @staticmethod
    def header(title: str) -> str:
        return f"""
╔══════════════════════════════╗
║   ✨ {title} ✨
╚══════════════════════════════╝
"""
    
    @staticmethod
    def footer() -> str:
        return f"""
╚══════════════════════════════╝
🤖 {config.BOT_NAME} v{config.BOT_VERSION}
📢 {config.BOT_CHANNEL}
"""
    
    @staticmethod
    def progress_bar(percent: int, length: int = 20) -> str:
        filled = int(length * percent / 100)
        bar = '█' * filled + '░' * (length - filled)
        return f"[{bar}] {percent}%"
    
    @staticmethod
    def random_emoji() -> str:
        return random.choice(list(config.EMOJIS.values()))

class TimeUtils:
    """Time-related utilities"""
    
    @staticmethod
    def get_current_time() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    @staticmethod
    def format_timestamp(timestamp: float) -> str:
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%I:%M %p - %d/%m/%Y")
    
    @staticmethod
    def time_ago(dt: datetime) -> str:
        now = datetime.now(timezone.utc)
        diff = now - dt
        
        if diff.days > 365:
            return f"{diff.days // 365} سنة"
        elif diff.days > 30:
            return f"{diff.days // 30} شهر"
        elif diff.days > 0:
            return f"{diff.days} يوم"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600} ساعة"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60} دقيقة"
        else:
            return f"{diff.seconds} ثانية"
    
    @staticmethod
    def format_duration(seconds: int) -> str:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        parts = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if secs > 0 or not parts:
            parts.append(f"{secs}s")
        
        return " ".join(parts)

class StringUtils:
    """String manipulation utilities"""
    
    @staticmethod
    def truncate(text: str, length: int = 100) -> str:
        return text[:length] + "..." if len(text) > length else text
    
    @staticmethod
    def random_string(length: int = 10) -> str:
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    @staticmethod
    def extract_urls(text: str) -> List[str]:
        url_pattern = r'https?://\S+'
        return re.findall(url_pattern, text)

# =============================================
# 🎨 NAME DECORATION SYSTEM
# =============================================
class NameDecorator:
    """Professional name decoration system"""
    
    # 100+ decoration styles
    STYLES = {
        'arabic': [
            "『{name}』", "「{name}」", "【{name}】", "《{name}》",
            "﴿{name}﴾", "۞{name}۞", "❀{name}❀", "✿{name}✿",
            "『♚』{name}『♚』", "『★』{name}『★』"
        ],
        'crowns': [
            "♔{name}♔", "♕{name}♕", "♛{name}♛", "♚{name}♚",
            "👑{name}👑", "👑『{name}』👑", "♛『{name}』♛"
        ],
        'wings': [
            "༺{name}༻", "༺☆{name}☆༻", "彡{name}彡",
            "ζ{name}ζ", "↭{name}↭", "『』{name}『』"
        ],
        'stars': [
            "★{name}★", "☆{name}☆", "✦{name}✦", "✧{name}✧",
            "⭐{name}⭐", "🌟{name}🌟", "✨{name}✨"
        ],
        'hearts': [
            "❤️{name}❤️", "💕{name}💕", "💗{name}💗",
            "💝{name}💝", "♥{name}♥", "♡{name}♡"
        ],
        'fire': [
            "🔥{name}🔥", "『🔥』{name}『🔥』", "☠️{name}☠️",
            "💀{name}💀", "⚡{name}⚡"
        ],
        'gaming': [
            "『G』{name}", "『VIP』{name}", "『PRO』{name}",
            "【VIP】{name}", "〖PRO〗{name}", "『LEGEND』{name}"
        ],
        'special': [
            "◈{name}◈", "◆{name}◆", "◇{name}◇", "◉{name}◉",
            "◎{name}◎", "●{name}●", "○{name}○", "■{name}■"
        ],
        'animals': [
            "🐉{name}🐉", "🦅{name}🦅", "🦊{name}🦊",
            "🐺{name}🐺", "🦁{name}🦁", "🐯{name}🐯"
        ],
        'mixed': [
            "★彡{name}彡★", "♛★{name}★♛", "☆彡{name}彡☆",
            "❤️★{name}★❤️", "⚡彡{name}彡⚡"
        ]
    }
    
    @staticmethod
    def decorate(name: str, category: str = None) -> str:
        """Decorate name with specified or random style"""
        name = name.strip()
        if not name:
            return "❌ Please enter a name"
        
        results = []
        
        if category and category in NameDecorator.STYLES:
            styles = NameDecorator.STYLES[category]
            results = [style.format(name=name) for style in styles]
        else:
            # Return all styles organized by category
            for cat, styles in NameDecorator.STYLES.items():
                results.append(f"\n{'='*30}\n📌 {cat.upper()}\n{'='*30}")
                results.extend([f"{i+1}. {style.format(name=name)}" 
                              for i, style in enumerate(styles)])
        
        return '\n'.join(results)
    
    @staticmethod
    def advanced_decorate(name: str) -> str:
        """Advanced decoration with multiple formats"""
        decorations = []
        
        # Simple decorations
        decorations.append(f"1. 『{name}』")
        decorations.append(f"2. 【{name}】")
        decorations.append(f"3. 「{name}」")
        
        # With symbols
        decorations.append(f"4. ★{name}★")
        decorations.append(f"5. ✦{name}✦")
        decorations.append(f"6. ♔{name}♔")
        
        # Complex
        decorations.append(f"7. 『★』{name}『★』")
        decorations.append(f"8. ♛『{name}』♛")
        decorations.append(f"9. 彡★{name}★彡")
        
        # Emoji
        decorations.append(f"10. 👑{name}👑")
        decorations.append(f"11. 🔥{name}🔥")
        decorations.append(f"12. ⚡{name}⚡")
        
        # Gaming
        decorations.append(f"13. [VIP] {name}")
        decorations.append(f"14. {name} | PRO")
        decorations.append(f"15. 『{name}』✓")
        
        # Special fonts
        decorations.append(f"16. ➤ {name}")
        decorations.append(f"17. • {name} •")
        decorations.append(f"18. ◈ {name} ◈")
        
        return '\n'.join(decorations)

# =============================================
# 📜 QURAN & RELIGIOUS CONTENT
# =============================================
class ReligiousContent:
    """Quran verses and religious content"""
    
    QURAN_VERSES = [
        {"text": "اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ", "surah": "البقرة", "ayah": 255},
        {"text": "إِنَّ مَعَ الْعُسْرِ يُسْرًا", "surah": "الشرح", "ayah": 6},
        {"text": "أَلَا بِذِكْرِ اللَّهِ تَطْمَئِنُّ الْقُلُوبُ", "surah": "الرعد", "ayah": 28},
        {"text": "وَقُلْ رَبِّ زِدْنِي عِلْمًا", "surah": "طه", "ayah": 114},
        {"text": "وَمَنْ يَتَوَكَّلْ عَلَى اللَّهِ فَهُوَ حَسْبُهُ", "surah": "الطلاق", "ayah": 3},
        {"text": "إِنَّ اللَّهَ مَعَ الصَّابِرِينَ", "surah": "البقرة", "ayah": 153},
        {"text": "وَإِذَا سَأَلَكَ عِبَادِي عَنِّي فَإِنِّي قَرِيبٌ", "surah": "البقرة", "ayah": 186},
        {"text": "وَلَسَوْفَ يُعْطِيكَ رَبُّكَ فَتَرْضَىٰ", "surah": "الضحى", "ayah": 5},
        {"text": "إِنَّ اللَّهَ وَمَلَائِكَتَهُ يُصَلُّونَ عَلَى النَّبِيِّ", "surah": "الأحزاب", "ayah": 56},
        {"text": "فَاذْكُرُونِي أَذْكُرْكُمْ وَاشْكُرُوا لِي وَلَا تَكْفُرُونِ", "surah": "البقرة", "ayah": 152},
        {"text": "لَا يُكَلِّفُ اللَّهُ نَفْسًا إِلَّا وُسْعَهَا", "surah": "البقرة", "ayah": 286},
        {"text": "وَاعْتَصِمُوا بِحَبْلِ اللَّهِ جَمِيعًا وَلَا تَفَرَّقُوا", "surah": "آل عمران", "ayah": 103},
        {"text": "قُلْ هُوَ اللَّهُ أَحَدٌ", "surah": "الإخلاص", "ayah": 1},
        {"text": "وَمَا تَوْفِيقِي إِلَّا بِاللَّهِ", "surah": "هود", "ayah": 88},
        {"text": "إِنَّ أَكْرَمَكُمْ عِنْدَ اللَّهِ أَتْقَاكُمْ", "surah": "الحجرات", "ayah": 13},
        {"text": "وَأُفَوِّضُ أَمْرِي إِلَى اللَّهِ", "surah": "غافر", "ayah": 44},
        {"text": "فَبِأَيِّ آلَاءِ رَبِّكُمَا تُكَذِّبَانِ", "surah": "الرحمن", "ayah": 13},
        {"text": "هَلْ جَزَاءُ الْإِحْسَانِ إِلَّا الْإِحْسَانُ", "surah": "الرحمن", "ayah": 60},
        {"text": "وَعَسَىٰ أَنْ تَكْرَهُوا شَيْئًا وَهُوَ خَيْرٌ لَكُمْ", "surah": "البقرة", "ayah": 216},
        {"text": "وَالَّذِينَ جَاهَدُوا فِينَا لَنَهْدِيَنَّهُمْ سُبُلَنَا", "surah": "العنكبوت", "ayah": 69},
        {"text": "رَبَّنَا لَا تُزِغْ قُلُوبَنَا بَعْدَ إِذْ هَدَيْتَنَا", "surah": "آل عمران", "ayah": 8},
        {"text": "وَقُلْ جَاءَ الْحَقُّ وَزَهَقَ الْبَاطِلُ", "surah": "الإسراء", "ayah": 81},
        {"text": "إِنَّ الْحَسَنَاتِ يُذْهِبْنَ السَّيِّئَاتِ", "surah": "هود", "ayah": 114},
        {"text": "وَاخْفِضْ لَهُمَا جَنَاحَ الذُّلِّ مِنَ الرَّحْمَةِ", "surah": "الإسراء", "ayah": 24},
        {"text": "وَلَا تَحْسَبَنَّ اللَّهَ غَافِلًا عَمَّا يَعْمَلُ الظَّالِمُونَ", "surah": "إبراهيم", "ayah": 42},
        {"text": "نَبِّئْ عِبَادِي أَنِّي أَنَا الْغَفُورُ الرَّحِيمُ", "surah": "الحجر", "ayah": 49},
        {"text": "ادْعُونِي أَسْتَجِبْ لَكُمْ", "surah": "غافر", "ayah": 60},
        {"text": "وَإِنْ تَعُدُّوا نِعْمَةَ اللَّهِ لَا تُحْصُوهَا", "surah": "إبراهيم", "ayah": 34},
        {"text": "قُلْ يَا عِبَادِيَ الَّذِينَ أَسْرَفُوا عَلَىٰ أَنْفُسِهِمْ لَا تَقْنَطُوا مِنْ رَحْمَةِ اللَّهِ", "surah": "الزمر", "ayah": 53},
        {"text": "إِنَّ الصَّلَاةَ تَنْهَىٰ عَنِ الْفَحْشَاءِ وَالْمُنْكَرِ", "surah": "العنكبوت", "ayah": 45}
    ]
    
    ADHKAR = [
        "سبحان الله وبحمده، سبحان الله العظيم",
        "لا إله إلا الله وحده لا شريك له، له الملك وله الحمد وهو على كل شيء قدير",
        "سبحان الله، والحمد لله، ولا إله إلا الله، والله أكبر",
        "أستغفر الله العظيم الذي لا إله إلا هو الحي القيوم وأتوب إليه",
        "اللهم صل وسلم على نبينا محمد",
        "لا حول ولا قوة إلا بالله",
        "حسبي الله لا إله إلا هو عليه توكلت وهو رب العرش العظيم",
        "اللهم إني أسألك العفو والعافية في الدنيا والآخرة"
    ]
    
    @staticmethod
    def get_random_verse() -> dict:
        return random.choice(ReligiousContent.QURAN_VERSES)
    
    @staticmethod
    def format_verse(verse: dict) -> str:
        return f"""
╔══════════════════════════════╗
║     📖 آيَةٌ قُرْآنِيَّةٌ     ║
╚══════════════════════════════╝

✨ ﴿ {verse['text']} ﴾ ✨

═══════════════════════════════
📖 سورة {verse['surah']} - آية {verse['ayah']}
═══════════════════════════════

🌸 تأملوها واذكروا الله العظيم
"""
    
    @staticmethod
    def get_random_dhikr() -> str:
        return random.choice(ReligiousContent.ADHKAR)

# =============================================
# 💬 WELCOME SYSTEM
# =============================================
class WelcomeSystem:
    """Advanced welcome system with multiple styles"""
    
    @staticmethod
    def get_welcome_style(user_name: str, user_id: int, group_name: str = "المجموعة") -> tuple:
        """Return (text, style_type)"""
        
        styles = []
        
        # Style 1: Royal Welcome
        styles.append((f"""
╔══════════════════════════════════╗
║     👑 تَرْحِيبٌ مَلَكِيٌّ 👑     ║
╚══════════════════════════════════╝

✨ أهلاً وسهلاً بك يا ملك في {group_name}

👤 <b>العضو الكريم:</b> {user_name}
🆔 <b>الآيدي:</b> <code>{user_id}</code>
📅 <b>التاريخ:</b> {datetime.now().strftime('%Y/%m/%d')}

🎉 نورت المكان وشرفتنا بقدومك
🌸 نتمنى لك أوقاتاً سعيدة معنا

═══════════════════════════════════
""", "royal"))
        
        # Style 2: Modern Tech
        styles.append((f"""
╭━━━━━━━━━━━━━━━━━━━━━━━━━╮
┃   🤖 تَرْحِيبٌ تِقَنِيٌّ   ┃
╰━━━━━━━━━━━━━━━━━━━━━━━━━╯

👋 Hey {user_name}!

📌 Welcome to {group_name}
🆔 ID: <code>{user_id}</code>

✅ Enjoy your stay!
✅ Follow the rules!
✅ Have fun!

━━━━━━━━━━━━━━━━━━━━━━━━━━
""", "tech"))
        
        # Style 3: Arabic Elegant
        styles.append((f"""
✦ ✦ ✦ ✦ ✦ ✦ ✦ ✦ ✦ ✦ ✦ ✦

     أهلًا بِالضَّيْفِ العَزِيز
     
     {user_name}
     
     فِي قُلُوبِنَا مَنْزِلَتُك
     
✦ ✦ ✦ ✦ ✦ ✦ ✦ ✦ ✦ ✦ ✦ ✦

📋 <b>الآيدي:</b> <code>{user_id}</code>
📅 <b>التاريخ:</b> {datetime.now().strftime('%d/%m/%Y')}
""", "arabic"))
        
        # Style 4: Minimal
        styles.append((f"""
━━━━━━━━━━━━━━━━━━
✨ Welcome ✨

{user_name}

━━━━━━━━━━━━━━━━━━
""", "minimal"))
        
        # Style 5: Gaming Style
        styles.append((f"""
🎮 ••●•• ●••● ••●•• 🎮

  Player Joined!
  
  [{user_name}]
  
  Level: Legend 🔥
  ID: {user_id}

🎮 ••●•• ●••● ••●•• 🎮
""", "gaming"))
        
        return random.choice(styles)
    
    @staticmethod
    def get_goodbye_message(user_name: str) -> str:
        messages = [
            f"😢 مع السلامة {user_name}، نتمنى عودتك قريباً",
            f"👋 باي باي {user_name}، فُقدت",
            f"💔 للأسف {user_name} غادر، سنفتقدك",
            f"🚶‍♂️ {user_name} قرر المغادرة، بالتوفيق"
        ]
        return random.choice(messages)

# =============================================
# 🎨 KEYBOARD & UI SYSTEM
# =============================================
class KeyboardSystem:
    """Advanced keyboard and UI system"""
    
    @staticmethod
    def get_main_menu() -> ReplyKeyboardMarkup:
        keyboard = [
            [KeyboardButton("📥 تحميل فيديو"), KeyboardButton("🎵 تحميل صوت")],
            [KeyboardButton("✨ زخرفة اسم"), KeyboardButton("📖 آية قرآنية")],
            [KeyboardButton("👑 لوحة التحكم"), KeyboardButton("ℹ️ معلومات")],
            [KeyboardButton("📊 إحصائيات"), KeyboardButton("⚙️ إعدادات")]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    @staticmethod
    def get_admin_panel() -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton("📢 بث جماعي", callback_data="admin_broadcast"),
                InlineKeyboardButton("📖 بث آية", callback_data="admin_verse")
            ],
            [
                InlineKeyboardButton("📊 إحصائيات كاملة", callback_data="admin_stats"),
                InlineKeyboardButton("👥 قائمة المستخدمين", callback_data="admin_users")
            ],
            [
                InlineKeyboardButton("🔨 حظر مستخدم", callback_data="admin_ban"),
                InlineKeyboardButton("🔇 كتم مستخدم", callback_data="admin_mute")
            ],
            [
                InlineKeyboardButton("⚙️ وضع الصيانة", callback_data="admin_maintenance"),
                InlineKeyboardButton("🔄 إعادة تشغيل", callback_data="admin_restart")
            ],
            [
                InlineKeyboardButton("📨 رسالة لمستخدم", callback_data="admin_message"),
                InlineKeyboardButton("🔑 تغيير كلمة السر", callback_data="admin_changepass")
            ],
            [InlineKeyboardButton("🚫 إغلاق اللوحة", callback_data="admin_close")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_decoration_menu() -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton("👑 ملوكي", callback_data="deco_crowns"),
                InlineKeyboardButton("⭐ نجوم", callback_data="deco_stars")
            ],
            [
                InlineKeyboardButton("❤️ قلوب", callback_data="deco_hearts"),
                InlineKeyboardButton("🔥 ناري", callback_data="deco_fire")
            ],
            [
                InlineKeyboardButton("🎮 Gaming", callback_data="deco_gaming"),
                InlineKeyboardButton("🦅 حيوانات", callback_data="deco_animals")
            ],
            [
                InlineKeyboardButton("✨ متقدم", callback_data="deco_advanced"),
                InlineKeyboardButton("🔀 عشوائي", callback_data="deco_random")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

# =============================================
# 📊 STATISTICS TRACKER
# =============================================
class StatsTracker:
    """Tracks bot statistics"""
    
    @staticmethod
    def record_command(command: str):
        stats = Database.load(config.STATS_FILE)
        stats["commands_used"][command] = stats["commands_used"].get(command, 0) + 1
        stats["total_messages"] += 1
        Database.save(config.STATS_FILE, stats)
    
    @staticmethod
    def record_user_activity(user_id: int):
        today = datetime.now().strftime("%Y-%m-%d")
        stats = Database.load(config.STATS_FILE)
        if today not in stats["daily_active"]:
            stats["daily_active"][today] = []
        if user_id not in stats["daily_active"][today]:
            stats["daily_active"][today].append(user_id)
        Database.save(config.STATS_FILE, stats)
    
    @staticmethod
    def get_stats() -> dict:
        return Database.load(config.STATS_FILE)
    
    @staticmethod
    def format_stats() -> str:
        stats = Database.load(config.STATS_FILE)
        users = Database.load(config.USERS_FILE)
        groups = Database.load(config.GROUPS_FILE)
        
        return f"""
╔══════════════════════════════╗
║     📊 إحصائيات البوت        ║
╚══════════════════════════════╝

👥 إجمالي المستخدمين: {len(users)}
👥 إجمالي المجموعات: {len(groups)}
💬 إجمالي الرسائل: {stats.get('total_messages', 0)}
📅 تاريخ البدء: {stats.get('start_date', 'غير معروف')[:10]}

═══════════════════════════════

📈 أكثر الأوامر استخداماً:
{chr(10).join([f'  • {cmd}: {count}' for cmd, count in sorted(stats.get('commands_used', {}).items(), key=lambda x: x[1], reverse=True)[:5]])}

═══════════════════════════════

📊 النشاط اليومي:
{chr(10).join([f'  • {date}: {len(users)} مستخدم' for date, users in sorted(stats.get('daily_active', {}).items(), reverse=True)[:7]])}

═══════════════════════════════
🚀 {config.BOT_NAME} v{config.BOT_VERSION}
"""
    
    @staticmethod
    def format_users_list(page: int = 1, per_page: int = 10) -> str:
        users = Database.load(config.USERS_FILE)
        user_items = list(users.items())
        total_pages = max(1, (len(user_items) + per_page - 1) // per_page)
        
        start = (page - 1) * per_page
        end = start + per_page
        page_users = user_items[start:end]
        
        text = f"👥 قائمة المستخدمين (صفحة {page}/{total_pages})\n\n"
        for i, (uid, data) in enumerate(page_users, start + 1):
            text += f"{i}. <code>{uid}</code> | {data.get('name', 'مستخدم')}\n"
        
        return text

# =============================================
# 🤖 BOT HANDLERS
# =============================================

# Initialize bot
async def post_init(application):
    """Setup bot commands and initial configuration"""
    Database.ensure_files()
    
    commands = [
        BotCommand("start", "🚀 بدء التشغيل"),
        BotCommand("help", "📚 قائمة المساعدة"),
        BotCommand("admin", "👑 لوحة التحكم"),
        BotCommand("quran", "📖 آية قرآنية عشوائية"),
        BotCommand("decorate", "✨ زخرفة اسم"),
        BotCommand("stats", "📊 إحصائيات البوت"),
        BotCommand("info", "ℹ️ معلومات عن البوت"),
        BotCommand("settings", "⚙️ الإعدادات"),
        BotCommand("support", "🆘 الدعم الفني"),
    ]
    
    await application.bot.set_my_commands(commands)
    
    # Log startup
    print(f"""
{config.COLORS['cyan']}
╔══════════════════════════════════════════╗
║   🤖 Bot Started Successfully           ║
║   Name: {config.BOT_NAME}                        ║
║   Version: {config.BOT_VERSION}                       ║
║   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}       
