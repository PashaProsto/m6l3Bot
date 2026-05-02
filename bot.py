# bot.py
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import random
import requests
from config import TOKEN, WEATHER_API_KEY
from database import Database, PasswordDatabase
from generator import generate_password, generate_strong_password, check_password_strength, validate_length

bot = telebot.TeleBot(TOKEN)
db = Database()
pass_db = PasswordDatabase()
user_states = {}
games = {}
user_city = {}

def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📝 Заметки"), KeyboardButton("🔐 Пароли"))
    markup.add(KeyboardButton("🎮 Крестики-нолики"), KeyboardButton("🔑 Мои пароли"))
    markup.add(KeyboardButton("🌤 Погода"), KeyboardButton("🌤 Моя погода"))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    db.add_user(message.from_user.id, message.from_user.username or "")
    pass_db.add_user(message.from_user.id, message.from_user.username or "")
    bot.send_message(message.chat.id, f"👋 Привет, {message.from_user.first_name}!\n\n/setcity - сохранить город", reply_markup=main_menu())

@bot.message_handler(commands=['setcity'])
def set_city_cmd(message):
    user_states[message.from_user.id] = "set_city"
    bot.send_message(message.chat.id, "🌍 Напиши название города:")

@bot.message_handler(func=lambda m: m.text == "📝 Заметки")
def notes_menu(m):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("➕ Создать", callback_data="create_note"))
    markup.add(InlineKeyboardButton("📋 Список", callback_data="view_notes"))
    markup.add(InlineKeyboardButton("🗑 Удалить", callback_data="delete_note"))
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="back"))
    bot.send_message(m.chat.id, "📝 Заметки:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🔐 Пароли")
def gen_menu(m):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🎲 Простой", callback_data="simple"))
    markup.add(InlineKeyboardButton("⚡ Сильный", callback_data="strong"))
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="back"))
    bot.send_message(m.chat.id, "🔐 Выбери тип:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🔑 Мои пароли")
def my_passwords(m):
    passwords = pass_db.get_passwords(m.from_user.id, 10)
    if not passwords:
        bot.send_message(m.chat.id, "📭 Нет сохранённых паролей")
        return
    text = "🔑 *Твои пароли:*\n\n"
    for pid, pwd, length, _ in passwords:
        text += f"ID:{pid} | {pwd[:4]}***{pwd[-4:]}\n"
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🗑 Удалить", callback_data="del_pass_menu"))
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="back"))
    bot.send_message(m.chat.id, text, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🎮 Крестики-нолики")
def game_menu(m):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🤖 Против бота", callback_data="vsbot"))
    markup.add(InlineKeyboardButton("👥 2 игрока", callback_data="pvp"))
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="back"))
    bot.send_message(m.chat.id, "🎮 Выбери режим:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🌤 Погода")
def weather_ask(m):
    user_states[m.from_user.id] = "wait_city"
    bot.send_message(m.chat.id, "🌍 Напиши название города:")

@bot.message_handler(func=lambda m: m.text == "🌤 Моя погода")
def my_weather(m):
    uid = m.from_user.id
    if uid in user_city and user_city[uid]:
        get_weather(m, user_city[uid])
    else:
        bot.send_message(m.chat.id, "Город не сохранён. Используй /setcity")

def get_weather(message, city):
    if not WEATHER_API_KEY:
        bot.send_message(message.chat.id, "API ключ не настроен")
        return
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        if data.get("cod") != 200:
            bot.send_message(message.chat.id, "Город не найден")
            return
        temp = round(data["main"]["temp"])
        feels = round(data["main"]["feels_like"])
        desc = data["weather"][0]["description"].capitalize()
        humidity = data["main"]["humidity"]
        wind = data["wind"].get("speed", 0)
        text = f"🌤 *{city.capitalize()}*\n\n🌡 {temp}°C (ощущается {feels}°C)\n☁️ {desc}\n💧 Влажность: {humidity}%\n🌬 Ветер: {wind} м/с"
        bot.send_message(message.chat.id, text, parse_mode="Markdown")
    except:
        bot.send_message(message.chat.id, "Ошибка получения данных")

def init_game(chat_id, mode):
    games[chat_id] = {
        'mode': mode,
        'board': [" "]*9,
        'turn': 'X' if mode == 'pvp' else 'player',
        'over': False
    }

def check_win(board, symbol):
    wins = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
    return any(board[a]==symbol and board[b]==symbol and board[c]==symbol for a,b,c in wins)

def check_draw(board):
    return " " not in board

def bot_move(board):
    empty = [i for i in range(9) if board[i] == " "]
    if empty:
        board[random.choice(empty)] = 'O'

def get_keyboard(chat_id):
    game = games.get(chat_id)
    if not game:
        return None
    markup = InlineKeyboardMarkup(row_width=3)
    buttons = []
    for i in range(9):
        c = game['board'][i]
        b = "⬜" if c==" " else "❌" if c=="X" else "⭕"
        buttons.append(InlineKeyboardButton(b, callback_data=f"move_{i}"))
    markup.add(*buttons[:3])
    markup.add(*buttons[3:6])
    markup.add(*buttons[6:9])
    markup.add(InlineKeyboardButton("🔙 Выйти", callback_data="back"))
    return markup

