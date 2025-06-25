import logging
import json
from pathlib import Path
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor

# ----------------- Настройки -----------------
API_TOKEN = "8065641616:AAHpIakr9YJk6jYPE4H_lp2CelIrh18ocNI"  # <-- вставьте свой токен
FACULTIES_FILE = Path(__file__).parent / "faculties.json"
# Русский язык добавляется автоматически, в кнопках его нет
ALL_SUBJECTS = [
    "Математика", "Физика", "Информатика", "Биология",
    "Химия", "История", "Иностранный язык", "Обществознание",
    "География", "Литература"
]
# ---------------------------------------------

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Хранилища: предметы и режим для каждого пользователя
user_subjects: dict[int, set[str]] = {}
user_mode: dict[int, str] = {}

# Загрузка данных о факультетах
with open(FACULTIES_FILE, encoding="utf-8") as f:
    FACULTIES = json.load(f)


def check_requirements(have: set[str], requirements: list) -> bool:
    """
    Проверяет, удовлетворяет ли набор have списку требований.
    Требование может быть строкой или списком альтернатив.
    """
    for req in requirements:
        if isinstance(req, list):
            if not any(r in have for r in req):
                return False
        else:
            if req not in have:
                return False
    return True


def main_keyboard() -> types.ReplyKeyboardMarkup:
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Мои ЕГЭ", "Мои факультеты")
    return kb


def subjects_keyboard(subjects: list[str]) -> types.ReplyKeyboardMarkup:
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for subj in subjects:
        kb.add(subj)
    kb.add("⏹️ Прекратить")
    return kb


@dp.message_handler(commands=["start"])
async def cmd_start(msg: types.Message):
    uid = msg.from_user.id
    subs = user_subjects.setdefault(uid, set())
    subs.add("Русский язык")
    user_mode[uid] = None

    await msg.answer("Добрый день! Я — бот-помощник по подбору факультетов МГУ.")
    await msg.answer("Я помогу тебе узнать, на какие факультеты ты можешь поступить.")

    await msg.answer(
        "Инструкция:\n\n"
        "1) Нажми «Мои ЕГЭ», чтобы посмотреть, добавить или удалить предметы ЕГЭ.\n\n"
        "2) В режиме добавления/удаления выбери предметы и нажми «⏹️ Прекратить».\n\n"
        "3) Нажми «Мои факультеты», и я покажу список, куда ты можешь подать документы!"
    )

    await msg.answer("Главное меню:", reply_markup=main_keyboard())
    logger.info(f"[{uid}] /start — приветствие и инструкция показаны")


@dp.message_handler(lambda m: m.text == "Мои ЕГЭ")
async def show_subjects(msg: types.Message):
    uid = msg.from_user.id
    have = user_subjects.setdefault(uid, set())
    if have:
        await msg.reply("Твои текущие предметы:\n" + ", ".join(sorted(have)))
    else:
        await msg.reply("У тебя ещё нет добавленных предметов.")
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Добавить предметы", "Удалить предметы")
    kb.add("Главное меню")
    await msg.answer("Что дальше?", reply_markup=kb)
    logger.info(f"[{uid}] Просмотр предметов: {have}")


@dp.message_handler(lambda m: m.text == "Добавить предметы")
async def enter_add_mode(msg: types.Message):
    uid = msg.from_user.id
    user_mode[uid] = "add"
    await msg.reply("Выбери предмет для добавления:", reply_markup=subjects_keyboard(ALL_SUBJECTS))
    logger.info(f"[{uid}] Вошёл в режим добавления")


@dp.message_handler(lambda m: m.text == "Удалить предметы")
async def enter_del_mode(msg: types.Message):
    uid = msg.from_user.id
    user_mode[uid] = "del"
    have = user_subjects.get(uid, set())
    to_del = sorted(have - {"Русский язык"})
    if not to_del:
        await msg.reply("Нечего удалять (Русский язык установлен автоматически).", reply_markup=main_keyboard())
        return
    await msg.reply("Выбери предмет для удаления:", reply_markup=subjects_keyboard(to_del))
    logger.info(f"[{uid}] Вошёл в режим удаления")


@dp.message_handler(lambda m: m.text == "⏹️ Прекратить")
async def stop_mode(msg: types.Message):
    uid = msg.from_user.id
    user_mode[uid] = None
    await msg.reply("Выход из режима редактирования.", reply_markup=main_keyboard())
    await msg.reply(
        "Чтобы узнать, на какие факультеты вы можете поступить, нажмите на кнопку «Мои факультеты»."
    )
    logger.info(f"[{uid}] Вышел из режима редактирования")


@dp.message_handler(lambda m: m.from_user.id in user_mode and user_mode[m.from_user.id] in ("add", "del"))
async def handle_add_del(msg: types.Message):
    uid = msg.from_user.id
    mode = user_mode[uid]
    subj = msg.text
    have = user_subjects.setdefault(uid, set())

    if mode == "add":
        if subj not in ALL_SUBJECTS:
            await msg.reply("Пожалуйста, выбери предмет или «⏹️ Прекратить».")
            return
        have.add(subj)
        await msg.reply(f"✅ Добавил: {subj}")
        logger.info(f"[{uid}] Добавлен предмет {subj}")
    else:
        if subj not in have or subj == "Русский язык":
            await msg.reply("Нельзя удалить этот предмет.")
            return
        have.remove(subj)
        await msg.reply(f"🗑 Удалил: {subj}")
        logger.info(f"[{uid}] Удалён предмет {subj}")


@dp.message_handler(lambda m: m.text == "Главное меню")
async def back_to_main(msg: types.Message):
    uid = msg.from_user.id
    user_mode[uid] = None
    await msg.reply("Главное меню:", reply_markup=main_keyboard())
    logger.info(f"[{uid}] Возврат в главное меню")


@dp.message_handler(lambda m: m.text == "Мои факультеты")
async def show_faculties(msg: types.Message):
    uid = msg.from_user.id
    have = user_subjects.setdefault(uid, set())
    if not have:
        await msg.reply("Сначала добавь хотя бы один предмет ЕГЭ.", reply_markup=main_keyboard())
        return

    matches = []
    for item in FACULTIES:
        reqs = item.get("requirements") or item.get("subjects") or []
        if check_requirements(have, reqs):
            matches.append(f"{item['faculty']} — {item['program']}")

    if matches:
        subj_list = ", ".join(sorted(have))
        header = f"С предметами {subj_list} можно поступить на:\n\n"
        body = "\n\n".join(matches)
        footer = (
            "\n\nБолее подробная информация о каждом из факультетов "
            "<a href=\"https://cpk.msu.ru\">ЦПК МГУ</a>."
        )
        await msg.reply(header + body + footer, reply_markup=main_keyboard(), parse_mode=ParseMode.HTML)
    else:
        await msg.reply("Пока ни одна программа не подходит.", reply_markup=main_keyboard())

    logger.info(f"[{uid}] Найдено факультетов: {len(matches)}")


async def on_startup(dp):
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Webhook удалён перед стартом polling")


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
