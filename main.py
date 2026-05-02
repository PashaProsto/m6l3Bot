import telebot
from telebot import types
import config
import requests

import tictac_pve
import tictac_pvp

bot = telebot.TeleBot(config.TOKEN)

user_state = {}
user_city = {}


@bot.message_handler(commands=['start'])
def welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🎮 Крестики-нолики"),
        types.KeyboardButton("🌤 Моя погода"),
        types.KeyboardButton("🌤 Погода"),
        types.KeyboardButton("ℹ️ Помощь")
    )
    
    bot.send_message(
        message.chat.id,
        f"Привет, {message.from_user.first_name}!\n\nВыбирай функцию:",
        reply_markup=markup
    )
    user_state[message.chat.id] = "menu"


# ==================== ПОГОДА ====================

@bot.message_handler(commands=['setcity'])
def set_city_command(message):
    bot.send_message(message.chat.id, "Напиши город, который хочешь сохранить как основной:")
    user_state[message.chat.id] = "setting_city"


@bot.message_handler(func=lambda m: m.text == "🌤 Моя погода")
def my_weather(message):
    chat_id = message.chat.id
    if chat_id in user_city and user_city[chat_id]:
        get_weather_by_city(message, user_city[chat_id])
    else:
        bot.send_message(chat_id, "У тебя ещё не установлен город.\nИспользуй /setcity или нажми «🌤 Погода»")


@bot.message_handler(func=lambda m: m.text == "🌤 Погода")
def weather_start(message):
    bot.send_message(message.chat.id, "Напиши название города:")
    user_state[message.chat.id] = "waiting_city"


def get_weather_by_city(message, city):
    """Получение погоды"""
    if not hasattr(config, 'WEATHER_API_KEY') or not config.WEATHER_API_KEY.strip():
        bot.send_message(message.chat.id, "❌ API ключ для погоды не настроен в config.py")
        return

    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={config.WEATHER_API_KEY}&units=metric&lang=ru"
    
    try:
        response = requests.get(url, timeout=8)
        data = response.json()

        if data.get("cod") != 200:
            error_msg = data.get("message", "Город не найден")
            bot.send_message(message.chat.id, f"❌ {error_msg.capitalize()}\nПопробуй написать город на английском или по-другому.")
            return

        temp = round(data["main"]["temp"])
        feels = round(data["main"]["feels_like"])
        desc = data["weather"][0]["description"].capitalize()
        humidity = data["main"]["humidity"]
        wind = data["wind"].get("speed", 0)

        text = f"""🌤 Погода в {city.capitalize()}

🌡 {temp}°C (ощущается как {feels}°C)
☁️ {desc}
💧 Влажность: {humidity}%
🌬 Ветер: {wind} м/с"""

        bot.send_message(message.chat.id, text)

    except requests.exceptions.Timeout:
        bot.send_message(message.chat.id, "⏳ Таймаут. Попробуй позже.")
    except Exception as e:
        print(f"Weather error: {e}")  # для отладки в консоли
        bot.send_message(message.chat.id, "Не удалось получить данные о погоде.\n\nПроверь API ключ и интернет.")


# Обработка сообщений
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    chat_id = message.chat.id
    text = message.text.strip()

    state = user_state.get(chat_id)

    if state == "waiting_city":
        get_weather_by_city(message, text)
        user_state[chat_id] = "menu"

    elif state == "setting_city":
        user_city[chat_id] = text
        bot.send_message(chat_id, f"✅ Город сохранён: {text.capitalize()}")
        user_state[chat_id] = "menu"

    elif text == "🎮 Крестики-нолики":
        games_menu(message)
    elif text == "ℹ️ Помощь":
        help_command(message)


# ==================== ИГРЫ ====================

@bot.message_handler(func=lambda message: message.text == "🎮 Крестики-нолики")
def games_menu(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("2 игрока", callback_data="game_2players"),
        types.InlineKeyboardButton("Против бота", callback_data="game_vsbot"),
        types.InlineKeyboardButton("Назад", callback_data="back_to_menu")
    )
    bot.send_message(message.chat.id, "Выбери режим:", reply_markup=markup, parse_mode='Markdown')


