# ========================= logic.py =========================
# Полный модуль логики покемон-бота

import random
import json
import os
from datetime import datetime

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
    "fighting": "🥊",
    "flying": "🕊️",
    "poison": "☠️",
    "ground": "⛰️",
    "bug": "🐛",
    "dark": "🌑",
    "steel": "⚙️",
    "fairy": "🧚"
}

POKEMON_DB = {
    "Pikachu": {"type": "electric", "base_hp": 35, "base_attack": 55, "base_defense": 40, "base_speed": 90},
    "Charmander": {"type": "fire", "base_hp": 39, "base_attack": 52, "base_defense": 43, "base_speed": 65},
    "Squirtle": {"type": "water", "base_hp": 44, "base_attack": 48, "base_defense": 65, "base_speed": 43},
    "Bulbasaur": {"type": "grass", "base_hp": 45, "base_attack": 49, "base_defense": 49, "base_speed": 45},
    "Dratini": {"type": "dragon", "base_hp": 41, "base_attack": 64, "base_defense": 45, "base_speed": 50},
    "Eevee": {"type": "normal", "base_hp": 55, "base_attack": 55, "base_defense": 50, "base_speed": 55},
    "Gastly": {"type": "ghost", "base_hp": 30, "base_attack": 35, "base_defense": 30, "base_speed": 80},
    "Geodude": {"type": "rock", "base_hp": 40, "base_attack": 80, "base_defense": 100, "base_speed": 20},
    "Abra": {"type": "psychic", "base_hp": 25, "base_attack": 20, "base_defense": 15, "base_speed": 90},
    "Magikarp": {"type": "water", "base_hp": 20, "base_attack": 10, "base_defense": 55, "base_speed": 80}
}

