import os
import threading
import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters

# ⚙️ الإعدادات
TOKEN = "8702640145:AAHyLv6r3xfyf9x-dptwim6_BrnJSbWYpmY"
OWNER_ID = 8038919535  # ⚠️ غير ده لآيديك الحقيقي
ADMIN_PASS = "0658"
MAINTENANCE_MODE = False

# 🌐 سيرفر Render - ضروري عشان الموقع مايقفلش
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")
    def log_message(self, format, *args):
        pass

def start_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    print(f"✅ Server running on port {port}")
    server.serve_forever()

# 📜 30 آية قرآنية
QURAN_VERSES = [
    "✨ ﴿ اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ ﴾ ✨",
    "📖 ﴿ إِنَّ مَعَ الْعُسْرِ يُسْرًا ﴾ 📖",
    "✨ ﴿ أَلَا بِذِكْرِ اللَّهِ تَطْمَئِنُّ الْقُلُوبُ ﴾ ✨",
    "📖 ﴿ وَقُلْ رَبِّ زِدْنِي عِلْمًا ﴾ 📖",
    "✨ ﴿ وَمَنْ يَتَوَكَّلْ عَلَى اللَّهِ فَهُوَ حَسْبُهُ ﴾ ✨",
    "📖 ﴿ إِنَّ اللَّهَ مَعَ الصَّابِرِينَ ﴾ 📖",
    "✨ ﴿ وَإِذَا سَأَلَكَ عِبَادِي عَنِّي فَإِنِّي قَرِيبٌ ﴾ ✨",
    "📖 ﴿ وَلَسَوْفَ يُعْطِيكَ رَبُّكَ فَتَرْضَىٰ ﴾ 📖",
    "✨ ﴿ إِنَّ اللَّهَ وَمَلَائِكَتَهُ يُصَلُّونَ عَلَى النَّبِيِّ ﴾ ✨",
    "📖 ﴿ فَاذْكُرُونِي أَذْكُرْكُمْ وَاشْكُرُوا لِي وَلَا تَكْفُرُونِ ﴾ 📖",
    "✨ ﴿ لَا يُكَلِّفُ اللَّهُ نَفْسًا إِلَّا وُسْعَهَا ﴾ 📖",
    "📖 ﴿ وَاعْتَصِمُوا بِحَبْلِ اللَّهِ جَمِيعًا وَلَا تَفَرَّقُوا ﴾ ✨",
    "✨ ﴿ قُلْ هُوَ اللَّهُ أَحَدٌ ﴾ 📖",
    "📖 ﴿ وَمَا تَوْفِيقِي إِلَّا بِاللَّهِ ﴾ ✨",
    "✨ ﴿ إِنَّ أَكْرَمَكُمْ عِنْدَ اللَّهِ أَتْقَاكُمْ ﴾ 📖",
    "📖 ﴿ وَأُفَوِّضُ أَمْرِي إِلَى اللَّهِ ﴾ ✨",
    "✨ ﴿ وَجَعَلْنَا مِنَ الْمَاءِ كُلَّ شَيْءٍ حَيٍّ ﴾ 📖",
    "📖 ﴿ فَبِأَيِّ آلَاءِ رَبِّكُمَا تُكَذِّبَانِ ﴾ ✨",
    "✨ ﴿ هَلْ جَزَاءُ الْإِحْسَانِ إِلَّا الْإِحْسَانُ ﴾ 📖",
    "📖 ﴿ وَعَسَىٰ أَنْ تَكْرَهُوا شَيْئًا وَهُوَ خَيْرٌ لَكُمْ ﴾ ✨",
    "✨ ﴿ وَالَّذِينَ جَاهَدُوا فِينَا لَنَهْدِيَنَّهُمْ سُبُلَنَا ﴾ 📖",
    "📖 ﴿ رَبَّنَا لَا تُزِغْ قُلُوبَنَا بَعْدَ إِذْ هَدَيْتَنَا ﴾ ✨",
    "✨ ﴿ وَقُلْ جَاءَ الْحَقُّ وَزَهَقَ الْبَاطِلُ ﴾ 📖",
    "📖 ﴿ إِنَّ الْحَسَنَاتِ يُذْهِبْنَ السَّيِّئَاتِ ﴾ ✨",
    "✨ ﴿ وَاخْفِضْ لَهُمَا جَنَاحَ الذُّلِّ مِنَ الرَّحْمَةِ ﴾ 📖",
    "📖 ﴿ وَلَا تَحْسَبَنَّ اللَّهَ غَافِلًا عَمَّا يَعْمَلُ الظَّالِمُونَ ﴾ ✨",
    "✨ ﴿ نَبِّئْ عِبَادِي أَنِّي أَنَا الْغَفُورُ الرَّحِيمُ ﴾ 📖",
    "📖 ﴿ ادْعُونِي أَسْتَجِبْ لَكُمْ ﴾ ✨",
    "✨ ﴿ وَإِنْ تَعُدُّوا نِعْمَةَ اللَّهِ لَا تُحْصُوهَا ﴾ 📖",
    "📖 ﴿ قُلْ يَا عِبَادِيَ الَّذِينَ أَسْرَفُوا عَلَىٰ أَنْفُسِهِمْ لَا تَقْنَطُوا مِنْ رَحْمَةِ اللَّهِ ﴾ ✨"
]