def get_text(chat_id):
    game = games[chat_id]
    b = game['board']
    rows = []
    for i in range(0,9,3):
        row = ["⬜" if c==" " else "❌" if c=="X" else "⭕" for c in b[i:i+3]]
        rows.append(" │ ".join(row))
    field = "\n───┼───┼───\n".join(rows)
    if game['mode'] == 'vsbot':
        turn = "Твой ход" if game['turn'] == 'player' else "Ход бота"
    else:
        turn = "Ход ❌" if game['turn'] == 'X' else "Ход ⭕"
    return f"{field}\n\n{turn}"

@bot.callback_query_handler(func=lambda call: True)
def handle(call):
    cid = call.message.chat.id
    mid = call.message.message_id
    uid = call.from_user.id

    if call.data == "back":
        bot.edit_message_text("Главное меню", cid, mid, reply_markup=main_menu())
        bot.answer_callback_query(call.id)
        return

    if call.data == "create_note":
        user_states[uid] = "wait_note"
        bot.send_message(cid, "✏️ Введи текст заметки:")
        bot.answer_callback_query(call.id)
        return

    if call.data == "view_notes":
        notes = db.get_notes(uid)
        if not notes:
            bot.send_message(cid, "📭 Нет заметок")
        else:
            text = "📋 *Заметки:*\n\n"
            for nid, note, _ in notes:
                text += f"ID:{nid} | {note[:40]}\n"
            bot.send_message(cid, text, parse_mode="Markdown")
        bot.answer_callback_query(call.id)
        return

    if call.data == "delete_note":
        notes = db.get_notes(uid)
        if not notes:
            bot.send_message(cid, "📭 Нет заметок")
        else:
            markup = InlineKeyboardMarkup()
            for nid, note, _ in notes[:5]:
                markup.add(InlineKeyboardButton(f"🗑 {nid}", callback_data=f"del_note_{nid}"))
            markup.add(InlineKeyboardButton("🔙 Назад", callback_data="back"))
            bot.edit_message_text("🗑 Выбери заметку:", cid, mid, reply_markup=markup)
        bot.answer_callback_query(call.id)
        return

    if call.data.startswith("del_note_"):
        nid = int(call.data.split("_")[2])
        db.delete_note(nid, uid)
        bot.answer_callback_query(call.id, "✅ Удалено", show_alert=True)
        notes = db.get_notes(uid)
        if not notes:
            bot.edit_message_text("📭 Нет заметок", cid, mid)
        else:
            markup = InlineKeyboardMarkup()
            for nid, note, _ in notes[:5]:
                markup.add(InlineKeyboardButton(f"{nid}", callback_data=f"del_note_{nid}"))
            markup.add(InlineKeyboardButton("🔙 Назад", callback_data="back"))
            bot.edit_message_text("🗑 Выбери заметку:", cid, mid, reply_markup=markup)
        return

    if call.data == "simple" or call.data == "strong":
        user_states[uid] = call.data
        bot.send_message(cid, "Введи длину (4-64):")
        bot.answer_callback_query(call.id)
        return

    if call.data == "del_pass_menu":
        passwords = pass_db.get_passwords(uid, 10)
        if not passwords:
            bot.send_message(cid, "📭 Нет паролей")
        else:
            markup = InlineKeyboardMarkup()
            for pid, pwd, _, _ in passwords:
                markup.add(InlineKeyboardButton(f"🗑 ID:{pid}", callback_data=f"del_pass_{pid}"))
            markup.add(InlineKeyboardButton("🗑❌ ВСЕ", callback_data="del_all_pass"))
            markup.add(InlineKeyboardButton("🔙 Назад", callback_data="back"))
            bot.edit_message_text("🗑 Выбери пароль:", cid, mid, reply_markup=markup)
        bot.answer_callback_query(call.id)
        return

    if call.data.startswith("del_pass_"):
        pid = int(call.data.split("_")[2])
        pass_db.delete_password(pid, uid)
        bot.answer_callback_query(call.id, "✅ Удалено", show_alert=True)
        my_passwords(call.message)
        return

    if call.data == "del_all_pass":
        pass_db.delete_all_passwords(uid)
        bot.answer_callback_query(call.id, "✅ Все удалены", show_alert=True)
        my_passwords(call.message)
        return

    if call.data == "vsbot":
        init_game(cid, 'vsbot')
        bot.edit_message_text(get_text(cid), cid, mid, parse_mode="Markdown", reply_markup=get_keyboard(cid))
        bot.answer_callback_query(call.id)
        return

    if call.data == "pvp":
        init_game(cid, 'pvp')
        bot.edit_message_text(get_text(cid), cid, mid, parse_mode="Markdown", reply_markup=get_keyboard(cid))
        bot.answer_callback_query(call.id)
        return

    if call.data.startswith("move_"):
        cell = int(call.data.split("_")[1])
        game = games.get(cid)
        if not game or game['over']:
            bot.answer_callback_query(call.id, "Игра окончена", show_alert=True)
            return

        if game['mode'] == 'vsbot':
            if game['turn'] != 'player':
                bot.answer_callback_query(call.id, "Не твой ход", show_alert=True)
                return
            if game['board'][cell] != " ":
                bot.answer_callback_query(call.id, "Занято", show_alert=True)
                return

            game['board'][cell] = 'X'
            if check_win(game['board'], 'X'):
                game['over'] = True
                bot.edit_message_text(f"{get_text(cid)}\n\nТы победил!", cid, mid, parse_mode="Markdown", reply_markup=get_keyboard(cid))
                bot.answer_callback_query(call.id)
                return
            if check_draw(game['board']):
                game['over'] = True
                bot.edit_message_text(f"{get_text(cid)}\n\nНичья!", cid, mid, parse_mode="Markdown", reply_markup=get_keyboard(cid))
                bot.answer_callback_query(call.id)
                return

            game['turn'] = 'bot'
            bot.edit_message_text(get_text(cid), cid, mid, parse_mode="Markdown", reply_markup=get_keyboard(cid))

            bot_move(game['board'])
            if check_win(game['board'], 'O'):
                game['over'] = True
                bot.edit_message_text(f"{get_text(cid)}\n\nБот победил!", cid, mid, parse_mode="Markdown", reply_markup=get_keyboard(cid))
            elif check_draw(game['board']):
                game['over'] = True
                bot.edit_message_text(f"{get_text(cid)}\n\nНичья!", cid, mid, parse_mode="Markdown", reply_markup=get_keyboard(cid))
            else:
                game['turn'] = 'player'
                bot.edit_message_text(get_text(cid), cid, mid, parse_mode="Markdown", reply_markup=get_keyboard(cid))
            bot.answer_callback_query(call.id)
            return

        else:
            if game['board'][cell] != " ":
                bot.answer_callback_query(call.id, "Занято", show_alert=True)
                return

            game['board'][cell] = game['turn']
            if check_win(game['board'], game['turn']):
                game['over'] = True
                winner = "❌" if game['turn'] == 'X' else "⭕"
                bot.edit_message_text(f"{get_text(cid)}\n\n🎉 Победил {winner}!", cid, mid, parse_mode="Markdown", reply_markup=get_keyboard(cid))
                bot.answer_callback_query(call.id)
                return
            if check_draw(game['board']):
                game['over'] = True
                bot.edit_message_text(f"{get_text(cid)}\n\n🤝 Ничья!", cid, mid, parse_mode="Markdown", reply_markup=get_keyboard(cid))
                bot.answer_callback_query(call.id)
                return

            game['turn'] = 'O' if game['turn'] == 'X' else 'X'
            bot.edit_message_text(get_text(cid), cid, mid, parse_mode="Markdown", reply_markup=get_keyboard(cid))
            bot.answer_callback_query(call.id)
            return

