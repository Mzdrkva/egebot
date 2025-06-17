import logging
import json
from pathlib import Path
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# ----------------- Настройки -----------------
API_TOKEN = "8065641616:AAHpIakr9YJk6jYPE4H_lp2CelIrh18ocNI"  # <-- вставьте свой токен

# Путь к JSON с факультетами
FACULTIES_FILE = Path(__file__).parent / "faculties.json"

# Все допустимые предметы ЕГЭ
ALL_SUBJECTS = [
    "Математика", "Физика", "Русский язык", "Информатика", "Биология",
    "Химия", "История", "Иностранный язык", "Обществознание", "География",
    "Литература"
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
    user_subjects.setdefault(uid, set())
    user_mode[uid] = None

    # Первое сообщение с инструкцией
    instruction = (
        "👋 Добро пожаловать!\n\n"
        "📋 Инструкция:\n"
        "1) Нажмите «✅ Сданные предметы ЕГЭ», чтобы добавить или удалить предметы.\n"
        "2) В режиме добавления/удаления выберите нужные предметы и нажмите «⏹ Прекратить».\n"
        "3) Нажмите «🎓 Узнать на какие факультеты», чтобы получить список факультетов.\n"
    )
    await msg.answer(instruction)

    # Затем выводим главное меню
    await msg.answer("Главное меню:", reply_markup=main_keyboard())
    logger.info(f"[{uid}] /start — отправлена инструкция и главное меню")

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
    logger.info(f"[{uid}] Режим добавления активирован")

@dp.message_handler(lambda m: m.text == "➖ Удалить предметы")
async def enter_del_mode(msg: types.Message):
    uid = msg.from_user.id
    user_mode[uid] = "del"
    await msg.reply("Выбери предмет для удаления (или «⏹ Прекратить»):", reply_markup=subjects_keyboard())
    logger.info(f"[{uid}] Режим удаления активирован")

@dp.message_handler(lambda m: m.text == "⏹ Прекратить")
async def stop_mode(msg: types.Message):
    uid = msg.from_user.id
    user_mode[uid] = None
    await msg.reply("Выход из режима редактирования.", reply_markup=main_keyboard())
    logger.info(f"[{uid}] Режим редактирования завершён")

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
        logger.info(f"[{uid}] Добавлен предмет: {subj}")
    else:
        if subj in have:
            have.remove(subj)
            await msg.reply(f"🗑 Удалил: {subj}")
            logger.info(f"[{uid}] Удалён предмет: {subj}")
        else:
            await msg.reply(f"⚠️ У тебя нет предмета «{subj}».")

@dp.message_handler(lambda m: m.text == "⏹ Главное меню")
async def back_to_main(msg: types.Message):
    uid = msg.from_user.id
    user_mode[uid] = None
    await msg.reply("Главное меню:", reply_markup=main_keyboard())
    logger.info(f"[{uid}] Возврат к главному меню")

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

# --- Запуск polling с удалением webhook ---

async def on_startup(dp: Dispatcher):
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Webhook удалён перед стартом polling")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
