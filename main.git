import asyncio
import re
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
)

# ======================= НАСТРОЙКИ =======================
BOT_TOKEN = "8728570016:AAGVl3SWOh7nUus8TqdItOAJLlgdiwvEwdo"
ADMIN_IDS = [8471049849, 7297564960]  # ID двух администраторов
# =========================================================

router = Router()

# Хранилища (в памяти; для прода — БД)
cooldowns: dict[int, datetime] = {}     # user_id -> время, до которого нельзя подать заявку
user_forms: dict[int, dict] = {}        # user_id -> анкета


class Form(StatesGroup):
    name = State()
    link = State()
    tg = State()
    views = State()
    confirm = State()
    edit_choice = State()
    edit_value = State()


# ---------------------- КЛАВИАТУРЫ ----------------------
def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Стать Media", callback_data="become_media")],
        [InlineKeyboardButton(text="О нас", callback_data="about")],
    ])


def confirm_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Да", callback_data="confirm_yes")]
    ])


def check_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Проверить", callback_data="check")]
    ])


def final_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Я все правильно заполнил", callback_data="form_ok")],
        [InlineKeyboardButton(text="Я ошибся", callback_data="form_err")],
    ])


def edit_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1", callback_data="edit_1")],
        [InlineKeyboardButton(text="2", callback_data="edit_2")],
        [InlineKeyboardButton(text="3", callback_data="edit_3")],
        [InlineKeyboardButton(text="4", callback_data="edit_4")],
    ])


def admin_kb(user_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Давай", callback_data=f"adm_go:{user_id}")]
    ])


def admin_decision_kb(user_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Принять", callback_data=f"adm_accept:{user_id}")],
        [InlineKeyboardButton(text="Отклонить", callback_data=f"adm_reject:{user_id}")],
        [InlineKeyboardButton(text="Рассмотрение", callback_data=f"adm_pending:{user_id}")],
    ])


# ---------------------- УТИЛИТЫ ----------------------
def format_form(d: dict) -> str:
    return (
        "📋 <b>Анкета:</b>\n"
        f"1. Имя: {d.get('name')}\n"
        f"2. TikTok/YouTube: {d.get('link')}\n"
        f"3. ТГ для связи: {d.get('tg')}\n"
        f"4. Просмотры: {d.get('views')}"
    )


def valid_link(text: str) -> bool:
    return text.startswith("https://youtube.com/") or text.startswith("https://www.tiktok.com/")


def valid_views(text: str) -> bool:
    return text.isdigit() and int(text) >= 350


ABOUT_TEXT = (
    "маленький путеводитель\n\n"
    "наш чат - https://t.me/+jLZPPE0LRbYyZTQ0\n\n"
    "наш канал - https://t.me/lexoravisuals\n\n"
    "скачать мод с тгк - https://t.me/lexora_up\n\n"
    "наш сайт - http://Lexoravisuals.fun/\n\n"
    "вопросник мода - https://t.me/+OVTkAXO_-9I4ZjUy\n\n"
    "DevLogs канал со спойлерами - https://t.me/DEVlexoravisuals\n\n\n"
    "спасибо за внимание с уважением Lexora Visuals!"
)


async def notify_admins(bot: Bot, user_id: int, username: str | None, data: dict):
    user_tag = f"@{username}" if username else f"id{user_id}"
    text = f"пользователь {user_tag} подал заявку на сотрудничество проверим ее?"
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text, reply_markup=admin_kb(user_id))
        except Exception:
            pass


# ---------------------- ХЕНДЛЕРЫ ----------------------
@router.message(CommandStart())
async def start(msg: Message):
    await msg.answer(
        "Привет я Медиа-Менеджер, я могу тебе помочь с чем либо? "
        "если да выбери что-то из пунктов ниже.",
        reply_markup=main_kb()
    )


@router.callback_query(F.data == "about")
async def about(cb: CallbackQuery):
    await cb.message.answer(ABOUT_TEXT)
    await cb.answer()


@router.callback_query(F.data == "become_media")
async def become_media(cb: CallbackQuery):
    user_id = cb.from_user.id
    # проверка кулдауна после отказа
    if user_id in cooldowns:
        remaining = cooldowns[user_id] - datetime.now()
        if remaining.total_seconds() > 0:
            days = remaining.days
            hours = remaining.seconds // 3600
            await cb.message.answer(
                f"ваша заявка отклонена попробуйте подать через {days} д. и {hours} ч.!"
            )
            await cb.answer()
            return
        else:
            del cooldowns[user_id]

    await cb.message.answer("ты уверен в этом?", reply_markup=confirm_kb())
    await cb.answer()


