import telebot
from telebot import types
import sqlite3
import random
from datetime import datetime, timedelta

# --- НАСТРОЙКИ ---
BOT_TOKEN = '8938905705:AAHGsCOozAcp2JHwb-3WS6-ptv_EGNyZyEU'
TGK_LINK = 'https://t.me/user_sechtgk'
DAILY_LIMIT = 3

bot = telebot.TeleBot(BOT_TOKEN)

# --- БАЗА ДАННЫХ ---
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            attempts_left INTEGER DEFAULT 3,
            last_reset TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT attempts_left, last_reset FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def update_user(user_id, attempts_left, last_reset=None):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    if last_reset:
        cursor.execute('UPDATE users SET attempts_left = ?, last_reset = ? WHERE user_id = ?',
                       (attempts_left, last_reset, user_id))
    else:
        cursor.execute('UPDATE users SET attempts_left = ? WHERE user_id = ?',
                       (attempts_left, user_id))
    conn.commit()
    conn.close()

def create_user(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('INSERT OR IGNORE INTO users (user_id, attempts_left, last_reset) VALUES (?, ?, ?)',
                   (user_id, DAILY_LIMIT, now))
    conn.commit()
    conn.close()

def check_and_reset_attempts(user_id):
    """Сбрасывает попытки раз в 24 часа."""
    row = get_user(user_id)
    if not row:
        create_user(user_id)
        return DAILY_LIMIT

    attempts_left, last_reset_str = row
    last_reset = datetime.fromisoformat(last_reset_str)

    if datetime.now() - last_reset >= timedelta(days=1):
        update_user(user_id, DAILY_LIMIT, datetime.now().isoformat())
        return DAILY_LIMIT
    return attempts_left

# --- ГЕНЕРАЦИЯ ЮЗЕРНЕЙМОВ ---
def generate_username():
    consonants = 'bcdfghjklmnpqrstvwxyz'
    vowels = 'aeiou'
    patterns = [
        lambda: random.choice(consonants) + random.choice(vowels) + random.choice(consonants) + random.choice(vowels) + random.choice(consonants),
        lambda: random.choice(consonants) + random.choice(vowels) + random.choice(consonants) + random.choice(vowels) + random.choice(vowels),
        lambda: random.choice(consonants) + random.choice(vowels) + random.choice(vowels) + random.choice(consonants) + random.choice(vowels),
        lambda: random.choice(consonants) + random.choice(consonants) + random.choice(vowels) + random.choice(consonants) + random.choice(vowels),
        lambda: random.choice(consonants) + random.choice(vowels) + random.choice(consonants) + random.choice(consonants) + random.choice(vowels),
    ]
    return random.choice(patterns)()

# --- КЛАВИАТУРЫ ---
def main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_tgk = types.InlineKeyboardButton('📢 наш тгк', url=TGK_LINK)
    btn_search = types.InlineKeyboardButton('🔍 искать username', callback_data='search')
    markup.add(btn_tgk, btn_search)
    return markup

def result_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_again = types.InlineKeyboardButton('🔄 искать ещё', callback_data='search')
    markup.add(btn_again)
    return markup

# --- ХЭНДЛЕРЫ ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    create_user(user_id)
    check_and_reset_attempts(user_id)

    text = (
        "Привет я бот ищейка Юзов составлю красивый юзернейм "
        "у тебя в день лимит 3 попытки поиска."
    )
    bot.send_message(message.chat.id, text, reply_markup=main_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == 'search')
def handle_search(call):
    user_id = call.from_user.id
    attempts_left = check_and_reset_attempts(user_id)

    if attempts_left <= 0:
        row = get_user(user_id)
        last_reset = datetime.fromisoformat(row[1])
        next_reset = last_reset + timedelta(days=1)
        seconds_left = (next_reset - datetime.now()).total_seconds()
        hours_left = max(1, int(seconds_left // 3600) + (1 if seconds_left % 3600 else 0))

        bot.answer_callback_query(call.id)
        bot.send_message(
            call.message.chat.id,
            f"🍕 попытки кончились попробуй через {hours_left} ч."
        )
        return

    # Генерируем ОДИН юзернейм за нажатие
    username = generate_username()
    new_attempts = attempts_left - 1
    update_user(user_id, new_attempts)

    text = (
        f"✈️ Вот твой username\n"
        f"@{username}\n"
        f"используй его если он тебе нравится\n\n"
        f"у тебя осталось попыток {new_attempts}"
    )

    bot.send_message(call.message.chat.id, text, reply_markup=result_keyboard())
    bot.answer_callback_query(call.id)

# --- ЗАПУСК ---
if __name__ == '__main__':
    init_db()
    print('Бот запущен...')
    bot.polling(none_stop=True)
