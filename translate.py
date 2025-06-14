import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.client.default import DefaultBotProperties
from googletrans import Translator
import aiosqlite

API_TOKEN = "7526297027:AAEJUTE617sHyTnjEba1AKK2MlWg1u-j228"
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
translator = Translator()

# Foydalanuvchi til sozlamasini olish yoki o‘rnatish
async def get_user_langs(user_id):
    async with aiosqlite.connect("users.db") as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            from_lang TEXT,
            to_lang TEXT
        )""")
        await db.commit()
        async with db.execute("SELECT from_lang, to_lang FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return row
        await db.execute("INSERT INTO users (user_id, from_lang, to_lang) VALUES (?, ?, ?)", (user_id, "auto", "en"))
        await db.commit()
        return ("auto", "en")

async def set_user_lang(user_id, from_lang, to_lang):
    async with aiosqlite.connect("users.db") as db:
        await db.execute("UPDATE users SET from_lang = ?, to_lang = ? WHERE user_id = ?", (from_lang, to_lang, user_id))
        await db.commit()

async def swap_langs(user_id):
    from_lang, to_lang = await get_user_langs(user_id)
    await set_user_lang(user_id, to_lang, from_lang)

def lang_keyboard():
    langs = [("🇺🇿 Uzbek", "uz"), ("🇷🇺 Russian", "ru"), ("🇬🇧 English", "en"), ("🇹🇷 Turkish", "tr"), ("🇰🇷 Korean", "ko")]
    buttons = [InlineKeyboardButton(text=name, callback_data=f"setlang:{code}") for name, code in langs]
    return InlineKeyboardMarkup(inline_keyboard=[buttons])

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    from_lang, to_lang = await get_user_langs(message.from_user.id)
    await message.answer(
        f"👋 Salom {message.from_user.full_name}!\n"
        f"Men sizga matnni boshqa tilga tarjima qilishda yordam beraman.\n\n"
        f"🔤 Joriy: <b>{from_lang} → {to_lang}</b>\n\n"
        f"📌 /language — til sozlash\n🔄 /swap — tillarni almashtirish",
        reply_markup=lang_keyboard()
    )

@dp.message(Command("language"))
async def cmd_language(message: types.Message):
    await message.answer("🌐 Qaysi tilga tarjima qilay?", reply_markup=lang_keyboard())

@dp.callback_query(F.data.startswith("setlang:"))
async def callback_lang(callback: types.CallbackQuery):
    lang_code = callback.data.split(":")[1]
    from_lang, _ = await get_user_langs(callback.from_user.id)
    await set_user_lang(callback.from_user.id, from_lang, lang_code)
    await callback.message.edit_text(f"✅ Tarjima tili: <b>{lang_code}</b> ga o‘zgartirildi.")

@dp.message(Command("swap"))
async def cmd_swap(message: types.Message):
    await swap_langs(message.from_user.id)
    from_lang, to_lang = await get_user_langs(message.from_user.id)
    await message.answer(f"🔁 Tillar o‘zgartirildi: <b>{from_lang} → {to_lang}</b>")

@dp.message(F.text)
async def handle_text(message: types.Message):
    from_lang, to_lang = await get_user_langs(message.from_user.id)
    try:
        result = translator.translate(message.text, src=from_lang, dest=to_lang)
        await message.reply(f"📝 <b>Tarjima:</b>\n{result.text}")
    except Exception as e:
        await message.reply(f"⚠️ Tarjima muvaffaqiyatsiz: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())