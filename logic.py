# ========================= logic.py =========================
# Полный модуль логики покемон-бота

import random

TYPE_EMOJI = {
    "fire": "🔥",
    "electric": "⚡",
    "ice": "❄️",
    "grass": "🌿",
    "dragon": "🐉",
    "water": "💧",
    "rock": "🪨",
    "psychic": "🔮",
    "normal": "⭐",
    "ghost": "👻",
}


class Pokemon:
    def __init__(self, name, type, hp, attack, defense, speed, image_path):
        self.name = name
        self.type = type
        self.hp = hp
        self.attack = attack
        self.defense = defense
        self.speed = speed
        self.image_path = image_path

        # Уровни
        self.level = 1
        self.xp = 0
        self.xp_to_next = 20

        # IV — генетические параметры
        self.iv_hp = random.randint(0, 31)
        self.iv_attack = random.randint(0, 31)
        self.iv_defense = random.randint(0, 31)
        self.iv_speed = random.randint(0, 31)

        # EV — опыт характеристик
        self.ev_hp = 0
        self.ev_attack = 0
        self.ev_defense = 0
        self.ev_speed = 0

    def show_img(self):
        return self.image_path

    def type_emoji(self):
        return TYPE_EMOJI.get(self.type.lower(), "❔")

    def add_xp(self, amount):
        self.xp += amount
        while self.xp >= self.xp_to_next:
            self.level += 1
            self.xp -= self.xp_to_next
            self.xp_to_next = int(self.xp_to_next * 1.5)

            # рост характеристик
            self.hp += 2
            self.attack += 1
            self.defense += 1
            self.speed += 1

    def apply_ev_gain(self):
        self.ev_hp += random.randint(1, 3)
        self.ev_attack += random.randint(1, 3)
        self.ev_defense += random.randint(1, 3)
        self.ev_speed += random.randint(1, 3)


class Trainer:
    trainers = {}

    def __init__(self, name):
        self.name = name
        self.pokemons = []
        self.items = {
            "potion": 2,
            "super_potion": 0,
            "trap": 0,
            "boost": 0
        }
        Trainer.trainers[name] = self

    def info(self):
        text = f"Тренер: {self.name}\nПокемоны: {len(self.pokemons)}\n"
        return text

    def add_pokemon(self):
        # генерация тестового покемона
        name = random.choice(["Pikachu", "Charmander", "Squirtle", "Bulbasaur", "Dratini"])
        type = random.choice(["electric", "fire", "water", "grass", "dragon"])
        hp = random.randint(40, 80)
        attack = random.randint(10, 25)
        defense = random.randint(5, 20)
        speed = random.randint(10, 30)
        image_path = "images/" + name.lower() + ".png"

        # шанс на редкого покемона
        if random.random() < 0.01:
            name = "🌟 Shiny " + name
            hp += 20
            attack += 10
            defense += 10
            image_path = "images/shiny_" + name.lower().replace(" ", "_") + ".png"

        p = Pokemon(name, type, hp, attack, defense, speed, image_path)
        self.pokemons.append(p)
        return f"Ты поймал {p.name}!"


class Battle:
    def __init__(self, t1, t2):
        self.t1 = t1
        self.t2 = t2

    def start(self):
        p1 = self.t1.pokemons[0]
        p2 = self.t2.pokemons[0]

        # простой бой по скорости
        if p1.speed > p2.speed:
            winner = p1
            loser = p2
        else:
            winner = p2
            loser = p1

        winner.add_xp(10)
        winner.apply_ev_gain()

        return f"🏆 Победил {winner.name}!"


# ========================= main.py =========================
# Телеграм-бот со всеми возможностями

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import token
from logic import Trainer, Pokemon, Battle

bot = telebot.TeleBot(token, parse_mode="Markdown")

battle_selection = {}


def get_username(user):
    return user.username.lower() if user.username else f"{user.first_name}_{user.id}"


def ensure_trainer(username):
    return Trainer.trainers.get(username) or Trainer(username)


@bot.message_handler(commands=['start', 'help'])
def start(message):
    bot.reply_to(message, "Команды: /create /catch /stats /top /rename /use /fight /battle")


@bot.message_handler(commands=['create'])
def create(message):
    uname = get_username(message.from_user)
    if uname in Trainer.trainers:
        bot.reply_to(message, "Профиль уже создан.")
        return
    Trainer(uname)
    bot.reply_to(message, "Профиль тренера создан!")


@bot.message_handler(commands=['catch'])
def catch(message):
    uname = get_username(message.from_user)
    t = ensure_trainer(uname)

    text = t.add_pokemon()
    p = t.pokemons[-1]

    if p.show_img():
        bot.send_photo(message.chat.id, p.show_img(), caption=text)
    else:
        bot.reply_to(message, text)


