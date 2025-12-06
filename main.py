import telebot
from config import token
from logic import Pokemon, Trainer, Battle

# Создаём бот с поддержкой Markdown
bot = telebot.TeleBot(token)

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
        "Основные:\n"
        "/create — создать профиль тренера\n"
        "/catch — поймать нового покемона (до 6)\n"
        "/my — показать профиль тренера\n"
        "/battle — начать бой\n\n"
        "Покемоны:\n"
        "/pokemons — список всех покемонов\n"
        "/stats — детальная статистика\n"
        "/rename — переименовать покемона\n"
        "/release — отпустить покемона\n"
        "/evolve — эволюционировать покемона\n"
        "/heal — вылечить всех покемонов\n\n"
        "Экономика:\n"
        "/daily — ежедневная награда\n"
        "/shop — магазин предметов\n"
        "/buy — купить предмет\n"
        "/items — показать инвентарь\n"
        "/use — использовать предмет\n"
        "/coins — баланс монет\n\n"
        "Топы:\n"
        "/top — рейтинг тренеров\n"
        "/toppokemons — лучшие покемоны\n\n"
        "Разное:\n"
        "/gym — бой с лидером зала\n"
        "/fight — бой с инлайн-кнопками\n\n"
        "Примеры:\n"
        "/catch — поймать покемона\n"
        "/battle @username — вызвать на бой\n"
        "/use potion Pikachu — использовать зелье\n"
        "/daily — получить награду\n\n"
        "Удачи в игре! 🎮"
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
    
    if result_text.startswith("❌"):
        bot.reply_to(message, result_text)
        return
    
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

@bot.message_handler(commands=['my', 'trainer', 'profile'])
def cmd_my(message):
    uname = get_username_from_user(message.from_user)
    if uname not in Trainer.trainers:
        bot.reply_to(message, "❌ У тебя ещё нет профиля. Создай его командой /create или просто используй /catch — он создаст профиль автоматически.")
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
        bot.reply_to(message, "❌ Укажи оппонента: используй /battle в ответ на сообщение игрока или `/battle username`.")
        return

    # проверяем профили (создаём профиль автоматически, если нужно)
    challenger = ensure_trainer(challenger_uname)
    opponent = Trainer.trainers.get(opponent_uname)
    if opponent is None:
        bot.reply_to(message, "❌ У оппонента ещё нет профиля (он не использовал бота).")
        return

    # проверка наличия покемонов
    if not challenger.pokemons:
        bot.reply_to(message, "❌ У тебя нет покемонов — поймай хотя бы одного (/catch).")
        return
    if not opponent.pokemons:
        bot.reply_to(message, "❌ У оппонента нет покемонов для боя.")
        return

    # создаём и стартуем бой
    battle = Battle(challenger, opponent)
    result = battle.start()

    # Отправляем превью покемонов (по одному фото каждого) + результат
    try:
        p1 = challenger.pokemons[0]
        p2 = opponent.pokemons[0]
        if p1.show_img():
            bot.send_photo(message.chat.id, p1.show_img(), caption=f"⚔️ {p1.name} — {challenger.name}")
        if p2.show_img():
            bot.send_photo(message.chat.id, p2.show_img(), caption=f"⚔️ {p2.name} — {opponent.name}")
    except Exception:
        # игнорируем ошибки с картинками
        pass

    bot.send_message(message.chat.id, result)

@bot.message_handler(commands=['stats'])
def cmd_stats(message):
    uname = get_username_from_user(message.from_user)

    if uname not in Trainer.trainers:
        bot.reply_to(message, "❌ У тебя нет профиля. Используй /create или /catch.")
        return

    trainer = Trainer.trainers[uname]

    if not trainer.pokemons:
        bot.reply_to(message, "❌ У тебя нет покемонов.")
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
        bot.reply_to(message, "❌ У тебя нет профиля. Используй /create или /catch.")
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

    bot.reply_to(message, f"❌ Покемон `{old}` не найден.", parse_mode="Markdown")