@bot.message_handler(func=lambda m: m.from_user.id in user_states)
def handle_input(message):
    uid = message.from_user.id
    text = message.text.strip()

    if user_states[uid] == "wait_note":
        if text:
            db.add_note(uid, text)
            bot.send_message(message.chat.id, "✅Заметка сохранена!", reply_markup=main_menu())
        else:
            bot.send_message(message.chat.id, "❌Пустая заметка")
        del user_states[uid]
        return

    if user_states[uid] == "set_city":
        user_city[uid] = text
        bot.send_message(message.chat.id, f"✅ Город {text} сохранён!", reply_markup=main_menu())
        del user_states[uid]
        return

    if user_states[uid] == "wait_city":
        get_weather(message, text)
        del user_states[uid]
        return

    if user_states[uid] in ["simple", "strong"]:
        length, err = validate_length(text)
        if err:
            bot.send_message(message.chat.id, f"❌ {err}")
            return
        pwd = generate_password(length) if user_states[uid] == "simple" else generate_strong_password(length)
        strength = check_password_strength(pwd)
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("💾Сохранить", callback_data=f"save_{pwd}_{length}"))
        markup.add(InlineKeyboardButton("🔄Ещё", callback_data=user_states[uid]))
        bot.send_message(message.chat.id, f"🔐 `{pwd}`\n\n📏 {length} | {strength}", parse_mode="Markdown", reply_markup=markup)
        del user_states[uid]

@bot.callback_query_handler(func=lambda call: call.data.startswith("save_"))
def save_pass(call):
    data = call.data[5:]
    last = data.rfind("_")
    pwd = data[:last]
    length = int(data[last+1:])
    pass_db.add_password(call.from_user.id, pwd, length)
    bot.answer_callback_query(call.id, "✅ Сохранено!", show_alert=True)
    bot.edit_message_text("🔙 Возврат", call.message.chat.id, call.message.message_id, reply_markup=main_menu())

if __name__ == "__main__":
    print("Бот запущен")
    bot.infinity_polling()