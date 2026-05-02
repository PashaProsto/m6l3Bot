from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def notes_menu():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("📝 Создать заметку", callback_data="create_note"),
        InlineKeyboardButton("🗑 Удалить заметку", callback_data="delete_note"),
        InlineKeyboardButton("📋 Просмотреть заметки", callback_data="view_notes"),
        InlineKeyboardButton("🔙 Назад в главное меню", callback_data="back_to_main")
    )
    return markup

def format_notes_list(notes):
    if not notes:
        return "📭 У вас нет заметок.\n\nНажмите 'Создать заметку' чтобы добавить первую заметку."
    
    result = "📋 *Ваши заметки:*\n\n"
    for note_id, note_text, created_at in notes:
        preview = note_text[:50] + ("..." if len(note_text) > 50 else "")
        result += f"📌 *ID:{note_id}* | {created_at[:16]}\n"
        result += f"`{preview}`\n\n"
    result += "\n⚠️ Для удаления заметки используйте ID заметки"
    return result

def delete_notes_markup(notes):
    if not notes:
        return None
    
    markup = InlineKeyboardMarkup()
    for note_id, note_text, _ in notes[:10]:
        preview = (note_text[:25] + "...") if len(note_text) > 25 else note_text
        preview = preview.replace("\n", " ")
        markup.add(InlineKeyboardButton(f"🗑 {note_id} | {preview}", callback_data=f"del_note_{note_id}"))
    
    if len(notes) > 10:
        markup.add(InlineKeyboardButton("📋 Показать все ID", callback_data="list_all_note_ids"))
    
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="back_to_notes"))
    return markup

def all_note_ids_markup(notes):
    markup = InlineKeyboardMarkup(row_width=3)
    buttons = []
    count = 0
    for note_id, note_text, _ in notes:
        if count < 30:
            buttons.append(InlineKeyboardButton(str(note_id), callback_data=f"del_note_{note_id}"))
            count += 1
    markup.add(*buttons)
    markup.add(InlineKeyboardButton("🔙 Назад к удалению", callback_data="delete_note"))
    return markup