import logging
import json
import asyncio
from pathlib import Path
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# ----------------- Настройки -----------------
API_TOKEN = "8065641616:AAHpIakr9YJk6jYPE4H_lp2CelIrh18ocNI"  # <-- вставьте свой токен
FACULTIES_FILE = Path(__file__).parent / "faculties.json"
ALL_SUBJECTS = [
    "Математика", "Физика", "Русский язык", "Информатика", "Биология",
    "Химия", "История", "Иностранный язык", "Обществознание", "География",
    "Литература"
]
# ---------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация и удаление вебхука _до_ старта polling
bot = Bot(token=API_TOKEN)
# Синхронно удаляем webhook, чтобы избежать конфликта
asyncio.run(bot.delete_webhook(drop_pending_updates=True))
logger.info("Webhook (if any) deleted before polling start")

dp = Dispatcher(bot)

# Загружаем данные факультетов
with open(FACULTIES_FILE, encoding="utf-8") as f:
    FACULTIES = json.load(f)

# Хранилище: user_subjects и режим работы
user_subjects: dict[int, set[str]] = {}
user_mode: dict[int, str] = {}

# --- Утилиты ---
def check_requirements(have: set[str], requirements: list):
    for req in requirements:
        if isinstance(req, list):
            if not any(r in have for r in req):
                return False
        else:
            if req not in have:
                return False
    return True

def main_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("✅ Сданные предметы ЕГЭ", "🎓 Узнать на какие факультеты")
    return kb

def subjects_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for subj in ALL_SUBJECTS:
        kb.add(subj)
    kb.add("⏹ Прекратить")
    return kb

# --- Обработчики ---
@dp.message_handler(commands=["start"])
async def cmd_start(msg: types.Message):
    uid = msg.from_user.id
    user_subjects.setdefault(uid, set())
    user_mode[uid] = None
    await msg.reply(
        "Привет!\nЯ помогу тебе узнать, на какие факультеты ты можешь поступить по твоим результатам ЕГЭ.\n\n"
        "Выбери действие:",
        reply_markup=main_keyboard()
    )
    logger.info(f"[{uid}] /start — режим сброшен.")

@dp.message_handler(lambda m: m.text == "✅ Сданные предметы ЕГЭ")
async def show_subjects(msg: types.Message):
    uid = msg.from_user.id
    have = user_subjects.setdefault(uid, set())
    logger.info(f"[{uid}] Показать предметы: {have}")
    if have:
        await msg.reply("Твои текущие предметы:\n" + ", ".join(sorted(have)))
    else:
        await msg.reply("У тебя ещё нет добавленных предметов.")
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ Добавить предметы", "➖ Удалить предметы")
    kb.add("⏹ Главное меню")
    await msg.answer("Что дальше?", reply_markup=kb)

@dp.message_handler(lambda m: m.text == "➕ Добавить предметы")
async def enter_add_mode(msg: types.Message):
    uid = msg.from_user.id
    user_mode[uid] = "add"
    logger.info(f"[{uid}] Вошёл в режим ADD")
    await msg.reply("Выбери предмет для добавления (или «⏹ Прекратить»):", reply_markup=subjects_keyboard())

@dp.message_handler(lambda m: m.text == "➖ Удалить предметы")
async def enter_del_mode(msg: types.Message):
    uid = msg.from_user.id
    user_mode[uid] = "del"
    logger.info(f"[{uid}] Вошёл в режим DEL")
    await msg.reply("Выбери предмет для удаления (или «⏹ Прекратить»):", reply_markup=subjects_keyboard())

@dp.message_handler(lambda m: m.text == "⏹ Прекратить")
async def stop_mode(msg: types.Message):
    uid = msg.from_user.id
    user_mode[uid] = None
    logger.info(f"[{uid}] Вышел из режима редактирования")
    await msg.reply("Выход из режима редактирования.", reply_markup=main_keyboard())

@dp.message_handler(lambda m: m.from_user.id in user_mode and user_mode[m.from_user.id] in ("add","del"))
async def handle_add_del(msg: types.Message):
    uid = msg.from_user.id
    mode = user_mode[uid]
    text = msg.text
    logger.info(f"[{uid}] handle_add_del mode={mode} text={text!r}")

    if text not in ALL_SUBJECTS:
        await msg.reply("Пожалуйста, выбери предмет из списка или «⏹ Прекратить».")
        return

    have = user_subjects.setdefault(uid, set())
    if mode == "add":
        have.add(text)
        await msg.reply(f"✅ Добавил: {text}")
    else:
        if text in have:
            have.remove(text)
            await msg.reply(f"🗑 Удалил: {text}")
        else:
            await msg.reply(f"⚠️ У тебя нет предмета «{text}».")

    logger.info(f"[{uid}] Новые предметы: {have}")

@dp.message_handler(lambda m: m.text == "⏹ Главное меню")
async def back_to_main(msg: types.Message):
    uid = msg.from_user.id
    user_mode[uid] = None
    logger.info(f"[{uid}] Главное меню")
    await msg.reply("Главное меню:", reply_markup=main_keyboard())

@dp.message_handler(lambda m: m.text == "🎓 Узнать на какие факультеты")
async def show_faculties(msg: types.Message):
    uid = msg.from_user.id
    have = user_subjects.setdefault(uid, set())
    logger.info(f"[{uid}] show_faculties with {have}")
    if not have:
        await msg.reply("Сначала добавь хотя бы один предмет ЕГЭ.", reply_markup=main_keyboard())
        return

    matches = []
    for item in FACULTIES:
        reqs = item.get("requirements", [])
        if check_requirements(have, reqs):
            matches.append(f"🏛 {item['faculty']} — {item['program']}")

    if matches:
        await msg.reply("Ты можешь поступать на:\n\n" + "\n".join(matches), reply_markup=main_keyboard())
    else:
        await msg.reply("Пока ни одна программа не подходит.", reply_markup=main_keyboard())

# --- Запуск polling ---
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