# 📋 القوائم
def main_menu():
    keyboard = [
        [KeyboardButton("📥 تحميل"), KeyboardButton("✨ زخرفة")],
        [KeyboardButton("👑 أدمن"), KeyboardButton("ℹ️ معلومات")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def admin_panel():
    keyboard = [
        [InlineKeyboardButton("📢 بث جماعي", callback_data="bc"), 
         InlineKeyboardButton("📖 بث آية", callback_data="verse")],
        [InlineKeyboardButton("📊 إحصائيات", callback_data="stats"), 
         InlineKeyboardButton("⚙️ صيانة", callback_data="mnt")],
        [InlineKeyboardButton("🚫 إغلاق", callback_data="close")]
    ]
    return InlineKeyboardMarkup(keyboard)

# 📂 حفظ المستخدمين
def save_user(chat_id, name="مستخدم"):
    try:
        with open("users.txt", "a+", encoding="utf-8") as f:
            f.seek(0)
            if str(chat_id) not in f.read():
                f.write(f"{chat_id}|{name}\n")
    except:
        pass

def get_name(update: Update):
    chat = update.effective_chat
    if chat.title:
        return chat.title
    name = chat.first_name or ""
    if chat.last_name:
        name += " " + chat.last_name
    return name or "مستخدم"

async def broadcast(bot, msg):
    if not os.path.exists("users.txt"):
        return 0
    with open("users.txt", "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    count = 0
    for line in lines:
        if line.strip():
            cid = line.split("|")[0]
            try:
                await bot.send_message(chat_id=int(cid), text=msg, parse_mode='HTML')
                count += 1
            except:
                pass
    return count

# 🎨 الزخرفة
def decorate(name):
    return "\n".join([
        f"1. 『{name}』",
        f"2. ♔{name}♔",
        f"3. ◈{name}◈",
        f"4. 彡{name}彡",
        f"5. ♛{name}♛",
        f"6. ツ{name}ツ",
        f"7. ✿{name}✿",
        f"8. ✦{name}✦"
    ])

# 🤖 إعداد الأوامر
async def post_init(app):
    cmds = [
        BotCommand("start", "بدء التشغيل"),
        BotCommand("help", "المساعدة"),
        BotCommand("admin", "🔐 لوحة تحكم المالك"),
    ]
    await app.bot.set_my_commands(cmds)

# 👑 أوامر البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_chat.id, get_name(update))
    await update.message.reply_text(
        "🎯 أهلاً بك في بوت الخدمات!\n\n🔐 للمالك: استخدم /admin",
        reply_markup=main_menu()
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_chat.id, get_name(update))
    await update.message.reply_text(
        "📚 <b>المساعدة:</b>\n\n"
        "📥 تحميل - أرسل رابط فيديو\n"
        "✨ زخرفة - اكتب: زخرفة الاسم\n"
        "🔐 أدمن - /admin",
        reply_markup=main_menu(),
        parse_mode='HTML'
    )

async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ هذا الأمر للمالك فقط!")
        return
    await update.message.reply_text("🔑 أدخل كلمة المرور (0658):")
    context.user_data['waiting_pass'] = True

# 🎯 معالج النصوص
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    
    save_user(update.effective_chat.id, get_name(update))
    text = update.message.text.strip()
    uid = update.effective_user.id

    # انتظار كلمة المرور
    if context.user_data.get('waiting_pass'):
        if text == ADMIN_PASS:
            context.user_data['waiting_pass'] = False
            await update.message.reply_text(
                "✅ <b>تم الدخول للوحة التحكم!</b>\nاختر من القائمة:",
                reply_markup=admin_panel(),
                parse_mode='HTML'
            )
        else:
            context.user_data['waiting_pass'] = False
            await update.message.reply_text("❌ كلمة المرور خاطئة!")
        return

    # انتظار رسالة البث
    if context.user_data.get('waiting_bc'):
        context.user_data['waiting_bc'] = False
        msg = await update.message.reply_text("📢 جاري البث الجماعي...")
        cnt = await broadcast(context.bot, text)
        await msg.edit_text(f"✅ تم البث إلى {cnt} مستخدم!")
        return

    # انتظار رقم الآية
    if context.user_data.get('waiting_verse'):
        context.user_data['waiting_verse'] = False
        try:
            n = int(text)
            if 1 <= n <= 30:
                verse = QURAN_VERSES[n-1]
                full = f"✨ 📜 <b>آيَةٌ قُرْآنِيَّةٌ كَرِيمَةٌ</b> 📜 ✨\n\n{verse}\n\n🌸 تأملها واذكر الله"
                msg = await update.message.reply_text("📖 جاري بث الآية...")
                cnt = await broadcast(context.bot, full)
                await msg.edit_text(f"✅ تم بث الآية إلى {cnt} مستخدم!")
            else:
                await update.message.reply_text("❌ اختر رقم من 1 إلى 30")
        except:
            await update.message.reply_text("❌ أدخل رقم صحيح")
        return

    # زر أدمن
    if text == "👑 أدمن":
        if uid != OWNER_ID:
            await update.message.reply_text("❌ للمالك فقط!")
            return
        await update.message.reply_text("🔑 أدخل كلمة المرور (0658):")
        context.user_data['waiting_pass'] = True
        return

    # زر تحميل
    if text == "📥 تحميل":
        await update.message.reply_text("📥 أرسل رابط الفيديو للتحميل\nأو اكتب: يوت اسم الأغنية")
        return

    # زر زخرفة
    if text == "✨ زخرفة":
        await update.message.reply_text("✨ اكتب: زخرفة [الاسم]\nمثال: زخرفة محمد")
        return

    # زر معلومات
    if text == "ℹ️ معلومات":
        user = update.effective_user
        await update.message.reply_text(
            f"👤 الاسم: {user.first_name}\n🆔 الآيدي: <code>{user.id}</code>",
            parse_mode='HTML'
        )
        return

    # زخرفة الاسم
    if text.startswith("زخرفة ") or text.startswith("زخرف "):
        parts = text.split(" ", 1)
        if len(parts) > 1 and parts[1].strip():
            name = parts[1].strip()
            result = f"✨ <b>زخرفة: {name}</b>\n\n{decorate(name)}"
            await update.message.reply_text(result, parse_mode='HTML')
        else:
            await update.message.reply_text("❌ مثال: زخرفة أحمد")
        return

    # رد على السلام
    if any(word in text for word in ["سلام", "السلام"]):
        await update.message.reply_text(
            f"✨ وعليكم السلام ورحمة الله وبركاته\nأهلاً {update.effective_user.first_name} 🌸"
        )

# 🎯 معالج الأزرار التفاعلية
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id != OWNER_ID:
        await query.edit_message_text("❌ هذه الأزرار للمالك فقط!")
        return

    data = query.data

    if data == "bc":
        await query.edit_message_text("📢 أرسل رسالة البث الجماعي الآن:")
        context.user_data['waiting_bc'] = True

    elif data == "verse":
        await query.edit_message_text("📖 أرسل رقم الآية (1-30):")
        context.user_data['waiting_verse'] = True

    elif data == "stats":
        if os.path.exists("users.txt"):
            with open("users.txt", "r", encoding="utf-8") as f:
                total = len(f.read().splitlines())
            await query.edit_message_text(f"📊 إجمالي المستخدمين: {total}")
        else:
            await query.edit_message_text("📊 لا يوجد مستخدمين بعد")

    elif data == "mnt":
        global MAINTENANCE_MODE
        MAINTENANCE_MODE = not MAINTENANCE_MODE
        status = "🔴 مفعل" if MAINTENANCE_MODE else "🟢 معطل"
        await query.edit_message_text(f"⚙️ وضع الصيانة: {status}")

    elif data == "close":
        await query.edit_message_text("🚫 تم إغلاق لوحة التحكم")
        context.user_data.clear()

# 🚀 دالة التشغيل الرئيسية
async def run_bot():
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    
    await app.initialize()
    await app.start()
    print("🚀 البوت اشتغل!")
    await app.updater.start_polling()
    
    # يخلي البوت شغال علطول
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    # شغل السيرفر
    threading.Thread(target=start_server, daemon=True).start()
    # شغل البوت
    asyncio.run(run_bot())
