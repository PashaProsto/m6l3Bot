import random
from telebot import types

games = {}

def init_game(chat_id):
    """Новая игра против бота"""
    games[chat_id] = {
        'gameGround': [" "] * 9,
        'playerSymbol': "X",
        'botSymbol': "0",
        'winbool': False,
        'losebool': False,
        'turn': 'player',
        'moves': 0
    }


def check_win(game, symbol):
    """Проверка победы"""
    g = game['gameGround']
    wins = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
    for a,b,c in wins:
        if g[a] == symbol and g[b] == symbol and g[c] == symbol:
            return True
    return False


def check_draw(game):
    """Проверка ничьей"""
    return " " not in game['gameGround']


def bot_move(game):
    """Ход бота"""
    g = game['gameGround']
    empty = [i for i in range(9) if g[i] == " "]
    if not empty:
        return False
    cell = random.choice(empty)
    g[cell] = game['botSymbol']
    game['moves'] += 1
    return True


def create_keyboard(chat_id):
    """Создаёт клавиатуру с полем"""
    game = games.get(chat_id)
    if not game:
        return None
    
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = []
    
    for i in range(9):
        cell = game['gameGround'][i]
        if cell == " ":
            text = "⬜"
        elif cell == "X":
            text = "❌"
        else:
            text = "⭕"
        buttons.append(types.InlineKeyboardButton(text, callback_data=f"vsbot_{i}"))
    
    markup.row(buttons[0], buttons[1], buttons[2])
    markup.row(buttons[3], buttons[4], buttons[5])
    markup.row(buttons[6], buttons[7], buttons[8])
    markup.row(types.InlineKeyboardButton("Выйти", callback_data="back_to_menu"))
    
    return markup


def get_game_status_text(chat_id):
    """Текст для сообщения с полем"""
    game = games[chat_id]
    g = game['gameGround']
    
    field = []
    for i in range(0, 9, 3):
        row = []
        for cell in g[i:i+3]:
            if cell == " ":
                row.append("⬜")
            elif cell == "X":
                row.append("❌")
            else:
                row.append("⭕")
        field.append(" │ ".join(row))
    
    field_text = "\n───┼───┼───\n".join(field)
    
    if game['turn'] == 'player':
        turn = "Твой ход"
    else:
        turn = "Ход бота"
    
    return f"""Крестики-нолики (против бота)

{field_text}

{turn}"""


def process_move(bot, call, chat_id, cell_index):
    """Ход игрока"""
    game = games.get(chat_id)
    if not game or game['turn'] != 'player':
        bot.answer_callback_query(call.id, "Не твой ход", show_alert=True)
        return False

    if game['gameGround'][cell_index] != " ":
        bot.answer_callback_query(call.id, "Клетка занята", show_alert=True)
        return False

    game['gameGround'][cell_index] = "X"
    game['moves'] += 1

    if check_win(game, "X"):
        game['winbool'] = True
        bot.answer_callback_query(call.id, "Ты выиграл!")
        return True

    if check_draw(game):
        bot.answer_callback_query(call.id, "Ничья!")
        return True

    game['turn'] = 'bot'
    bot.answer_callback_query(call.id, "Ход сделан")
    return False


def process_bot_move(bot, chat_id, message_id):
    """Ход бота"""
    game = games.get(chat_id)
    if not game or game['turn'] != 'bot':
        return False

    bot_move(game)

    if check_win(game, "0"):
        game['losebool'] = True
        return True

    if check_draw(game):
        return True

    game['turn'] = 'player'
    return False


def end_game(bot, chat_id, message_id):
    """Завершение игры"""
    game = games.get(chat_id)
    if not game:
        return

    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("Ещё раз", callback_data="vsbot_again"),
        types.InlineKeyboardButton("В меню", callback_data="back_to_menu")
    )

    # Формируем поле для финального сообщения
    g = game['gameGround']
    field = []
    for i in range(0, 9, 3):
        row = ["⬜" if c == " " else "❌" if c == "X" else "⭕" for c in g[i:i+3]]
        field.append(" │ ".join(row))
    field_text = "\n───┼───┼───\n".join(field)

    if game['winbool']:
        text = "Ты победил!"
    elif game['losebool']:
        text = "Бот победил"
    else:
        text = "Ничья"

    try:
        bot.edit_message_text(f"{text}\n\n{field_text}", chat_id, message_id, reply_markup=markup, parse_mode='Markdown')
    except:
        bot.send_message(chat_id, f"{text}\n\n{field_text}", reply_markup=markup, parse_mode='Markdown')

    games.pop(chat_id, None)