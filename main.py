import telebot
from config import token
from logic import Pokemon, Trainer, Battle

# Создаём бот с поддержкой Markdown
bot = telebot.TeleBot(token, parse_mode='Markdown')

def get_username_from_user(user):
    """Возвращаем уникальное имя тренера (username если есть, иначе first_name_id)."""
    if user.username:
        return user.username.lower()
    # безопасный fallback
    return f"{user.first_name}_{user.id}"

def ensure_trainer(username):
    """Создаёт Trainer, если ещё нет, и возвращает его."""
    if username in Trainer.trainers:
        return Trainer.trainers[username]
    return Trainer(username)

@bot.message_handler(commands=['start', 'help'])
def cmd_start(message):
    text = (
        "Привет! Я покемон-бот. Доступные команды:\n\n"
        "/create — создать профиль тренера (если ещё нет)\n"
        "/catch — поймать нового покемона (до 6)\n"
        "/my — показать список твоих покемонов\n"
        "/battle — начать бой с другим тренером.\n"
        "  • Используй `/battle` в ответ на сообщение другого пользователя — чтобы вызвать его\n"
        "  • Или `/battle username` (без @) — чтобы вызвать по имени.\n\n"
        "Примеры:\n"
        "  /catch\n"
        "  (ответ на сообщении игрока) /battle\n\n"
        "Если что-то пойдёт не так — бот напишет подсказку."
    )
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['create'])
def cmd_create(message):
    uname = get_username_from_user(message.from_user)
    if uname in Trainer.trainers:
        bot.reply_to(message, "У тебя уже есть профиль тренера.")
        return
    Trainer(uname)
    bot.reply_to(message, "✅ Профиль тренера создан! Можешь ловить покемонов командой /catch")

@bot.message_handler(commands=['catch', 'add'])
def cmd_catch(message):
    uname = get_username_from_user(message.from_user)
    trainer = ensure_trainer(uname)

    # Trainer.add_pokemon создаёт Pokemon и кладёт в trainer.pokemons
    result_text = trainer.add_pokemon()
    # последний добавленный покемон
    new_pokemon = trainer.pokemons[-1]

    # отправляем текст и картинку (если есть)
    try:
        bot.send_message(message.chat.id, f"🎉 {result_text}")
        if new_pokemon.show_img():
            bot.send_photo(message.chat.id, new_pokemon.show_img(), caption=new_pokemon.info())
        else:
            bot.send_message(message.chat.id, new_pokemon.info())
    except Exception:
        # на случай проблем с отправкой фото
        bot.reply_to(message, result_text + "\n(не удалось отправить изображение)")

@bot.message_handler(commands=['my', 'trainer'])
def cmd_my(message):
    uname = get_username_from_user(message.from_user)
    if uname not in Trainer.trainers:
        bot.reply_to(message, "У тебя ещё нет профиля. Создай его командой /create или просто используй /catch — он создаст профиль автоматически.")
        return
    trainer = Trainer.trainers[uname]
    bot.send_message(message.chat.id, trainer.info())

@bot.message_handler(commands=['battle'])
def cmd_battle(message):
    # Определяем оппонента: 1) если команда — в ответ на сообщение, 2) если передан аргумент /battle username
    challenger_uname = get_username_from_user(message.from_user)

    # получить оппонента
    opponent_uname = None
    if message.reply_to_message:
        opponent_uname = get_username_from_user(message.reply_to_message.from_user)
    else:
        parts = message.text.split(maxsplit=1)
        if len(parts) == 2:
            # убираем возможный @
            opponent_uname = parts[1].lstrip('@').strip().lower()

    if opponent_uname is None:
        bot.reply_to(message, "Укажи оппонента: используй /battle в ответ на сообщение игрока или `/battle username`.")
        return

    # проверяем профили (создаём профиль автоматически, если нужно)
    challenger = ensure_trainer(challenger_uname)
    opponent = Trainer.trainers.get(opponent_uname)
    if opponent is None:
        bot.reply_to(message, "У оппонента ещё нет профиля (он не использовал бота).")
        return

    # проверка наличия покемонов
    if not challenger.pokemons:
        bot.reply_to(message, "У тебя нет покемонов — поймай хотя бы одного (/catch).")
        return
    if not opponent.pokemons:
        bot.reply_to(message, "У оппонента нет покемонов для боя.")
        return

    # создаём и стартуем бой
    battle = Battle(challenger, opponent)
    result = battle.start()

    # Отправляем превью покемонов (по одному фото каждого) + результат
    try:
        p1 = challenger.pokemons[0]
        p2 = opponent.pokemons[0]
        if p1.show_img():
            bot.send_photo(message.chat.id, p1.show_img(), caption=f"{p1.name} — {challenger.name}")
        if p2.show_img():
            bot.send_photo(message.chat.id, p2.show_img(), caption=f"{p2.name} — {opponent.name}")
    except Exception:
        # игнорируем ошибки с картинками
        pass

    bot.send_message(message.chat.id, result)