@bot.message_handler(commands=['top'])
def cmd_top(message):
    if not Trainer.trainers:
        bot.reply_to(message, "❌ Пока нет ни одного тренера.")
        return

    ranking = []
    for username, t in Trainer.trainers.items():
        total_lvl = sum(p.level for p in t.pokemons)
        total_power = sum((p.hp + p.attack + p.defense + p.speed) for p in t.pokemons)
        ranking.append((t.name, total_lvl, total_power, t.coins, t.battles_won))

    ranking.sort(key=lambda x: (x[1], x[2]), reverse=True)

    text = "🏆 *Глобальный рейтинг тренеров:*\n\n"
    for i, (name, lvl, pw, coins, wins) in enumerate(ranking[:15], start=1):
        text += f"*{i}. {name}*\n"
        text += f"   ⭐ Уровни: `{lvl}`\n"
        text += f"   ⚡ Сила: `{pw}`\n"
        text += f"   💰 Монеты: `{coins}`\n"
        text += f"   🏆 Побед: `{wins}`\n\n"

    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=['daily'])
def cmd_daily(message):
    uname = get_username_from_user(message.from_user)
    trainer = ensure_trainer(uname)
    
    success, result = trainer.claim_daily()
    bot.reply_to(message, result)

@bot.message_handler(commands=['shop'])
def cmd_shop(message):
    text = (
        "🛒 *Магазин предметов:*\n\n"
        "1. Зелье здоровья (+20 HP) — 50 монет\n"
        "   `/buy potion`\n\n"
        "2. Супер-зелье (+50 HP) — 120 монет\n"
        "   `/buy super_potion`\n\n"
        "3. Буст атаки (+5 атаки) — 80 монет\n"
        "   `/buy boost`\n\n"
        "4. Редкая конфета (+50 XP) — 200 монет\n"
        "   `/buy rare_candy`\n\n"
        "5. Камень эволюции — 500 монет\n"
        "   `/buy evolution_stone`\n\n"
        "💡 Используй /coins чтобы проверить баланс\n"
        "💡 Используй /items чтобы посмотреть инвентарь"
    )
    bot.reply_to(message, text)

@bot.message_handler(commands=['buy'])
def cmd_buy(message):
    uname = get_username_from_user(message.from_user)
    trainer = Trainer.trainers.get(uname)
    
    if not trainer:
        bot.reply_to(message, "❌ Сначала создай профиль /create")
        return
    
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "Использование: `/buy предмет`\nПример: `/buy potion`")
        return
    
    item = parts[1].lower()
    prices = {
        "potion": 50,
        "super_potion": 120,
        "boost": 80,
        "rare_candy": 200,
        "evolution_stone": 500
    }
    
    if item not in prices:
        bot.reply_to(message, "❌ Такого предмета нет в магазине. Посмотри /shop")
        return
    
    price = prices[item]
    if trainer.coins < price:
        bot.reply_to(message, f"❌ Недостаточно монет. Нужно {price}, у тебя {trainer.coins}")
        return
    
    trainer.coins -= price
    trainer.items[item] = trainer.items.get(item, 0) + 1
    bot.reply_to(message, f"✅ Куплено: {item} за {price} монет. Осталось: {trainer.coins}")

@bot.message_handler(commands=['coins', 'balance'])
def cmd_coins(message):
    uname = get_username_from_user(message.from_user)
    trainer = Trainer.trainers.get(uname)
    
    if not trainer:
        bot.reply_to(message, "❌ Сначала создай профиль /create")
        return
    
    bot.reply_to(message, f"💰 Баланс: *{trainer.coins}* монет")

@bot.message_handler(commands=['use'])
def cmd_use(message):
    uname = get_username_from_user(message.from_user)
    trainer = Trainer.trainers.get(uname)
    
    if not trainer:
        bot.reply_to(message, "❌ Сначала создай профиль /create")
        return
    
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.reply_to(message, "Использование: `/use предмет покемон`\nПример: `/use potion Pikachu`")
        return
    
    item, pokemon_name = parts[1], parts[2]
    success, result = trainer.use_item(item, pokemon_name)
    bot.reply_to(message, result)

@bot.message_handler(commands=['items', 'inventory'])
def cmd_items(message):
    uname = get_username_from_user(message.from_user)
    trainer = Trainer.trainers.get(uname)
    
    if not trainer:
        bot.reply_to(message, "❌ Сначала создай профиль /create")
        return
    
    items_text = trainer.get_items_list()
    bot.reply_to(message, items_text)

