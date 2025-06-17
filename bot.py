import json
from pathlib import Path
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor

# =====================
# Настройки бота
# =====================

BOT_TOKEN = '8065641616:AAHpIakr9YJk6jYPE4H_lp2CelIrh18ocNI'  # ← замените на токен от @BotFather

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# =====================
# Данные ЕГЭ и фасультетов
# =====================

# Все возможные предметы ЕГЭ (можно расширить при необходимости)
EGE_SUBJECTS = [
    'Математика', 'Физика', 'Русский язык', 'Информатика',
    'Химия', 'Биология', 'История', 'Обществознание',
    'Иностранный язык', 'География', 'Литература'
]

# Хранилище предметов каждого пользователя: user_id -> список предметов
user_ege = {}

# Загрузка списка факультетов и программ из JSON
FACULTIES_FILE = Path(__file__).parent / "faculties.json"
with open(FACULTIES_FILE, "r", encoding="utf-8") as f:
    FACULTIES = json.load(f)
    # FACULTIES — список словарей:
    # { "faculty": "...", "program": "...", "subjects": ["Математика", ...] }

# =====================
# Клавиатуры
# =====================

# Главное меню
main_kb = ReplyKeyboardMarkup(resize_keyboard=True)
main_kb.add(KeyboardButton("Сданные предметы ЕГЭ"), KeyboardButton("Узнать на какие факультеты я могу поступить"))

# Меню управления ЕГЭ
ege_kb = ReplyKeyboardMarkup(resize_keyboard=True)
ege_kb.add(KeyboardButton("➕ Добавить предметы"), KeyboardButton("➖ Удалить предметы"))
ege_kb.add(KeyboardButton("🔙 Назад"))

# =====================
# Хэндлеры
# =====================

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я помогу тебе узнать, куда ты можешь поступить по ЕГЭ.",
        reply_markup=main_kb
    )

@dp.message_handler(lambda m: m.text == "Сданные предметы ЕГЭ")
async def show_ege(message: types.Message):
    user_id = message.from_user.id
    subjects = user_ege.get(user_id, [])
    if subjects:
        await message.answer(f"Ты добавил: {', '.join(subjects)}", reply_markup=ege_kb)
    else:
        await message.answer("У тебя пока нет добавленных предметов.", reply_markup=ege_kb)

@dp.message_handler(lambda m: m.text == "➕ Добавить предметы")
async def add_subjects(message: types.Message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for subj in EGE_SUBJECTS:
        markup.insert(KeyboardButton(subj))
    markup.add(KeyboardButton("✅ Готово"))
    await message.answer("Выбери предметы ЕГЭ (нажми несколько раз, чтобы добавить несколько):", reply_markup=markup)

@dp.message_handler(lambda m: m.text in EGE_SUBJECTS)
async def save_subject(message: types.Message):
    user_id = message.from_user.id
    user_ege.setdefault(user_id, [])
    if message.text not in user_ege[user_id]:
        user_ege[user_id].append(message.text)
        await message.answer(f"{message.text} добавлен.")
    else:
        await message.answer(f"{message.text} уже есть в списке.")

@dp.message_handler(lambda m: m.text == "✅ Готово")
async def done_adding(message: types.Message):
    await message.answer("ОК, возвращаюсь в меню ЕГЭ.", reply_markup=ege_kb)

@dp.message_handler(lambda m: m.text == "➖ Удалить предметы")
async def delete_subjects(message: types.Message):
    user_id = message.from_user.id
    current = user_ege.get(user_id, [])
    if not current:
        await message.answer("У тебя нет предметов для удаления.", reply_markup=ege_kb)
        return

    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for subj in current:
        markup.insert(KeyboardButton(f"Удалить {subj}"))
    markup.add(KeyboardButton("✅ Готово"))
    await message.answer("Выбери предметы для удаления:", reply_markup=markup)

@dp.message_handler(lambda m: m.text.startswith("Удалить "))
async def remove_subject(message: types.Message):
    user_id = message.from_user.id
    subject = message.text.replace("Удалить ", "")
    if subject in user_ege.get(user_id, []):
        user_ege[user_id].remove(subject)
        await message.answer(f"{subject} удалён.")
    else:
        await message.answer("Не могу удалить — нет такого предмета.")

@dp.message_handler(lambda m: m.text == "Узнать на какие факультеты я могу поступить")
async def show_faculties(message: types.Message):
    user_id = message.from_user.id
    user_subjects = set(user_ege.get(user_id, []))
    if not user_subjects:
        await message.answer("Сначала добавь хотя бы один предмет ЕГЭ.", reply_markup=main_kb)
        return

    matches = []
    for item in FACULTIES:
        required = set(item["subjects"])
        if required.issubset(user_subjects):
            matches.append(f"🏛 {item['faculty']} — {item['program']}")

    if matches:
        await message.answer("Ты можешь поступать на:\n\n" + "\n".join(matches), reply_markup=main_kb)
    else:
        await message.answer("Пока ни одна программа не подходит под твои предметы.", reply_markup=main_kb)

@dp.message_handler(lambda m: m.text == "🔙 Назад")
async def back_to_main(message: types.Message):
    await message.answer("Главное меню:", reply_markup=main_kb)

# =====================
# Запуск бота
# =====================

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