@bot.message_handler(commands=['stats'])
def cmd_stats(message):
    uname = get_username_from_user(message.from_user)

    if uname not in Trainer.trainers:
        bot.reply_to(message, "У тебя нет профиля. Используй /create или /catch.")
        return

    trainer = Trainer.trainers[uname]

    if not trainer.pokemons:
        bot.reply_to(message, "У тебя нет покемонов.")
        return

    # сортировки: /stats hp /stats attack /stats speed
    args = message.text.split()
    sort_mode = None
    if len(args) > 1:
        sort_mode = args[1].lower()

    if sort_mode == "hp":
        trainer.pokemons.sort(key=lambda p: p.hp, reverse=True)
    elif sort_mode == "attack":
        trainer.pokemons.sort(key=lambda p: p.attack, reverse=True)
    elif sort_mode == "speed":
        trainer.pokemons.sort(key=lambda p: p.speed, reverse=True)

    for p in trainer.pokemons:

        # XP прогресс-бар
        filled = int((p.xp / p.xp_to_next) * 10)
        bar = "█" * filled + "░" * (10 - filled)

        text = (
            f"*{p.name}* {p.type_emoji()}\n"
            f"Уровень: *{p.level}*\n"
            f"XP: `{p.xp} / {p.xp_to_next}`\n"
            f"{bar}\n\n"
            f"*Статы:*\n"
            f"HP: `{p.hp}`\n"
            f"Атака: `{p.attack}`\n"
            f"Защита: `{p.defense}`\n"
            f"Скорость: `{p.speed}`\n"
        )

        try:
            if p.show_img():
                bot.send_photo(message.chat.id, p.show_img(), caption=text, parse_mode="Markdown")
            else:
                bot.send_message(message.chat.id, text, parse_mode="Markdown")
        except:
            bot.send_message(message.chat.id, text, parse_mode="Markdown")


@bot.message_handler(commands=['rename'])
def cmd_rename(message):
    uname = get_username_from_user(message.from_user)

    if uname not in Trainer.trainers:
        bot.reply_to(message, "У тебя нет профиля. Используй /create или /catch.")
        return

    trainer = Trainer.trainers[uname]

    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.reply_to(message, "Использование: `/rename староеИмя новоеИмя`", parse_mode="Markdown")
        return

    old, new = parts[1], parts[2]

    # Поиск покемона
    for p in trainer.pokemons:
        if p.name.lower() == old.lower():
            p.name = new
            bot.reply_to(message, f"✏️ Переименовал `{old}` → *{new}*!", parse_mode="Markdown")
            return

    bot.reply_to(message, f"Покемон `{old}` не найден.", parse_mode="Markdown")


@bot.message_handler(commands=['top'])
def cmd_top(message):
    if not Trainer.trainers:
        bot.reply_to(message, "Пока нет ни одного тренера.")
        return

    ranking = []

    for username, t in Trainer.trainers.items():
        total_lvl = sum(p.level for p in t.pokemons)
        total_power = sum((p.hp + p.attack + p.defense + p.speed) for p in t.pokemons)
        ranking.append((t.name, total_lvl, total_power))

    ranking.sort(key=lambda x: (x[1], x[2]), reverse=True)

    text = "🏆 *Глобальный рейтинг тренеров:*\n\n"
    for i, (name, lvl, pw) in enumerate(ranking, start=1):
        text += f"*{i}. {name}* — уровни: `{lvl}`, сила: `{pw}`\n"

    bot.send_message(message.chat.id, text, parse_mode="Markdown")




@bot.message_handler(func=lambda m: True)
def fallback(message):
    # Небольшая подсказка на любые другие сообщения
    if message.text and message.text.startswith('/'):
        # неизвестная команда
        bot.reply_to(message, "Неизвестная команда. Напиши /help чтобы посмотреть доступные команды.")
    # иначе — игнорируем

if __name__ == "__main__":
    print("Bot started...")
    bot.infinity_polling(none_stop=True)