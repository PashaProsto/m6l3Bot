import random
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

games_vs_bot = {}
games_two_player = {}

def init_vs_bot(chat_id):
    games_vs_bot[chat_id] = {
        'gameGround': [" "] * 9,
        'playerSymbol': "X",
        'botSymbol': "0",
        'winbool': False,
        'losebool': False,
        'turn': 'player',
        'moves': 0
    }

def init_two_player(chat_id):
    games_two_player[chat_id] = {
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

def bot_move(game):
    g = game['gameGround']
    empty = [i for i in range(9) if g[i] == " "]
    if not empty:
        return False
    cell = random.choice(empty)
    g[cell] = game['botSymbol']
    game['moves'] += 1
    return True

def create_vs_bot_keyboard(chat_id):
    game = games_vs_bot.get(chat_id)
    if not game:
        return None
    
    markup = InlineKeyboardMarkup(row_width=3)
    buttons = []
    
    for i in range(9):
        cell = game['gameGround'][i]
        if cell == " ":
            text = "⬜"
        elif cell == "X":
            text = "❌"
        else:
            text = "⭕"
        buttons.append(InlineKeyboardButton(text, callback_data=f"vsbot_{i}"))
    
    markup.row(buttons[0], buttons[1], buttons[2])
    markup.row(buttons[3], buttons[4], buttons[5])
    markup.row(buttons[6], buttons[7], buttons[8])
    markup.row(InlineKeyboardButton("🔙 Выйти", callback_data="back_to_main"))
    
    return markup

def create_two_player_keyboard(chat_id):
    game = games_two_player.get(chat_id)
    if not game:
        return None
    
    markup = InlineKeyboardMarkup(row_width=3)
    buttons = []
    
    for i in range(9):
        cell = game['gameGround'][i]
        if cell == " ":
            text = "⬜"
        elif cell == "X":
            text = "❌"
        else:
            text = "⭕"
        buttons.append(InlineKeyboardButton(text, callback_data=f"2p_{i}"))
    
    markup.row(buttons[0], buttons[1], buttons[2])
    markup.row(buttons[3], buttons[4], buttons[5])
    markup.row(buttons[6], buttons[7], buttons[8])
    markup.row(InlineKeyboardButton("🔙 Выйти", callback_data="back_to_main"))
    return markup

def get_vs_bot_status_text(chat_id):
    game = games_vs_bot[chat_id]
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
    
    return f"""🤖 Крестики-нолики (ПРОТИВ БОТА)

{field_text}

🎮 {turn}"""

def get_two_player_status_text(chat_id):
    game = games_two_player[chat_id]
    g = game['gameGround']
    
    field = []
    for i in range(0, 9, 3):
        row = ["⬜" if c == " " else "❌" if c == "X" else "⭕" for c in g[i:i+3]]
        field.append(" │ ".join(row))
    field_text = "\n───┼───┼───\n".join(field)
    
    player = "❌ Крестики (X)" if game['current_player'] == 'X' else "⭕ Нолики (O)"
    return f"""👥 Крестики-нолики (2 ИГРОКА)

{field_text}

🎯 Ход: {player}"""

def process_vs_bot_move(bot, call, chat_id, cell_index):
    game = games_vs_bot.get(chat_id)
    if not game or game['turn'] != 'player':
        bot.answer_callback_query(call.id, "❌ Не твой ход", show_alert=True)
        return False

    if game['gameGround'][cell_index] != " ":
        bot.answer_callback_query(call.id, "❌ Клетка занята", show_alert=True)
        return False

    game['gameGround'][cell_index] = "X"
    game['moves'] += 1

    if check_win(game, "X"):
        game['winbool'] = True
        bot.answer_callback_query(call.id, "🎉 Ты выиграл!", show_alert=True)
        return True

    if check_draw(game):
        bot.answer_callback_query(call.id, "🤝 Ничья!", show_alert=True)
        return True

    game['turn'] = 'bot'
    bot.answer_callback_query(call.id, "✅ Ход сделан")
    return False

def process_vs_bot_bot_move(bot, chat_id, message_id):
    game = games_vs_bot.get(chat_id)
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

def process_two_player_move(bot, call, chat_id, cell_index):
    game = games_two_player.get(chat_id)
    if not game:
        bot.answer_callback_query(call.id, "❌ Игра не найдена", show_alert=True)
        return False

    if game['gameGround'][cell_index] != " ":
        bot.answer_callback_query(call.id, "❌ Клетка занята", show_alert=True)
        return False

    game['gameGround'][cell_index] = game['current_player']
    game['moves'] += 1

    if check_win(game, game['current_player']):
        game['winner'] = game['current_player']
        winner_text = "❌ Крестики победили!" if game['current_player'] == 'X' else "⭕ Нолики победили!"
        bot.answer_callback_query(call.id, f"🎉 {winner_text}", show_alert=True)
        return True

    if check_draw(game):
        bot.answer_callback_query(call.id, "🤝 Ничья!", show_alert=True)
        return True

    game['current_player'] = 'O' if game['current_player'] == 'X' else 'X'
    bot.answer_callback_query(call.id, "✅ Ход сделан")
    return False

def end_vs_bot_game(bot, chat_id, message_id):
    game = games_vs_bot.get(chat_id)
    if not game:
        return

    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🔄 Ещё раз", callback_data="vsbot_again"),
        InlineKeyboardButton("🔙 В меню", callback_data="back_to_main")
    )

    g = game['gameGround']
    field = []
    for i in range(0, 9, 3):
        row = ["⬜" if c == " " else "❌" if c == "X" else "⭕" for c in g[i:i+3]]
        field.append(" │ ".join(row))
    field_text = "\n───┼───┼───\n".join(field)

    if game['winbool']:
        text = "🎉 ТЫ ПОБЕДИЛ! 🎉"
    elif game['losebool']:
        text = "😭 БОТ ПОБЕДИЛ 😭"
    else:
        text = "🤝 НИЧЬЯ 🤝"

    try:
        bot.edit_message_text(f"{text}\n\n{field_text}", chat_id, message_id, reply_markup=markup)
    except:
        bot.send_message(chat_id, f"{text}\n\n{field_text}", reply_markup=markup)

    games_vs_bot.pop(chat_id, None)

def end_two_player_game(bot, chat_id, message_id):
    game = games_two_player.get(chat_id)
    if not game:
        return

    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🔄 Ещё раз", callback_data="2p_again"),
        InlineKeyboardButton("🔙 В меню", callback_data="back_to_main")
    )

    g = game['gameGround']
    field = []
    for i in range(0, 9, 3):
        row = ["⬜" if c == " " else "❌" if c == "X" else "⭕" for c in g[i:i+3]]
        field.append(" │ ".join(row))
    field_text = "\n───┼───┼───\n".join(field)

    if game['winner']:
        text = "🎉 ПОБЕДИЛ " + ("❌ КРЕСТИКИ" if game['winner'] == 'X' else "⭕ НОЛИКИ") + "! 🎉"
    else:
        text = "🤝 НИЧЬЯ 🤝"

    try:
        bot.edit_message_text(f"{text}\n\n{field_text}", chat_id, message_id, reply_markup=markup)
    except:
        bot.send_message(chat_id, f"{text}\n\n{field_text}", reply_markup=markup)

    games_two_player.pop(chat_id, None)