@bot.message_handler(func=lambda message: message.text == "ℹ️ Помощь")
def help_command(message):
    bot.send_message(message.chat.id, """
Команды:

🎮 Крестики-нолики — сыграть
🌤 Погода — любой город
🌤 Моя погода — сохранённый город
/setcity — установить свой город

/start — главное меню
    """)


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    if call.data == "back_to_menu":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(
            types.KeyboardButton("🎮 Крестики-нолики"),
            types.KeyboardButton("🌤 Моя погода"),
            types.KeyboardButton("🌤 Погода"),
            types.KeyboardButton("ℹ️ Помощь")
        )
        bot.edit_message_text("Главное меню", chat_id, message_id)
        bot.send_message(chat_id, "Выбирай:", reply_markup=markup)
        user_state[chat_id] = "menu"
        bot.answer_callback_query(call.id)
        return

    # Игра против бота
    if call.data == "game_vsbot":
        tictac_pve.init_game(chat_id)
        markup = tictac_pve.create_keyboard(chat_id)
        text = tictac_pve.get_game_status_text(chat_id)
        bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode='Markdown')
        user_state[chat_id] = "vsbot"
        bot.answer_callback_query(call.id)
        return

    # Игра на двоих
    if call.data == "game_2players":
        tictac_pvp.init_game(chat_id)
        markup = tictac_pvp.create_keyboard(chat_id)
        text = tictac_pvp.get_game_status_text(chat_id)
        bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode='Markdown')
        user_state[chat_id] = "2players"
        bot.answer_callback_query(call.id)
        return

    # Ходы в игре с ботом
    if call.data.startswith("vsbot_") and user_state.get(chat_id) == "vsbot":
        if call.data == "vsbot_again":
            tictac_pve.init_game(chat_id)
            markup = tictac_pve.create_keyboard(chat_id)
            text = tictac_pve.get_game_status_text(chat_id)
            bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode='Markdown')
            bot.answer_callback_query(call.id)
            return

        cell = int(call.data.split("_")[1])
        ended = tictac_pve.process_move(bot, call, chat_id, cell)
        
        if ended:
            tictac_pve.end_game(bot, chat_id, message_id)
        else:
            markup = tictac_pve.create_keyboard(chat_id)
            text = tictac_pve.get_game_status_text(chat_id)
            bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode='Markdown')

            game = tictac_pve.games.get(chat_id)
            if game and game['turn'] == 'bot':
                ended = tictac_pve.process_bot_move(bot, chat_id, message_id)
                if ended:
                    tictac_pve.end_game(bot, chat_id, message_id)
                else:
                    markup = tictac_pve.create_keyboard(chat_id)
                    text = tictac_pve.get_game_status_text(chat_id)
                    bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode='Markdown')
        
        bot.answer_callback_query(call.id)
        return

    # Ходы в игре на двоих
    if call.data.startswith("2p_") and user_state.get(chat_id) == "2players":
        if call.data == "2p_again":
            tictac_pvp.init_game(chat_id)
            markup = tictac_pvp.create_keyboard(chat_id)
            text = tictac_pvp.get_game_status_text(chat_id)
            bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode='Markdown')
            bot.answer_callback_query(call.id)
            return

        cell = int(call.data.split("_")[1])
        ended = tictac_pvp.process_move(bot, call, chat_id, cell)
        
        if ended:
            tictac_pvp.end_game(bot, chat_id, message_id)
        else:
            markup = tictac_pvp.create_keyboard(chat_id)
            text = tictac_pvp.get_game_status_text(chat_id)
            bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode='Markdown')
        
        bot.answer_callback_query(call.id)
        return


if __name__ == "__main__":
    print("Бот запущен!")
    bot.infinity_polling()