@router.callback_query(F.data == "confirm_yes")
async def confirm_yes(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.answer("тогда заполни анкету!\n\n1. ваше имя:")
    await state.set_state(Form.name)
    await cb.answer()


# ---------------------- ЗАПОЛНЕНИЕ АНКЕТЫ ----------------------
@router.message(StateFilter(Form.name))
async def get_name(msg: Message, state: FSMContext):
    await state.update_data(name=msg.text.strip())
    await msg.answer("2. ваш тик-ток/Ютуб (ссылка должна начинаться на https://youtube.com/ или https://www.tiktok.com/):")
    await state.set_state(Form.link)


@router.message(StateFilter(Form.link))
async def get_link(msg: Message, state: FSMContext):
    text = msg.text.strip()
    if not valid_link(text):
        await msg.answer("❌ ссылка должна начинаться на https://youtube.com/ или https://www.tiktok.com/. попробуйте ещё раз:")
        return
    await state.update_data(link=text)
    await msg.answer("3. ваш ТГ для связи:")
    await state.set_state(Form.tg)


@router.message(StateFilter(Form.tg))
async def get_tg(msg: Message, state: FSMContext):
    await state.update_data(tg=msg.text.strip())
    await msg.answer("4. число ваших просмотров (от 350):")
    await state.set_state(Form.views)


@router.message(StateFilter(Form.views))
async def get_views(msg: Message, state: FSMContext):
    text = msg.text.strip()
    if not valid_views(text):
        await msg.answer("❌ число просмотров должно быть числом и не меньше 350. попробуйте ещё раз:")
        return
    await state.update_data(views=text)
    await msg.answer("проверьте все правильно?", reply_markup=check_kb())
    await state.set_state(Form.confirm)


@router.callback_query(F.data == "check", StateFilter(Form.confirm))
async def check(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await cb.message.answer(format_form(data), reply_markup=final_kb())
    await cb.answer()


# ---------------------- ПОДТВЕРЖДЕНИЕ ----------------------
@router.callback_query(F.data == "form_ok", StateFilter(Form.confirm))
async def form_ok(cb: CallbackQuery, state: FSMContext):
    user_id = cb.from_user.id
    data = await state.get_data()
    user_forms[user_id] = dict(data)  # сохраняем анкету
    await cb.message.answer("отлично анкета отправлена администратору")
    await notify_admins(cb.bot, user_id, cb.from_user.username, data)
    await state.clear()
    await cb.answer()


@router.callback_query(F.data == "form_err", StateFilter(Form.confirm))
async def form_err(cb: CallbackQuery, state: FSMContext):
    await cb.message.answer("ой ты ошибся? бывает!")
    await cb.message.answer(
        "какой пункт ты написал не правильно выбери от 1 до 4",
        reply_markup=edit_kb()
    )
    await state.set_state(Form.edit_choice)
    await cb.answer()


@router.callback_query(F.data.startswith("edit_"), StateFilter(Form.edit_choice))
async def edit_choice(cb: CallbackQuery, state: FSMContext):
    num = cb.data.split("_")[1]
    await state.update_data(edit_num=num)
    await cb.message.answer(f"введи правильный ответ пункта {num}")
    await state.set_state(Form.edit_value)
    await cb.answer()


@router.message(StateFilter(Form.edit_value))
async def edit_value(msg: Message, state: FSMContext):
    data = await state.get_data()
    num = data.get("edit_num")
    text = msg.text.strip()

    if num == "2" and not valid_link(text):
        await msg.answer("❌ ссылка должна начинаться на https://youtube.com/ или https://www.tiktok.com/. попробуйте ещё раз:")
        return
    if num == "4" and not valid_views(text):
        await msg.answer("❌ число просмотров должно быть числом и не меньше 350. попробуйте ещё раз:")
        return

    key_map = {"1": "name", "2": "link", "3": "tg", "4": "views"}
    data[key_map[num]] = text
    await state.update_data(**data)

    user_id = msg.from_user.id
    user_forms[user_id] = dict(data)

    await msg.answer("отлично анкета отправлена администратору")
    await notify_admins(msg.bot, user_id, msg.from_user.username, data)
    await state.clear()


# ---------------------- ДЕЙСТВИЯ АДМИНА ----------------------
@router.callback_query(F.data.startswith("adm_go:"))
async def adm_go(cb: CallbackQuery):
    if cb.from_user.id not in ADMIN_IDS:
        await cb.answer("нет доступа", show_alert=True)
        return
    user_id = int(cb.data.split(":")[1])
    data = user_forms.get(user_id)
    if not data:
        await cb.answer("анкета не найдена", show_alert=True)
        return
    await cb.message.answer(format_form(data), reply_markup=admin_decision_kb(user_id))
    await cb.answer()


@router.callback_query(F.data.startswith("adm_accept:"))
async def adm_accept(cb: CallbackQuery):
    if cb.from_user.id not in ADMIN_IDS:
        await cb.answer("нет доступа", show_alert=True)
        return
    user_id = int(cb.data.split(":")[1])
    try:
        await cb.bot.send_message(
            user_id,
            "вы приняты на сотрудничество скоро вам напишет менеджер"
        )
    except Exception:
        pass
    await cb.message.answer("✅ Принято.")
    user_forms.pop(user_id, None)
    await cb.answer()


@router.callback_query(F.data.startswith("adm_reject:"))
async def adm_reject(cb: CallbackQuery):
    if cb.from_user.id not in ADMIN_IDS:
        await cb.answer("нет доступа", show_alert=True)
        return
    user_id = int(cb.data.split(":")[1])
    cooldowns[user_id] = datetime.now() + timedelta(days=3)  # блок на 3 дня
    try:
        await cb.bot.send_message(
            user_id,
            "ваша заявка отклонена администратором попробуйте подать через 3 дня"
        )
    except Exception:
        pass
    await cb.message.answer("❌ Отклонено.")
    user_forms.pop(user_id, None)
    await cb.answer()


@router.callback_query(F.data.startswith("adm_pending:"))
async def adm_pending(cb: CallbackQuery):
    if cb.from_user.id not in ADMIN_IDS:
        await cb.answer("нет доступа", show_alert=True)
        return
    user_id = int(cb.data.split(":")[1])
    try:
        await cb.bot.send_message(
            user_id,
            "ваша анкета на рассмотрении менеджер напишет вам если вас примут"
        )
    except Exception:
        pass
    await cb.message.answer("⏳ Отмечено как «рассмотрение».")
    await cb.answer()


# ---------------------- ЗАПУСК ----------------------
async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