class Pokemon:
    def __init__(self, name, type, hp, attack, defense, speed, image_path=None):
        self.name = name
        self.type = type
        self.max_hp = hp
        self.hp = hp
        self.attack = attack
        self.defense = defense
        self.speed = speed
        self.image_path = image_path

        # Уровни
        self.level = 1
        self.xp = 0
        self.xp_to_next = 100

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

        # Эволюция
        self.can_evolve = random.random() < 0.3  # 30% шанс что покемон может эволюционировать
        self.evolution_stage = 1
        
        # Боевая статистика
        self.battles_won = 0
        self.battles_lost = 0

    def show_img(self):
        return self.image_path

    def type_emoji(self):
        return TYPE_EMOJI.get(self.type.lower(), "❔")

    def add_xp(self, amount):
        self.xp += amount
        while self.xp >= self.xp_to_next:
            self.level_up()

    def level_up(self):
        self.level += 1
        self.xp -= self.xp_to_next
        self.xp_to_next = int(self.xp_to_next * 1.5)

        # рост характеристик с учетом IV и EV
        self.max_hp += 2 + (self.iv_hp // 10) + (self.ev_hp // 50)
        self.attack += 1 + (self.iv_attack // 15) + (self.ev_attack // 50)
        self.defense += 1 + (self.iv_defense // 15) + (self.ev_defense // 50)
        self.speed += 1 + (self.iv_speed // 15) + (self.ev_speed // 50)
        
        # Восстановление HP при повышении уровня
        self.hp = self.max_hp

    def apply_ev_gain(self):
        self.ev_hp += random.randint(1, 3)
        self.ev_attack += random.randint(1, 3)
        self.ev_defense += random.randint(1, 3)
        self.ev_speed += random.randint(1, 3)

    def heal(self):
        self.hp = self.max_hp
        self.ev_attack = max(0, self.ev_attack - 5)

    def evolve(self):
        if self.can_evolve and self.evolution_stage == 1:
            self.evolution_stage = 2
            self.name = f"Mega {self.name}"
            self.max_hp += 20
            self.hp = self.max_hp
            self.attack += 15
            self.defense += 10
            self.speed += 5
            return True
        return False

    def info_detailed(self):
        return (
            f"*{self.name}* {self.type_emoji()} (Ур. {self.level})\n"
            f"XP: `{self.xp}/{self.xp_to_next}` | Победы: `{self.battles_won}`\n"
            f"HP: `{self.hp}/{self.max_hp}` (IV: {self.iv_hp}, EV: {self.ev_hp})\n"
            f"Атака: `{self.attack}` (IV: {self.iv_attack}, EV: {self.ev_attack})\n"
            f"Защита: `{self.defense}` (IV: {self.iv_defense}, EV: {self.ev_defense})\n"
            f"Скорость: `{self.speed}` (IV: {self.iv_speed}, EV: {self.ev_speed})\n"
            f"Эволюция: {'🟢 Доступна' if self.can_evolve and self.evolution_stage == 1 else '🔴 Недоступна'}"
        )


class Trainer:
    trainers = {}
    
    def __init__(self, name):
        self.name = name
        self.pokemons = []
        self.items = {
            "potion": 3,
            "super_potion": 1,
            "trap": 0,
            "boost": 1,
            "rare_candy": 0,
            "evolution_stone": 0
        }
        self.coins = 100
        self.battles_won = 0
        self.battles_lost = 0
        self.last_daily = None
        Trainer.trainers[name] = self

    def info(self):
        total_power = sum((p.hp + p.attack + p.defense + p.speed) for p in self.pokemons)
        return (
            f"*Тренер: {self.name}*\n"
            f"Покемоны: `{len(self.pokemons)}/6`\n"
            f"Монеты: `{self.coins}` 💰\n"
            f"Бои: `{self.battles_won}🏆 / {self.battles_lost}💔`\n"
            f"Общая сила: `{total_power}`\n"
            f"Средний уровень: `{sum(p.level for p in self.pokemons) / max(1, len(self.pokemons)):.1f}`"
        )

    def add_pokemon(self):
        if len(self.pokemons) >= 6:
            return "❌ У тебя уже максимальное количество покемонов (6)! Используй /release чтобы отпустить кого-то."

        name = random.choice(list(POKEMON_DB.keys()))
        data = POKEMON_DB[name]
        
        # Базовые статы с небольшим разбросом
        hp = data["base_hp"] + random.randint(-5, 10)
        attack = data["base_attack"] + random.randint(-3, 7)
        defense = data["base_defense"] + random.randint(-3, 7)
        speed = data["base_speed"] + random.randint(-5, 10)
        
        type_ = data["type"]
        image_path = f"images/{name.lower()}.png"

        # Шанс на редкого покемона (5%)
        is_shiny = random.random() < 0.05
        if is_shiny:
            name = f"🌟 Shiny {name}"
            hp += 30
            attack += 20
            defense += 15
            speed += 15
            image_path = f"images/shiny_{name.lower().replace(' ', '_')}.png"

        p = Pokemon(name, type_, hp, attack, defense, speed, image_path)
        self.pokemons.append(p)
        
        return f"🎉 Ты поймал *{p.name}*! (HP: {p.hp}, Атака: {p.attack})"

    def use_item(self, item_name, pokemon_name):
        item_name = item_name.lower()
        
        if item_name not in self.items or self.items[item_name] <= 0:
            return False, "❌ У тебя нет такого предмета."

        pokemon = None
        for p in self.pokemons:
            if p.name.lower() == pokemon_name.lower():
                pokemon = p
                break

        if not pokemon:
            return False, "❌ Покемон не найден."

        result = ""
        if item_name == "potion":
            heal_amount = 20
            pokemon.hp = min(pokemon.hp + heal_amount, pokemon.max_hp)
            result = f"💊 Использовано зелье на {pokemon.name}. HP: {pokemon.hp}/{pokemon.max_hp}"
        elif item_name == "super_potion":
            heal_amount = 50
            pokemon.hp = min(pokemon.hp + heal_amount, pokemon.max_hp)
            result = f"💊 Использовано супер-зелье на {pokemon.name}. HP: {pokemon.hp}/{pokemon.max_hp}"
        elif item_name == "boost":
            pokemon.attack += 5
            result = f"💪 Использован буст на {pokemon.name}. Атака теперь: {pokemon.attack}"
        elif item_name == "rare_candy":
            pokemon.add_xp(50)
            result = f"🍬 Использована редкая конфета на {pokemon.name}. XP +50!"
        elif item_name == "evolution_stone":
            if pokemon.evolve():
                result = f"✨ {pokemon.name} эволюционировал!"
            else:
                result = f"❌ Этот покемон не может эволюционировать."
                return False, result

        self.items[item_name] -= 1
        return True, result

    def heal_all(self):
        for p in self.pokemons:
            p.heal()
        return "💚 Все покемоны вылечены!"

    def release_pokemon(self, pokemon_name):
        for i, p in enumerate(self.pokemons):
            if p.name.lower() == pokemon_name.lower():
                released = self.pokemons.pop(i)
                self.coins += released.level * 5  # Награда за отпускание
                return True, f"🕊️ Покемон {released.name} отпущен на волю. Получено {released.level * 5} монет!"
        return False, "❌ Покемон не найден."

    def get_items_list(self):
        if not any(count > 0 for count in self.items.values()):
            return "📦 Инвентарь пуст. Используй /daily или /shop"
        
        text = "📦 *Твой инвентарь:*\n"
        for item, count in self.items.items():
            if count > 0:
                text += f"• {item}: `{count}`\n"
        text += f"\n💰 Монеты: `{self.coins}`"
        return text

    def claim_daily(self):
        today = datetime.now().date()
        if self.last_daily and self.last_daily == today:
            return False, "❌ Ты уже получал ежедневную награду сегодня. Приходи завтра!"
        
        self.last_daily = today
        reward = random.choice(["potion", "super_potion", "boost", "coins"])
        
        if reward == "coins":
            amount = random.randint(50, 150)
            self.coins += amount
            return True, f"🎁 Ежедневная награда: {amount} монет!"
        else:
            self.items[reward] += 1
            return True, f"🎁 Ежедневная награда: 1x {reward}!"


class Battle:
    def __init__(self, t1, t2):
        self.t1 = t1
        self.t2 = t2
        self.log = []

    def calculate_damage(self, attacker, defender):
        # Базовая формула урона
        damage = max(1, attacker.attack - defender.defense // 2)
        
        # Критический удар (10% шанс)
        if random.random() < 0.1:
            damage *= 2
            self.log.append(f"✨ Критический удар!")
        
        # Множитель типа (упрощенный)
        type_multiplier = 1.0
        if attacker.type == "water" and defender.type == "fire":
            type_multiplier = 2.0
        elif attacker.type == "fire" and defender.type == "grass":
            type_multiplier = 2.0
        elif attacker.type == "grass" and defender.type == "water":
            type_multiplier = 2.0
            
        damage = int(damage * type_multiplier)
        return max(1, damage)

    def start(self):
        p1 = self.t1.pokemons[0]
        p2 = self.t2.pokemons[0]
        
        self.log.append(f"⚔️ *Бой начинается!*")
        self.log.append(f"{p1.name} (HP: {p1.hp}) vs {p2.name} (HP: {p2.hp})")

        turn = 1
        while p1.hp > 0 and p2.hp > 0 and turn <= 20:
            # Определяем очередность по скорости
            if p1.speed >= p2.speed:
                first, second = p1, p2
                first_trainer, second_trainer = self.t1, self.t2
            else:
                first, second = p2, p1
                first_trainer, second_trainer = self.t2, self.t1

            # Атака первого
            damage = self.calculate_damage(first, second)
            second.hp -= damage
            self.log.append(f"Ход {turn}: {first.name} атакует {second.name} (урон: {damage})")

            if second.hp <= 0:
                winner = first
                loser = second
                winner_trainer = first_trainer
                loser_trainer = second_trainer
                break

            # Атака второго
            damage = self.calculate_damage(second, first)
            first.hp -= damage
            self.log.append(f"       {second.name} атакует {first.name} (урон: {damage})")

            if first.hp <= 0:
                winner = second
                loser = first
                winner_trainer = second_trainer
                loser_trainer = first_trainer
                break

            turn += 1

        # Определяем победителя
        if p1.hp <= 0:
            winner = p2
            loser = p1
            winner_trainer = self.t2
            loser_trainer = self.t1
        else:
            winner = p1
            loser = p2
            winner_trainer = self.t1
            loser_trainer = self.t2

        # Награды
        xp_gain = 25 + loser.level * 5
        winner.add_xp(xp_gain)
        winner.apply_ev_gain()
        winner.battles_won += 1
        loser.battles_lost += 1
        
        winner_trainer.battles_won += 1
        loser_trainer.battles_lost += 1
        winner_trainer.coins += 50
        loser_trainer.coins += 20

        self.log.append(f"\n🏆 *Победитель: {winner.name}!*")
        self.log.append(f"🎯 {winner.name} получает {xp_gain} XP")
        self.log.append(f"💰 {winner_trainer.name} получает 50 монет, {loser_trainer.name} получает 20 монет")

        return "\n".join(self.log)