@bot.message_handler(commands=['pokemons', 'list'])
def cmd_pokemons(message):
    uname = get_username_from_user(message.from_user)
    trainer = Trainer.trainers.get(uname)
    
    if not trainer:
        bot.reply_to(message, "❌ Сначала создай профиль /create")
        return
    
    if not trainer.pokemons:
        bot.reply_to(message, "❌ У тебя нет покемонов. Используй /catch")
        return
    
    text = f"📋 *Твои покемоны ({len(trainer.pokemons)}/6):*\n\n"
    for i, p in enumerate(trainer.pokemons, 1):
        hp_bar = "█" * int(p.hp / p.max_hp * 10) + "░" * (10 - int(p.hp / p.max_hp * 10))
        text += f"{i}. *{p.name}* {p.type_emoji()} (ур. {p.level})\n"
        text += f"   HP: {hp_bar} {p.hp}/{p.max_hp}\n"
        text += f"   ⚔️{p.attack} 🛡️{p.defense} 🏃{p.speed}\n\n"
    
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['evolve'])
def cmd_evolve(message):
    uname = get_username_from_user(message.from_user)
    trainer = Trainer.trainers.get(uname)
    
    if not trainer:
        bot.reply_to(message, "❌ Сначала создай профиль /create")
        return
    
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        # Показать покемонов, которые могут эволюционировать
        evolvable = [p for p in trainer.pokemons if p.can_evolve and p.evolution_stage == 1]
        if not evolvable:
            bot.reply_to(message, "❌ Нет покемонов, которые могут эволюционировать")
            return
        
        text = "🔄 *Покемоны, которые могут эволюционировать:*\n\n"
        for p in evolvable:
            text += f"• *{p.name}* (ур. {p.level})\n"
        text += "\nИспользуй: `/evolve имя_покемона`"
        bot.reply_to(message, text)
        return
    
    pokemon_name = parts[1]
    for p in trainer.pokemons:
        if p.name.lower() == pokemon_name.lower():
            if p.evolve():
                bot.reply_to(message, f"✨ *{p.name}* эволюционировал!")
            else:
                bot.reply_to(message, f"❌ *{p.name}* не может эволюционировать")
            return
    
    bot.reply_to(message, "❌ Покемон не найден")

@bot.message_handler(commands=['top_pokemons', 'best'])
def cmd_top_pokemons(message):
    all_pokemons = []
    for trainer in Trainer.trainers.values():
        for pokemon in trainer.pokemons:
            power = pokemon.hp + pokemon.attack + pokemon.defense + pokemon.speed
            all_pokemons.append((pokemon, trainer.name, power))
    
    if not all_pokemons:
        bot.reply_to(message, "❌ В мире пока нет покемонов")
        return
    
    all_pokemons.sort(key=lambda x: x[2], reverse=True)
    
    text = "🏆 *Топ 10 покемонов:*\n\n"
    for i, (pokemon, trainer_name, power) in enumerate(all_pokemons[:10], 1):
        text += f"{i}. *{pokemon.name}* {pokemon.type_emoji()}\n"
        text += f"   👤 Тренер: {trainer_name}\n"
        text += f"   ⚡ Сила: {power} | Ур. {pokemon.level}\n"
        text += f"   🏆 Побед: {pokemon.battles_won}\n\n"
    
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['gym'])
def cmd_gym(message):
    uname = get_username_from_user(message.from_user)
    trainer = Trainer.trainers.get(uname)
    
    if not trainer or not trainer.pokemons:
        bot.reply_to(message, "❌ Нужен хотя бы один покемон для боя в зале")
        return
    
    # Создаем сильного NPC-тренера
    gym_leader = Trainer("Лидер Залы Брок")
    gym_leader.pokemons = [
        Pokemon("Geodude", "rock", 80, 100, 120, 30),
        Pokemon("Onix", "rock", 120, 80, 150, 50)
    ]
    
    battle = Battle(trainer, gym_leader)
    result = battle.start()
    
    bot.send_message(message.chat.id, f"🏛️ *Бой в Зале Скалы!*\n\n{result}")

