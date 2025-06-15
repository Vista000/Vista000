from keepalive import keep_alive
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    filters,
)
import os
import logging
import asyncio
from dotenv import load_dotenv
import aiohttp
import tempfile
from telegram.error import Conflict

load_dotenv()
keep_alive()

# --- لاگینگ ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.info("🚀 Bot is starting...")

# --- اطلاعات پایه ---
TOKEN = os.environ["TOKEN"]
ADMIN_ID = os.getenv("ADMIN_ID")
AZMON11SAMPLE = os.getenv("AZMON11SAMPLE")
KETAB9SAMPLE = os.getenv("KETAB9SAMPLE")
KETAB10SAMPLE = os.getenv("KETAB10SAMPLE")
KETAB11SAMPLE = os.getenv("KETAB11SAMPLE")

KETAB9FULL = os.getenv("KETAB9FULL")
KETAB10FULL = os.getenv("KETAB10FULL")
KETAB11FULL = os.getenv("KETAB11FULL")

AZMON11FULL = os.getenv("AZMON11FULL")

# --- پیام‌ها ---
bookMessage = """📚 کتابچه چیه؟  
1️⃣ اول فایل یه مقدمه کامل و تا-حدی-دلی داره، با همسنات مصاحبه کردم و راهکارهایی که برای 20 گرفتن دینی کمکشون کرده رو اونجا نوشتم. خیلیا گفتن با خوندن مقدمه توی ذهنشون جرقه خورده و ببیشتر به دینی علاقه‌مند شدن که باعث افتخارمونه!

2️⃣ چکیده‌ی درس‌ها، با کلمات رنگی رنگی و مثال‌هایی که به تفهیم مطلب کمک میکنن، هر رنگی یه معنی خاص داره
3️⃣ پاسخ تشریحی سوالات آخر درس (خود کتاب)

4️⃣ نمونه سوال متن درس، برای اینکه طراح اگه به سرش زد از متن سوال بده تو حرفه ای باشی
5️⃣ پاسخ‌ خیلی خیلی تشریحی! 

6️⃣ یه بخش جدید تازه اضافه شده به اسم #تعریفیات ! که جواب همه سوالات "فلان چیز را تعریف کنید" اونجاست! در پایان هر درس میتونی پیداش کنی 
➕ تعریفیات کل کتاب در پایان فایل! این یکی دیکه خیلی خفنه و مخصوص مرور شب امتحانه :)

* نکته مهم: #تعریفیات ! فعلا فقط برای پایه یازدهم در دسترسه. برای بقیه پایه ها به زودی اضافه میشه

💡 همین الان زیر 1 دقیقه می‌تونی کل فایل کتابچه رو تهیه‌ کنی! آماده‌ای؟"""

examMessage = """📝 آزمونچه چیه؟  
آزمونچه‌ها شامل سوالات تستی و تشریحی برای سنجش و تمرین بهتر مطالب کتابچه هستند.  
با داشتن آزمونچه می‌تونید خودتون رو بسنجید و برای امتحانات آماده بشید.  
توجه داشته باشید که آزمونچه‌ها فعلاً فقط برای پایه یازدهم فعال است."""

sampleReminder = "بهتره قبل از خرید نسخه کامل، درس اول تا سوم مخصوص پایه خودت رو رایگان دانلود کنی!"

paymentInfo = """💳 دمت گرم که یه قدم جدی به سمت نمره 20 برداشتی!  
برای دریافت نسخه کامل، فقط کافیه 79 هزارتومن واریز کنی اینجا 👇 و رسیدش رو هم همین‌جا ارسال کنی:

💳 5859 8312 3017 6678

🟡 ربات خودش رسید رو میفرسته برای ادمین. بعد از تایید ادمین، لینک دسترسی به فایل کامل (مخصوص خودت) بدون هیچ مشکلی برات ارسال میشه. :>"""