@bot.message_handler(commands=['stats'])
def stats(message):
    uname = get_username(message.from_user)
    if uname not in Trainer.trainers:
        bot.reply_to(message, "Сначала создай тренера.")
        return

    t = Trainer.trainers[uname]

    args = message.text.split()
    if len(args) > 1:
        mode = args[1].lower()
        if mode == "hp": t.pokemons.sort(key=lambda p: p.hp, reverse=True)
        if mode == "attack": t.pokemons.sort(key=lambda p: p.attack, reverse=True)
        if mode == "speed": t.pokemons.sort(key=lambda p: p.speed, reverse=True)

    for p in t.pokemons:
        filled = int((p.xp / p.xp_to_next) * 10)
        bar = "█" * filled + "░" * (10 - filled)

        text = (
            f"*{p.name}* {p.type_emoji()}\n"
            f"Уровень: *{p.level}*\n"
            f"XP: `{p.xp}/{p.xp_to_next}`\n"
            f"{bar}\n\n"
            f"HP: `{p.hp}`  (IV {p.iv_hp}, EV {p.ev_hp})\n"
            f"Атака: `{p.attack}`  (IV {p.iv_attack}, EV {p.ev_attack})\n"
            f"Защита: `{p.defense}`  (IV {p.iv_defense}, EV {p.ev_defense})\n"
            f"Скорость: `{p.speed}`  (IV {p.iv_speed}, EV {p.ev_speed})\n"
        )

        bot.send_photo(message.chat.id, p.show_img(), caption=text)


@bot.message_handler(commands=['rename'])
def rename(message):
    uname = get_username(message.from_user)
    t = Trainer.trainers.get(uname)
    if not t:
        bot.reply_to(message, "Создай тренера.")
        return

    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.reply_to(message, "Использование: /rename старое новое")
        return

    old, new = parts[1], parts[2]
    for p in t.pokemons:
        if p.name.lower() == old.lower():
            p.name = new
            bot.reply_to(message, f"Имя изменено: {old} → {new}")
            return

    bot.reply_to(message, "Покемон не найден.")


@bot.message_handler(commands=['top'])
def top(message):
    ranking = []
    for name, t in Trainer.trainers.items():
        total_lvl = sum(p.level for p in t.pokemons)
        total_pow = sum(p.hp + p.attack + p.defense + p.speed for p in t.pokemons)
        ranking.append((t.name, total_lvl, total_pow))

    ranking.sort(key=lambda x: (x[1], x[2]), reverse=True)

    text = "🏆 Топ тренеров:\n\n"
    for i, (name, lvl, pw) in enumerate(ranking, 1):
        text += f"{i}. *{name}* — уровни `{lvl}`, сила `{pw}`\n"

    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['use'])
def use(message):
    uname = get_username(message.from_user)
    t = Trainer.trainers.get(uname)

    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.reply_to(message, "Формат: /use предмет покемон")
        return

    item, target = parts[1], parts[2].lower()

    if item not in t.items or t.items[item] <= 0:
        bot.reply_to(message, "Нет такого предмета.")
        return

    p = next((x for x in t.pokemons if x.name.lower() == target), None)
    if not p:
        bot.reply_to(message, "Покемон не найден.")
        return

    if item == "potion": p.hp += 20
    if item == "super_potion": p.hp += 50
    if item == "boost": p.attack += 5

    t.items[item] -= 1
    bot.reply_to(message, f"Использовано {item} на {p.name}")


@bot.message_handler(commands=['fight'])
def fight(message):
    uname = get_username(message.from_user)
    t = Trainer.trainers.get(uname)
    if not t or not t.pokemons:
        bot.reply_to(message, "Нет покемонов.")
        return

    kb = InlineKeyboardMarkup()
    for p in t.pokemons:
        kb.add(InlineKeyboardButton(text=p.name, callback_data=f"pick_{p.name}"))

    battle_selection[message.from_user.id] = {"step": 1}
    bot.send_message(message.chat.id, "Выбери своего покемона:", reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith("pick_"))
def pick(call):
    user_id = call.from_user.id
    pname = call.data.split("_", 1)[1]

    if user_id not in battle_selection:
        bot.answer_callback_query(call.id, "Начни /fight")
        return

    uname = get_username(call.from_user)
    t = Trainer.trainers[uname]

    p = next((x for x in t.pokemons if x.name == pname), None)
    if not p:
        bot.answer_callback_query(call.id, "Покемон не найден")
        return

    if battle_selection[user_id]["step"] == 1:
        battle_selection[user_id]["first"] = p
        battle_selection[user_id]["step"] = 2
        bot.edit_message_text("Теперь выбери покемона соперника (он тоже должен нажать /fight).", call.message.chat.id, call.message.message_id)
    else:
        first = battle_selection[user_id]["first"]
        second = p
        del battle_selection[user_id]

        result = f"Бой: {first.name} vs {second.name}\nПобедил: {first.name if first.speed >= second.speed else second.name}"
        bot.send_message(call.message.chat.id, result)


@bot.message_handler(commands=['battle'])
def battle_cmd(message):
    uname = get_username(message.from_user)
    t1 = ensure_trainer(uname)

    if message.reply_to_message:
        opponent = message.reply_to_message.from_user
        uname2 = get_username(opponent)
        t2 = ensure_trainer(uname2)

        b = Battle(t1, t2)
        bot.reply_to(message, b.start())
    else:
        bot.reply_to(message, "Используй /battle в ответ на сообщение оппонента.")


bot.infinity_polling()
