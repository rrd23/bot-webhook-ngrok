import os
import logging
import aiohttp
import asyncio
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

# Асинхронная версия получения URL ngrok
async def get_ngrok_url():
    url = 'http://ngrok_tunnel:4040/api/tunnels'
    max_attempts = 10
    attempt = 0
    
    async with aiohttp.ClientSession() as session:
        while attempt < max_attempts:
            try:
                async with session.get(url) as response:
                    data = await response.json()
                    if len(data['tunnels']) > 0:
                        public_url = data['tunnels'][0]['public_url']
                        return public_url
                    else:
                        logging.info(f"No tunnels found. Attempt {attempt+1}/{max_attempts}. Retrying in 3 seconds...")
            except aiohttp.ClientError:
                logging.info(f"Connection error on attempt {attempt+1}/{max_attempts}. Retrying in 3 seconds...")
            
            attempt += 1
            await asyncio.sleep(3)
    
    raise ConnectionError("Failed to connect to ngrok or no tunnels available after multiple attempts")

# Настраиваем вебхуки и HTTP сервер
async def on_startup(app):
    webhook_url = f"{await get_ngrok_url()}/webhook"
    logging.info(f"Setting webhook: {webhook_url}")
    await bot.set_webhook(webhook_url)

async def on_shutdown(app):
    await bot.delete_webhook()

# Основная функция для запуска сервера
async def main():
    # Настраиваем Aiohttp веб-приложение
    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/webhook")  # Путь для вебхука
    
    # Вебхук устанавливается при запуске приложения
    app.on_startup.append(on_startup)
    
    # Удаляем вебхук при остановке
    app.on_shutdown.append(on_shutdown)
    
    return app

if __name__ == '__main__':
    app = asyncio.run(main())
    web.run_app(app, host="0.0.0.0", port=3000)
