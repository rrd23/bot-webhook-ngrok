import os
import logging
import requests
import time
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiohttp import web

# Получаем токен бота из переменных окружения
API_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Простой обработчик команды /start
@dp.message(Command(commands=['start']))
async def start_command(message: types.Message):
    await message.answer("Привет! Это бот на вебхуках.")

# Получение публичного URL ngrok с повторными попытками
def get_ngrok_url():
    url = 'http://ngrok_tunnel:4040/api/tunnels'
    max_attempts = 10  # Максимум 10 попыток
    attempt = 0
    while attempt < max_attempts:
        try:
            response = requests.get(url)  # Запрашиваем API ngrok
            data = response.json()
            if len(data['tunnels']) > 0:  # Проверяем, есть ли хотя бы один туннель
                public_url = data['tunnels'][0]['public_url']  # Извлекаем публичный URL
                return public_url
            else:
                logging.info(f"No tunnels found. Attempt {attempt+1}/{max_attempts}. Retrying in 3 seconds...")
        except requests.exceptions.ConnectionError:
            logging.info(f"Connection error on attempt {attempt+1}/{max_attempts}. Retrying in 3 seconds...")
        
        attempt += 1
        time.sleep(3)  # Ожидание перед новой попыткой
    
    raise ConnectionError("Failed to connect to ngrok or no tunnels available after multiple attempts")

# Настраиваем вебхуки и HTTP сервер
async def on_startup(app):
    webhook_url = f"{get_ngrok_url()}/webhook"  # Получаем публичный URL ngrok
    logging.info(f"Setting webhook: {webhook_url}")
    await bot.set_webhook(webhook_url)

async def on_shutdown(app):
    await bot.delete_webhook()

# Основная функция для запуска сервера
def main():
    # Настраиваем Aiohttp веб-приложение
    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/webhook")  # Путь для вебхука
    
    # Вебхук устанавливается при запуске приложения
    app.on_startup.append(on_startup)
    
    # Удаляем вебхук при остановке
    app.on_shutdown.append(on_shutdown)
    
    # Запускаем HTTP сервер (без asyncio.run())
    web.run_app(app, host="0.0.0.0", port=3000)

if __name__ == '__main__':
    main()
