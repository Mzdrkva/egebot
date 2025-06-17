import logging
import json
from pathlib import Path
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# ----------------- Настройки -----------------
API_TOKEN = "ВАШ_BOT_TOKEN_HERE"  # <-- вставьте свой токен

# Путь к JSON с факультетами
FACULTIES_FILE = Path(__file__).parent / "faculties.json"

# Всё допустимые предметы ЕГЭ (можете расширить этот список)
ALL_SUBJECTS = [
    "Математика", "Физика", "Русский язык", "Информатика", "Биология",
    "Химия", "История", "Иностранный язык", "Обществознание", "География"
]
# ---------------------------------------------

# Логирование
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Пользовательские данные хранятся в памяти (для демо). 
# key: user_id, value: set добавленных предметов
user_subjects: dict[int, set[str]] = {}
# key: user_id, value: режим ("add", "del" или None)
user_mode: dict[int, str] = {}

# Загрузка списка факультетов
with open(FACULTIES_FILE, encoding="utf-8") as f:
    FACULTIES = json.load(f)

# --- Утилиты ---
def parse_requirements(raw: list):
    """
    Проверяет, выполняет ли набор пользовательских предметов raw
    все требования одной программы.
    requirements может быть: строка или список альтернатив.
    """
    have = set(raw)
    for req in raw: pass  # just for type hint
    # not used

def check_requirements(have: set[str], requirements: list):
    """
    requirements: list элементов, где
      - элемент = str ― обязательный предмет
      - элемент = list[str] ― нужно хотя бы один из списка
    """
    for req in requirements:
        if isinstance(req, list):
            # проверяем, что есть хотя бы один из альтернатив
            if not any(r in have for r in req):
                return False
        else:
            # обычное требование
            if req not in have:
                return False
    return True

def main_keyboard() -> types.ReplyKeyboardMarkup:
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("✅ Сданные предметы ЕГЭ", "🎓 Узнать на какие факультеты")
    return kb

def subjects_keyboard() -> types.ReplyKeyboardMarkup:
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for subj in ALL_SUBJECTS:
        kb.add(subj)
    kb.add("⏹ Прекратить")
    return kb

# --- Обработчики ---
@dp.message_handler(commands=["start"])
async def cmd_start(msg: types.Message):
    user_subjects.setdefault(msg.from_user.id, set())
    user_mode[msg.from_user.id] = None
    await msg.reply(
        "Привет!\nЯ помогу тебе узнать, на какие факультеты ты можешь поступить по твоим результатам ЕГЭ.\n\n"
        "Выбери действие:",
        reply_markup=main_keyboard()
    )

@dp.message_handler(lambda m: m.text == "✅ Сданные предметы ЕГЭ")
async def show_subjects(msg: types.Message):
    uid = msg.from_user.id
    have = user_subjects.get(uid, set())
    if have:
        await msg.reply("Твои текущие предметы:\n" + ", ".join(sorted(have)))
    else:
        await msg.reply("У тебя ещё нет добавленных предметов.")
    # Предложим добавить или удалить
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ Добавить предметы", "➖ Удалить предметы")
    kb.add("⏹ Главное меню")
    await msg.answer("Что дальше?", reply_markup=kb)

@dp.message_handler(lambda m: m.text == "➕ Добавить предметы")
async def enter_add_mode(msg: types.Message):
    uid = msg.from_user.id
    user_mode[uid] = "add"
    await msg.reply("Выбери предмет, чтобы добавить:\n(или «⏹ Прекратить»)", reply_markup=subjects_keyboard())

@dp.message_handler(lambda m: m.text == "➖ Удалить предметы")
async def enter_del_mode(msg: types.Message):
    uid = msg.from_user.id
    user_mode[uid] = "del"
    await msg.reply("Выбери предмет, чтобы удалить:\n(или «⏹ Прекратить»)", reply_markup=subjects_keyboard())

@dp.message_handler(lambda m: m.text == "⏹ Прекратить")
async def stop_mode(msg: types.Message):
    uid = msg.from_user.id
    user_mode[uid] = None
    await msg.reply("Выход из режима редактирования.", reply_markup=main_keyboard())

@dp.message_handler(lambda m: m.from_user.id in user_mode and user_mode[m.from_user.id] in ("add","del"))
async def handle_add_del(msg: types.Message):
    uid = msg.from_user.id
    mode = user_mode[uid]
    text = msg.text

    if text not in ALL_SUBJECTS:
        await msg.reply("Пожалуйста, выбери предмет из списка или «⏹ Прекратить».")
        return

    if mode == "add":
        user_subjects[uid].add(text)
        await msg.reply(f"Добавил: {text}")
    else:  # mode == "del"
        if text in user_subjects[uid]:
            user_subjects[uid].remove(text)
            await msg.reply(f"Удалил: {text}")
        else:
            await msg.reply(f"У тебя нет предмета «{text}».")

    # Остаёмся в том же режиме, список клавиш не меняется

@dp.message_handler(lambda m: m.text == "⏹ Главное меню")
async def back_to_main(msg: types.Message):
    user_mode[msg.from_user.id] = None
    await msg.reply("Главное меню:", reply_markup=main_keyboard())

@dp.message_handler(lambda m: m.text == "🎓 Узнать на какие факультеты")
async def show_faculties(msg: types.Message):
    uid = msg.from_user.id
    have = user_subjects.get(uid, set())
    if not have:
        await msg.reply("Сначала добавь хотя бы один предмет ЕГЭ.", reply_markup=main_keyboard())
        return

    matches = []
    for item in FACULTIES:
        reqs = item.get("requirements") or item.get("subjects") or []
        if check_requirements(have, reqs):
            matches.append(f"🏛 {item['faculty']} — {item['program']}")

    if matches:
        await msg.reply("Ты можешь поступать на:\n\n" + "\n".join(matches), reply_markup=main_keyboard())
    else:
        await msg.reply("Пока ни одна программа не подходит.", reply_markup=main_keyboard())

# --- Запуск ---
async def on_startup(dp: Dispatcher):
    # Снимаем webhook, чтобы использовать polling
    await bot.delete_webhook()
    logging.info("Webhook deleted, polling started.")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
