import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor

# Заменить на свой токен
BOT_TOKEN = 'YOUR_TOKEN_HERE'

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Предметы ЕГЭ (можно расширить)
EGE_SUBJECTS = ['Математика', 'Физика', 'Русский язык', 'Информатика', 'Химия', 'Биология', 'История', 'Обществознание', 'Иностранный язык', 'География', 'Литература']

# Хранилище данных: user_id -> список предметов
user_ege = {}

# Главное меню
main_kb = ReplyKeyboardMarkup(resize_keyboard=True)
main_kb.add(KeyboardButton("Сданные предметы ЕГЭ"), KeyboardButton("Узнать на какие факультеты я могу поступить"))

# Кнопки в разделе ЕГЭ
ege_kb = ReplyKeyboardMarkup(resize_keyboard=True)
ege_kb.add(KeyboardButton("➕ Добавить предметы"), KeyboardButton("➖ Удалить предметы"))
ege_kb.add(KeyboardButton("🔙 Назад"))

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await message.answer("Привет! Я помогу тебе узнать, куда ты можешь поступить по ЕГЭ", reply_markup=main_kb)

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
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    for subj in EGE_SUBJECTS:
        markup.add(KeyboardButton(subj))
    markup.add(KeyboardButton("✅ Готово"))
    await message.answer("Выбери предметы ЕГЭ:", reply_markup=markup)

@dp.message_handler(lambda m: m.text in EGE_SUBJECTS)
async def save_subject(message: types.Message):
    user_id = message.from_user.id
    user_ege.setdefault(user_id, [])
    if message.text not in user_ege[user_id]:
        user_ege[user_id].append(message.text)
        await message.answer(f"{message.text} добавлен.")
    else:
        await message.answer(f"{message.text} уже добавлен.")

@dp.message_handler(lambda m: m.text == "✅ Готово")
async def done_adding(message: types.Message):
    await message.answer("Готово! Возвращаюсь в меню ЕГЭ.", reply_markup=ege_kb)

@dp.message_handler(lambda m: m.text == "➖ Удалить предметы")
async def delete_subjects(message: types.Message):
    user_id = message.from_user.id
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    for subj in user_ege.get(user_id, []):
        markup.add(KeyboardButton(f"Удалить {subj}"))
    markup.add(KeyboardButton("✅ Готово"))
    await message.answer("Выбери предметы для удаления:", reply_markup=markup)

@dp.message_handler(lambda m: m.text.startswith("Удалить "))
async def remove_subject(message: types.Message):
    user_id = message.from_user.id
    subject = message.text.replace("Удалить ", "")
    if subject in user_ege.get(user_id, []):
        user_ege[user_id].remove(subject)
        await message.answer(f"{subject} удалён.")

@dp.message_handler(lambda m: m.text == "Узнать на какие факультеты я могу поступить")
async def show_faculties(message: types.Message):
    user_id = message.from_user.id
    subjects = set(user_ege.get(user_id, []))
    if not subjects:
        await message.answer("Сначала добавь хотя бы один предмет ЕГЭ.")
        return

    # Пример простой логики фильтрации (замени на реальную из PDF)
    example_faculties = {
        "Физфак": {"Математика", "Физика", "Русский язык"},
        "Филфак": {"Литература", "Русский язык", "История"},
        "Экон": {"Математика", "Обществознание", "Русский язык"}
    }

    result = []
    for name, required in example_faculties.items():
        if required.issubset(subjects):
            result.append(name)

    if result:
        await message.answer("Ты можешь поступать на:\n" + "\n".join(result))
    else:
        await message.answer("Пока ни один факультет не подходит. Попробуй добавить другие предметы.")

@dp.message_handler(lambda m: m.text == "🔙 Назад")
async def back_to_main(message: types.Message):
    await message.answer("Главное меню", reply_markup=main_kb)

# Запуск
if __name__ == "__main__":
    from aiogram import executor
    executor.start_polling(dp)