# --- کیبوردها ---
mainKeyboard = ReplyKeyboardMarkup(
    [["نهم", "دهم"], ["یازدهم", "دوازدهم"], ["ℹ️ معرفی"]], resize_keyboard=True
)
choiceKeyboard = ReplyKeyboardMarkup(
    [["📚 کتابچه", "📝 آزمونچه"], ["🔙 بازگشت"]], resize_keyboard=True
)
readyKeyboard = ReplyKeyboardMarkup(
    [["✅ معلومه که آماده‌م!"], ["🔙 بازگشت"]], resize_keyboard=True
)
backOnlyKeyboard = ReplyKeyboardMarkup([["🔙 بازگشت"]], resize_keyboard=True)

# --- وضعیت کاربران ---
user_grades, user_ready, user_mode = {}, {}, {}

# --- ارسال لینک نمونه (بدون دانلود مستقیم) ---
async def send_link_sample(bot, chat_id, url, caption=None):
    try:
        if caption:
            await bot.send_message(chat_id=chat_id, text=f"{caption}\n{url}")
        else:
            await bot.send_message(chat_id=chat_id, text=url)
    except Exception as e:
        await bot.send_message(chat_id, f"❌ خطا در ارسال لینک نمونه: {e}")

# --- گرفتن لینک نمونه از env ---
def get_sample_link(grade, mode):
    mapping = {
        "book": {
            "نهم": KETAB9SAMPLE,
            "دهم": KETAB10SAMPLE,
            "یازدهم": KETAB11SAMPLE,
        },
        "exam": {
            "یازدهم": AZMON11SAMPLE,
        },
    }
    return mapping.get(mode, {}).get(grade)

# --- گرفتن لینک کامل از env ---
def get_full_link(grade, mode):
    mapping = {
        "book": {
            "نهم": KETAB9FULL,
            "دهم": KETAB10FULL,
            "یازدهم": KETAB11FULL,
        },
        "exam": {
            "یازدهم": AZMON11FULL,
        },
    }
    return mapping.get(mode, {}).get(grade)

# --- هندل پیام /start جدا ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎉 به ربات ویستانشر خوش اومدی!\nلطفاً پایه تحصیلی‌ت رو انتخاب کن:",
        reply_markup=mainKeyboard,
    )

