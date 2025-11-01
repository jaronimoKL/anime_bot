import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
# DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///database/anime_bot.db')
current_dir = os.path.dirname(os.path.abspath(__file__))  # Путь к src/
database_dir = os.path.join(current_dir, 'database')      # Путь к src/database/
db_path = os.path.join(database_dir, 'anime_bot.db')      # Путь к src/database/anime_bot.db

# Создаем директорию database если её нет
os.makedirs(database_dir, exist_ok=True)

DATABASE_URL = f'sqlite+aiosqlite:///{db_path}'