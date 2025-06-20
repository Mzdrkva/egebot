import logging
import json
from pathlib import Path
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# ----------------- Настройки -----------------
API_TOKEN = "8065641616:AAHpIakr9YJk6jYPE4H_lp2CelIrh18ocNI"  # <-- вставьте свой токен

# Путь к JSON с факультетами
FACULTIES_FILE = Path(__file__).parent / "faculties.json"

# Все допустимые предметы ЕГЭ (без «Русский язык»)
ALL_SUBJECTS = [
    "Математика", "Физика", "Информатика", "Биология",
    "Химия", "История", "Иностранный язык", "Обществознание",
    "География", "Литература"
]
# ---------------------------------------------

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Хранилище: user_id → set предметов, user_id → режим ("add", "del", None)
user_subjects: dict[int, set[str]] = {}
user_mode: dict[int, str] = {}

# Загрузка списка факультетов из JSON
with open(FACULTIES_FILE, encoding="utf-8") as f:
    FACULTIES = json.load(f)

# --- Вспомогательные функции ---

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
    # Гарантируем, что у пользователя есть запись и сразу добавляем "Русский язык"
    subjects = user_subjects.setdefault(uid, set())
    subjects.add("Русский язык")
    user_mode[uid] = None

    # Первое приветствие с описанием возможностей
    await msg.answer(
        "👋 Привет! Я — бот-помощник по подбору факультетов МГУ.\n"
        "Я помогу тебе:\n"
        "- Добавить и удалить твои сданные ЕГЭ-предметы;\n"
        "- Узнать, на какие факультеты ты можешь поступить по этим предметам.\n"
    )
    # Далее инструкция
    await msg.answer(
        "📋 Инструкция:\n"
        "1) Нажми «✅ Сданные предметы ЕГЭ», чтобы посмотреть или отредактировать твои предметы (русский проставлен автоматически).\n"
        "2) В режиме добавления/удаления выбери предметы и нажми «⏹ Прекратить».\n"
        "3) Нажми «🎓 Узнать на какие факультеты» — и я покажу список!\n"
    )
    # Главное меню
    await msg.answer("Главное меню:", reply_markup=main_keyboard())
    logger.info(f"[{uid}] /start — пользователь вошел, русский язык добавлен")

@dp.message_handler(lambda m: m.text == "✅ Сданные предметы ЕГЭ")
async def show_subjects(msg: types.Message):
    uid = msg.from_user.id
    have = user_subjects.setdefault(uid, set())
    if have:
        await msg.reply("Твои текущие предметы:\n" + ", ".join(sorted(have)))
    else:
        await msg.reply("У тебя ещё нет добавленных предметов.")
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ Добавить предметы", "➖ Удалить предметы")
    kb.add("⏹ Главное меню")
    await msg.answer("Что дальше?", reply_markup=kb)
    logger.info(f"[{uid}] Просмотр предметов: {have}")

@dp.message_handler(lambda m: m.text == "➕ Добавить предметы")
async def enter_add_mode(msg: types.Message):
    uid = msg.from_user.id
    user_mode[uid] = "add"
    await msg.reply("Выбери предмет для добавления (или «⏹ Прекратить»):", reply_markup=subjects_keyboard())
    logger.info(f"[{uid}] Вошёл в режим добавления")

@dp.message_handler(lambda m: m.text == "➖ Удалить предметы")
async def enter_del_mode(msg: types.Message):
    uid = msg.from_user.id
    user_mode[uid] = "del"
    await msg.reply("Выбери предмет для удаления (или «⏹ Прекратить»):", reply_markup=subjects_keyboard())
    logger.info(f"[{uid}] Вошёл в режим удаления")

@dp.message_handler(lambda m: m.text == "⏹ Прекратить")
async def stop_mode(msg: types.Message):
    uid = msg.from_user.id
    user_mode[uid] = None
    await msg.reply("Выход из режима редактирования.", reply_markup=main_keyboard())
    logger.info(f"[{uid}] Вышел из режима редактирования")

@dp.message_handler(lambda m: m.from_user.id in user_mode and user_mode[m.from_user.id] in ("add","del"))
async def handle_add_del(msg: types.Message):
    uid = msg.from_user.id
    mode = user_mode[uid]
    subj = msg.text

    if subj not in ALL_SUBJECTS:
        await msg.reply("Пожалуйста, выбери предмет из списка или «⏹ Прекратить».")
        return

    have = user_subjects.setdefault(uid, set())
    if mode == "add":
        have.add(subj)
        await msg.reply(f"✅ Добавил: {subj}")
        logger.info(f"[{uid}] Добавил предмет: {subj}")
    else:
        if subj in have:
            have.remove(subj)
            await msg.reply(f"🗑 Удалил: {subj}")
            logger.info(f"[{uid}] Удалил предмет: {subj}")
        else:
            await msg.reply(f"⚠️ У тебя нет предмета «{subj}».")

@dp.message_handler(lambda m: m.text == "⏹ Главное меню")
async def back_to_main(msg: types.Message):
    uid = msg.from_user.id
    user_mode[uid] = None
    await msg.reply("Главное меню:", reply_markup=main_keyboard())
    logger.info(f"[{uid}] Возврат в главное меню")

@dp.message_handler(lambda m: m.text == "🎓 Узнать на какие факультеты")
async def show_faculties(msg: types.Message):
    uid = msg.from_user.id
    have = user_subjects.setdefault(uid, set())
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
    logger.info(f"[{uid}] Найдено факультетов: {len(matches)}")

# --- Запуск polling с удалением webhook перед стартом ---

async def on_startup(dp):
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Webhook удалён перед стартом polling")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
