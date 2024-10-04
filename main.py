import os
import aiohttp
import logging
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

API_TOKEN = '7334080838:AAECrnJlcDbhrdWVmSAK85VVre2z1fV-6p4'
DJANGO_SAVE_URL = 'http://localhost:8000/save-message'


# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
print(API_TOKEN)


@dp.message(Command("start"))
async def start_command(message: Message):
    print(message.chat.id)
    await message.answer("Xush kelibsiz! Sizning xabaringizni saqlash uchun xabar yuboring.")

@dp.message()
async def save_message(message: Message):
    user = message.from_user
    user_message = message.text
    chat_id = message.chat.id  # Get the chat_id from the message

    async with aiohttp.ClientSession() as session:
        # Prepare the data to send to Django
        data = {
            'first_name': user.first_name,
            'message': user_message,
            'chat_id': chat_id  # Send chat_id
        }
        async with session.post(DJANGO_SAVE_URL, data=data) as response:
            if response.status == 200:
                await message.reply("Xabaringiz saqlandi.")
            else:
                await message.reply("Xabarni saqlashda xatolik yuz berdi!")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
