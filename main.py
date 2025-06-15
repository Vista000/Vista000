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
import time
import logging
import asyncio
from dotenv import load_dotenv
import aiohttp
import tempfile

load_dotenv()
keep_alive()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

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

🟡 ربات خودش رسید رو میفرسته برای ادمین. بعد از تایید ادمین، فایل کامل بدون هیچ مشکلی برات ارسال میشه. :>"""

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

# --- دانلود و ارسال فایل از لینک (async) ---
async def send_file_from_url(bot, chat_id, url, caption=None):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    tmp = tempfile.NamedTemporaryFile(delete=False)
                    data = await resp.read()
                    tmp.write(data)
                    tmp.close()
                    with open(tmp.name, "rb") as f:
                        await bot.send_document(chat_id=chat_id, document=f, caption=caption)
                    os.unlink(tmp.name)
                else:
                    await bot.send_message(chat_id, "❌ خطا در دانلود فایل نمونه!")
    except Exception as e:
        await bot.send_message(chat_id, f"❌ خطا در ارسال فایل: {e}")

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

# --- هندلر پیام‌ها ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    text = message.text.strip() if message and message.text else None
    chat_id = str(update.effective_chat.id)

    if not text:
        return

    if text == "/start":
        await message.reply_text(
            "🎉 به ربات ویستانشر خوش اومدی!\nلطفاً پایه تحصیلی‌ت رو انتخاب کن:",
            reply_markup=mainKeyboard,
        )

    elif text in ["نهم", "دهم", "یازدهم", "دوازدهم"]:
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
            await send_file_from_url(
                context.bot, chat_id, sample_link, caption="📄 نمونه فایل رو ببین!"
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
            # فقط لینک کامل رو برای کاربر بفرست
            await message.reply_text(
                f"برای دریافت نسخه کامل روی لینک زیر کلیک کن:\n\n{full_link}\n\n"
                + paymentInfo
            )

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

    if query.data.startswith("confirm_") and str(query.message.chat.id) == str(ADMIN_ID):
        target_id = query.data.split("_")[1]
        grade, mode = user_grades.get(target_id), user_mode.get(target_id)
        full_link = get_full_link(grade, mode)

        if full_link:
            try:
                # برای نسخه کامل فقط لینک رو میفرستیم (مثل پیام قبل)
                await context.bot.send_message(
                    chat_id=int(target_id),
                    text=f"نسخه کامل شما:\n\n{full_link}\n\nموفق باشید! 🌟",
                )
            except Exception as e:
                print(f"[ERROR] Full file send fail: {e}")


def main():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", handle_message))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    application.add_handler(CallbackQueryHandler(handle_callback_query))

    application.run_polling()


if __name__ == "__main__":
    main()