@bot.message_handler(commands=['release'])
def cmd_release(message):
    uname = get_username_from_user(message.from_user)
    trainer = Trainer.trainers.get(uname)
    
    if not trainer:
        bot.reply_to(message, "❌ Сначала создай профиль /create")
        return
    
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        # Показать список покемонов для отпускания
        if not trainer.pokemons:
            bot.reply_to(message, "❌ У тебя нет покемонов")
            return
        
        text = "🕊️ *Твои покемоны (отпусти кого-то):*\n\n"
        for i, p in enumerate(trainer.pokemons, 1):
            text += f"{i}. *{p.name}* (ур. {p.level})\n"
        
        text += "\nИспользуй: `/release имя_покемона`"
        bot.reply_to(message, text)
        return
    
    pokemon_name = parts[1]
    success, result = trainer.release_pokemon(pokemon_name)
    bot.reply_to(message, result)

@bot.message_handler(commands=['heal'])
def cmd_heal(message):
    uname = get_username_from_user(message.from_user)
    trainer = Trainer.trainers.get(uname)
    
    if not trainer:
        bot.reply_to(message, "❌ Сначала создай профиль /create")
        return
    
    if not trainer.pokemons:
        bot.reply_to(message, "❌ У тебя нет покемонов")
        return
    
    result = trainer.heal_all()
    bot.reply_to(message, result)

# Добавляем команду /fight с инлайн-кнопками из logic1.py
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
battle_selection = {}

@bot.message_handler(commands=['fight'])
def cmd_fight(message):
    uname = get_username_from_user(message.from_user)
    trainer = Trainer.trainers.get(uname)
    
    if not trainer or not trainer.pokemons:
        bot.reply_to(message, "❌ Нет покемонов для боя.")
        return
    
    kb = InlineKeyboardMarkup()
    for p in trainer.pokemons:
        kb.add(InlineKeyboardButton(text=p.name, callback_data=f"pick_{p.name}"))
    
    battle_selection[message.from_user.id] = {"step": 1}
    bot.send_message(message.chat.id, "⚔️ Выбери своего покемона для боя:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("pick_"))
def pick_callback(call):
    user_id = call.from_user.id
    pname = call.data.split("_", 1)[1]
    
    if user_id not in battle_selection:
        bot.answer_callback_query(call.id, "Начни бой командой /fight")
        return
    
    uname = get_username_from_user(call.from_user)
    trainer = Trainer.trainers[uname]
    
    p = next((x for x in trainer.pokemons if x.name == pname), None)
    if not p:
        bot.answer_callback_query(call.id, "❌ Покемон не найден")
        return
    
    if battle_selection[user_id]["step"] == 1:
        battle_selection[user_id]["first"] = p
        battle_selection[user_id]["step"] = 2
        bot.edit_message_text(
            "✅ Выбран покемон для боя! Теперь попроси оппонента тоже использовать /fight и выбрать своего покемона.",
            call.message.chat.id,
            call.message.message_id
        )
    else:
        first = battle_selection[user_id]["first"]
        second = p
        
        # Простой расчет победителя по скорости
        winner = first if first.speed >= second.speed else second
        loser = second if winner == first else first
        
        # Начисление XP победителю
        winner.add_xp(25)
        
        result = (
            f"⚔️ *Бой завершен!*\n\n"
            f"{first.name} (Скорость: {first.speed}) vs {second.name} (Скорость: {second.speed})\n\n"
            f"🏆 Победил: *{winner.name}!*\n"
            f"🎯 {winner.name} получает 25 XP"
        )
        
        del battle_selection[user_id]
        bot.send_message(call.message.chat.id, result)

@bot.message_handler(func=lambda m: True)
def fallback(message):
    # Небольшая подсказка на любые другие сообщения
    if message.text and message.text.startswith('/'):
        # неизвестная команда
        bot.reply_to(message, 
            "❌ Неизвестная команда. Напиши /help для списка команд\n"
            "💡 Быстрые команды:\n"
            "/catch — поймать покемона\n"
            "/daily — ежедневная награда\n"
            "/my — мой профиль"
        )
    # иначе — игнорируем

if __name__ == "__main__":
    print("Bot started...")
    bot.infinity_polling(none_stop=True)