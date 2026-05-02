from telebot import types

games = {}

def init_game(chat_id):
    games[chat_id] = {
        'gameGround': [" "] * 9,
        'current_player': 'X',
        'winner': None,
        'moves': 0
    }


def check_win(game, symbol):
    g = game['gameGround']
    wins = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
    for a,b,c in wins:
        if g[a] == symbol and g[b] == symbol and g[c] == symbol:
            return True
    return False


def check_draw(game):
    return " " not in game['gameGround']


def create_keyboard(chat_id):
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
        buttons.append(types.InlineKeyboardButton(text, callback_data=f"2p_{i}"))
    
    markup.row(buttons[0], buttons[1], buttons[2])
    markup.row(buttons[3], buttons[4], buttons[5])
    markup.row(buttons[6], buttons[7], buttons[8])
    markup.row(types.InlineKeyboardButton("Выйти", callback_data="back_to_menu"))
    return markup


def get_game_status_text(chat_id):
    game = games[chat_id]
    g = game['gameGround']
    
    field = []
    for i in range(0, 9, 3):
        row = ["⬜" if c == " " else "❌" if c == "X" else "⭕" for c in g[i:i+3]]
        field.append(" │ ".join(row))
    field_text = "\n───┼───┼───\n".join(field)
    
    player = "Крестики (X)" if game['current_player'] == 'X' else "Нолики (O)"
    return f"""Крестики-нолики (2 игрока)

{field_text}

Ход: {player}"""


def process_move(bot, call, chat_id, cell_index):
    game = games.get(chat_id)
    if not game:
        bot.answer_callback_query(call.id, "Игра не найдена", show_alert=True)
        return False

    if game['gameGround'][cell_index] != " ":
        bot.answer_callback_query(call.id, "Занято", show_alert=True)
        return False

    game['gameGround'][cell_index] = game['current_player']
    game['moves'] += 1

    if check_win(game, game['current_player']):
        game['winner'] = game['current_player']
        bot.answer_callback_query(call.id, "Победа!")
        return True

    if check_draw(game):
        bot.answer_callback_query(call.id, "Ничья!")
        return True

    game['current_player'] = 'O' if game['current_player'] == 'X' else 'X'
    bot.answer_callback_query(call.id, "Ход сделан")
    return False


def end_game(bot, chat_id, message_id):
    game = games.get(chat_id)
    if not game:
        return

    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("Ещё раз", callback_data="2p_again"),
        types.InlineKeyboardButton("В меню", callback_data="back_to_menu")
    )

    g = game['gameGround']
    field = []
    for i in range(0, 9, 3):
        row = ["⬜" if c == " " else "❌" if c == "X" else "⭕" for c in g[i:i+3]]
        field.append(" │ ".join(row))
    field_text = "\n───┼───┼───\n".join(field)

    if game['winner']:
        text = "Победил " + ("X" if game['winner'] == 'X' else "O")
    else:
        text = "Ничья"

    try:
        bot.edit_message_text(f"{text}\n\n{field_text}", chat_id, message_id, reply_markup=markup, parse_mode='Markdown')
    except:
        bot.send_message(chat_id, f"{text}\n\n{field_text}", reply_markup=markup, parse_mode='Markdown')

    games.pop(chat_id, None)