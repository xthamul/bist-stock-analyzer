import json
import bcrypt
import os

USERS_FILE = "users.json"

def _load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def _save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def register_user(username, password):
    users = _load_users()
    if username in users:
        return False, "Bu kullanıcı adı zaten mevcut."
    
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    users[username] = {"password": hashed_password}
    _save_users(users)
    return True, "Kayıt başarılı."

def login_user(username, password):
    users = _load_users()
    if username not in users:
        return False, "Kullanıcı adı bulunamadı."
    
    hashed_password = users[username]["password"].encode('utf-8')
    if bcrypt.checkpw(password.encode('utf-8'), hashed_password):
        return True, "Giriş başarılı."
    else:
        return False, "Yanlış şifre."
