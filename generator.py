import random
import string

def generate_password(length):
    characters = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?"
    password = ''.join(random.choice(characters) for _ in range(length))
    return password

def generate_strong_password(length):
    password = []
    if length >= 1:
        password.append(random.choice(string.ascii_uppercase))
    if length >= 2:
        password.append(random.choice(string.ascii_lowercase))
    if length >= 3:
        password.append(random.choice(string.digits))
    if length >= 4:
        password.append(random.choice("!@#$%^&*()_+-=[]{}|;:,.<>?"))
    
    remaining = length - len(password)
    if remaining > 0:
        all_chars = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?"
        password.extend(random.choice(all_chars) for _ in range(remaining))
    
    random.shuffle(password)
    return ''.join(password)

def check_password_strength(password):
    score = 0
    length = len(password)
    
    if length >= 16:
        score += 2
    elif length >= 12:
        score += 1
    
    if any(c.isupper() for c in password):
        score += 1
    if any(c.islower() for c in password):
        score += 1
    if any(c.isdigit() for c in password):
        score += 1
    if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        score += 2
    
    if password.isalnum():
        score -= 1
    
    if length >= 20 and score >= 7:
        return "🔐 Очень сильный"
    elif score >= 6:
        return "🔒 Сильный"
    elif score >= 4:
        return "⚠️ Средний"
    else:
        return "❌ Слабый"

def validate_length(length_str):
    try:
        length = int(length_str)
        if 4 <= length <= 64:
            return length, None
        return None, "Длина должна быть от 4 до 64 символов"
    except ValueError:
        return None, "Введите число"