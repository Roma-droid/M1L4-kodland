from random import randint
import requests
import random

# Добавляем словарь эмодзи
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
        ...
        # IV — индивидуальная генетика
        self.iv_hp = random.randint(0, 31)
        self.iv_attack = random.randint(0, 31)
        self.iv_defense = random.randint(0, 31)
        self.iv_speed = random.randint(0, 31)

        # EV — награда от боёв
        self.ev_hp = 0
        self.ev_attack = 0
        self.ev_defense = 0
        self.ev_speed = 0

    def apply_ev_gain(self):
        # EV растут на случайные 1–3
        self.ev_hp += random.randint(1, 3)
        self.ev_attack += random.randint(1, 3)
        self.ev_defense += random.randint(1, 3)
        self.ev_speed += random.randint(1, 3)

    def total_stat(self, base, iv, ev):
        return base + iv + ev // 4  # простая формула

class Pokemon:
    pokemons = {}

    def __init__(self, pokemon_trainer):
        self.pokemon_trainer = pokemon_trainer
        self.pokemon_number = randint(1, 898)  # Реальные ID покемонов в PokeAPI (до 898)
        self.name = None
        self.img = None
        self.health = 100
        self.attack = randint(20, 50)
        
        # Единовременное получение данных
        self.get_pokemon_info()

        Pokemon.pokemons[pokemon_trainer] = self

    def get_pokemon_info(self):
        """Однократный запрос к API для получения имени и изображения"""
        url = f'https://pokeapi.co/api/v2/pokemon/{self.pokemon_number}'
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.name = data['forms'][0]['name'].title()
                self.img = data['sprites']['front_default']
                return
        except requests.exceptions.RequestException:
            pass  # В случае любой ошибки — используем значения по умолчанию

        # Резервные значения
        self.name = "Pikachu"
        self.img = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/25.png"

    def info(self):
        return (
            f"✅ Имя твоего покемона: **{self.name}**\n"
            f"❤️ Здоровье: {self.health}\n"
            f"⚔️ Атака: {self.attack}"
        )

    def show_img(self):
        return self.img

    def attack_pokemon(self, enemy):
        if isinstance(enemy, Pokemon):
            damage = self.attack
            enemy.health -= damage
            if enemy.health <= 0:
                enemy.health = 0
                return f"💥 {self.name} атаковал {enemy.name} и нанёс {damage} урона!\n🎉 {enemy.name} побеждён!"
            else:
                return f"💥 {self.name} атаковал {enemy.name} и нанёс {damage} урона!\n❤️ У {enemy.name} осталось {enemy.health} здоровья."
        return "Цель не является покемоном!"


class Trainer:
    trainers = {}

    def __init__(self, name):
        self.name = name
        self.pokemons = []
        Trainer.trainers[name] = self

    def add_pokemon(self):
        if len(self.pokemons) < 6:  # Максимум 6 покемонов
            new_pokemon = Pokemon(self.name + f"_pokemon_{len(self.pokemons)}")
            self.pokemons.append(new_pokemon)
            return f"{self.name} поймал покемона: {new_pokemon.name}!"
        return "У тренера уже 6 покемонов — максимум!"

    def info(self):
        if not self.pokemons:
            return f"📦 У {self.name} пока нет покемонов."
        result = f"📦 Покемоны {self.name}:\n"
        for i, p in enumerate(self.pokemons, 1):
            result += f"{i}. {p.name} (❤️{p.health}, ⚔️{p.attack})\n"
        return result


class Battle:
    def __init__(self, trainer1: Trainer, trainer2: Trainer):
        self.trainer1 = trainer1
        self.trainer2 = trainer2
        self.winner = None

    def start(self):
        if not self.trainer1.pokemons or not self.trainer2.pokemons:
            return "❗ Один из тренеров не имеет покемонов для битвы!"

        p1 = self.trainer1.pokemons[0]  # Берём первого покемона
        p2 = self.trainer2.pokemons[0]

        result = f"🔥 Бой начинается: {p1.name} ({self.trainer1.name}) против {p2.name} ({self.trainer2.name})!\n\n"

        # Пошаговая атака
        while p1.health > 0 and p2.health > 0:
            result += p1.attack_pokemon(p2) + "\n"
            if p2.health <= 0:
                break
            result += p2.attack_pokemon(p1) + "\n"

        if p1.health > 0:
            self.winner = self.trainer1
            result += f"\n🏆 Победитель: {self.trainer1.name}!"
        else:
            self.winner = self.trainer2
            result += f"\n🏆 Победитель: {self.trainer2.name}!"

        return result