# --- هندلر پیام‌ها فقط برای پیام‌های متنی عادی ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    text = message.text.strip() if message and message.text else None
    chat_id = str(update.effective_chat.id)

    if not text:
        return

    if text == "/start":
        return

    if text in ["نهم", "دهم", "یازدهم", "دوازدهم"]:
        user_grades[chat_id] = text
        if text == "دوازدهم":
            await message.reply_text("❌ فعلاً محتوای خاصی برای پایه دوازدهم آماده نیست.")
        else:
            await message.reply_text(
                f"✅ پایه‌ی شما ({text}) ثبت شد.\nحالا انتخاب کن که دنبال چی هستی:",
                reply_markup=choiceKeyboard,
            )

    elif text in ["📚 کتابچه", "📝 آزمونچه"]:
        grade = user_grades.get(chat_id)
        if not grade:
            await message.reply_text("⛔ لطفاً ابتدا پایه تحصیلی خود را مشخص کن.")
            return
        mode = "book" if "کتابچه" in text else "exam"
        if mode == "exam" and grade != "یازدهم":
            await message.reply_text(
                "❌ آزمونچه در حال حاضر فقط برای پایه یازدهم فعاله.",
                reply_markup=backOnlyKeyboard,
            )
            return

        user_mode[chat_id] = mode
        await message.reply_text(bookMessage if mode == "book" else examMessage)
        await context.bot.send_message(chat_id=chat_id, text=sampleReminder)

        sample_link = get_sample_link(grade, mode)
        if sample_link:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"📄 نمونه فایل رو اینجا ببین:\n{sample_link}",
            )
            full_link = get_full_link(grade, mode)
            if full_link:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="آماده‌ای برای دریافت نسخه کامل؟ 👇",
                    reply_markup=readyKeyboard,
                )
            else:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="⚠️ نسخه کامل فعلاً آماده نیست.",
                    reply_markup=backOnlyKeyboard,
                )
        else:
            await message.reply_text("❌ فایل نمونه موجود نیست. لطفاً به ادمین پیام بده.")

    elif text == "✅ معلومه که آماده‌م!":
        grade, mode = user_grades.get(chat_id), user_mode.get(chat_id)
        full_link = get_full_link(grade, mode)
        if not full_link:
            await message.reply_text(
                "⛔ نسخه کامل برای این پایه فعلاً آماده نیست.", reply_markup=backOnlyKeyboard
            )
        else:
            user_ready[chat_id] = True
            await message.reply_text(paymentInfo)

    elif text == "ℹ️ معرفی":
        await message.reply_text(
            "ما در ویستانشر محتوای دینی زرتشتی برای دانش‌آموزان تولید می‌کنیم. 📘🌟"
        )

    elif text == "🔙 بازگشت":
        await message.reply_text("بازگشتی موفقیت‌آمیز 😄", reply_markup=mainKeyboard)

    elif user_ready.get(chat_id):
        try:
            await context.bot.send_message(
                ADMIN_ID, f"📥 رسید از کاربر {chat_id} دریافت شد:"
            )
            await context.bot.forward_message(
                chat_id=ADMIN_ID, from_chat_id=int(chat_id), message_id=message.message_id
            )
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text="📌 برای تأیید پرداخت، روی دکمه زیر بزن:",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("تأیید پرداخت", callback_data=f"confirm_{chat_id}")]]
                ),
            )
            await message.reply_text("✅ رسیدت توسط بات برای ادمین ارسال شد.")
            user_ready[chat_id] = False
        except Exception as e:
            print(f"[ERROR] رسید ارسال نشد: {e}")
            await message.reply_text("❌ خطا در ارسال رسید. لطفاً دوباره امتحان کن.")

    elif chat_id != str(ADMIN_ID):
        await message.reply_text("📩 پیام شما ثبت شد و به ادمین ارسال می‌شود.")
        await context.bot.forward_message(
            chat_id=ADMIN_ID, from_chat_id=int(chat_id), message_id=message.message_id
        )

# --- تأیید ادمین ---
async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("confirm_") and str(update.effective_user.id) == str(ADMIN_ID):
        target_id = query.data.split("_")[1]
        target_id_str = str(target_id)

        grade = user_grades.get(target_id_str)
        mode = user_mode.get(target_id_str)
        full_link = get_full_link(grade, mode)

        if not grade or not mode or not full_link:
            await query.edit_message_text("❌ اطلاعات کاربر ناقص است یا فایل پیدا نشد.")
            logging.warning(f"[WARNING] کاربر {target_id} اطلاعات ناقص دارد.")
            return

        try:
            await context.bot.send_message(
                chat_id=int(target_id),
                text=f"✅ پرداخت شما تایید شد.\n\n📁 لینک دریافت نسخه کامل:\n{full_link}\n\n🌟 موفق باشید!",
            )
            await query.edit_message_text("✅ فایل کامل با موفقیت ارسال شد.")
        except Exception as e:
            logging.error(f"[ERROR] Full file send fail: {e}")
            await query.edit_message_text("❌ خطا در ارسال فایل برای کاربر.")

# --- هندلر خطا ---
async def error_handler(update, context):
    if isinstance(context.error, Conflict):
        logging.warning("⚠️ Conflict: یک نسخه دیگر از بات اجرا شده بود.")
    else:
        logging.error(msg="❌ خطای غیرمنتظره:", exc_info=context.error)

    if update and update.effective_message:
        try:
            await update.effective_message.reply_text("❌ خطایی رخ داد. لطفاً دوباره تلاش کن.")
        except Exception:
            pass

def main():
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    application.add_error_handler(error_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
