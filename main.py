import os
import aiohttp
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

from ERRORS import send_error_to_telegram
from config import *




logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

class Form(StatesGroup):
    waiting_for_reason = State()
    waiting_for_message = State()


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Creates the main menu inline keyboard."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Aloqa", callback_data='write_to_assistant'),
            InlineKeyboardButton(text="Savol va Javoblar", callback_data='question_answer')
        ]
    ])
    return keyboard


async def check_chat_status(chat_id: int) -> str:
    """Check the chat status (open, closed, etc.) by calling the backend API."""
    async with aiohttp.ClientSession() as session:
        params = {'chat_id': chat_id}
        async with session.get(CHECK_CHAT_STATUS_URL, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return data['status']
            return "closed"


@dp.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    await message.reply("Xush Kelibsiz😊 Iltimos kerakli bo'lgan bo'limni tanlang:", reply_markup=main_menu_keyboard())


@dp.callback_query()
async def handle_inline_buttons(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == 'write_to_assistant':
        chat_id = callback.message.chat.id
        status = await check_chat_status(chat_id)

        if status == "open":
            await callback.message.reply("Siz mutaxassis bilan aloqadasiz xabaringizni yozishingiz mumkin 😊.")
            await state.set_state(Form.waiting_for_message)
        if status == "new":
            await callback.message.reply("Mutaxassis bilan bog'lanish uchun avval iltimos arizangiz sababini kiriting! ")
            await state.set_state(Form.waiting_for_reason)
        if status == "closed":
            await callback.message.reply("Avvalgi aloqa mutaxassis tomonidan yopilgan. Iltimos arizangiz sababini kiriting!")
            await state.set_state(Form.waiting_for_reason)  # Set state to waiting for reason
        elif callback.data == 'question_answer':
            law_info = (
                "O'zbekiston Respublikasining qonunlari:\n"
                "1. O'zbekiston Respublikasining Fuqarolik Kodeksi.\n"
                "2. O'zbekiston Respublikasining Jinoyat Kodeksi.\n"
                "3. O'zbekiston Respublikasining Ma'muriy Kodeksi.\n"
                "4. O'zbekiston Respublikasining Mehnat Kodeksi.\n"
                "Savollaringiz bo'lsa, iltimos, ularni yozing."
            )
        await callback.message.reply(law_info)


@dp.message(Form.waiting_for_reason)
async def ask_reason(message: types.Message, state: FSMContext):
    await state.update_data(reason=message.text)
    await message.reply("Rahmat! Endi, iltimos, xabaringizni yuboring.")
    await state.set_state(Form.waiting_for_message)



@dp.message(Form.waiting_for_message)
async def receive_text_message(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    reason = user_data.get('reason', None)  # Get reason if available

    if message.text:
        await save_message(message, reason, state)
    elif message.document:
        await save_file(message, reason, state)
    elif message.video:
        await save_video(message, reason, state)
    elif message.photo:
        await save_photo(message, reason, state)
    else:
        await message.reply("Iltimos to'g'ri matn, rasm, video yoki fayl jo'nating")


async def save_photo(message: types.Message, reason: str, state: FSMContext):
    first_name = message.from_user.first_name
    username = message.from_user.username or "Unknown"
    chat_id = message.chat.id

    if message.photo:
        photo_id = message.photo[-1].file_id
        photo_info = await bot.get_file(photo_id)

        user_directory = f'media/messages/{first_name}_{chat_id}'
        if not os.path.exists(user_directory):
            os.makedirs(user_directory)

        photo_path = os.path.join(user_directory, f"photo_{photo_id}.jpg")

        await bot.download_file(photo_info.file_path, photo_path)
        logging.info(f"Photo saved at: {photo_path}")

        await process_file_to_backend(first_name, username, chat_id, photo_path, reason)

        await message.reply("Suratingiz yuborildi va saqlandi. Iltimos, mutaxassis javobini kuting.")
        if state:
            await state.clear()
    else:
        await message.reply("RAsm topilmadi!!")


async def save_video(message: types.Message, reason: str, state: FSMContext):
    first_name = message.from_user.first_name
    username = message.from_user.username or "Unknown"
    chat_id = message.chat.id

    if message.video:
        video_id = message.video.file_id
        video_info = await bot.get_file(video_id)

        user_directory = f'media/messages/{first_name}_{chat_id}'
        if not os.path.exists(user_directory):
            os.makedirs(user_directory)

        video_path = os.path.join(user_directory, f"{message.video.file_name or 'video.mp4'}")


        await bot.download_file(video_info.file_path, video_path)
        logging.info(f"Video saved at: {video_path}")

        await process_file_to_backend(first_name, username, chat_id, video_path, reason)

        await message.reply("Videongiz yuborildi va saqlandi. Iltimos, mutaxassis javobini kuting.")
        await state.clear()
    else:
        await message.reply("Video topilmadi!!")



async def save_message(message: types.Message, reason: str, state: FSMContext):
    first_name = message.from_user.first_name
    username = message.from_user.username or "Unknown"
    chat_id = message.chat.id
    await process_message_to_backend(first_name, username, chat_id, message.text, reason)
    await message.reply("Xabaringiz Yuborildi Iltimos Mutaxassis Javobini Kuting!")
    if state is not None:
        await state.clear()


async def save_file(message: types.Message, reason: str, state: FSMContext):
    first_name = message.from_user.first_name
    username = message.from_user.username or "Unknown"
    chat_id = message.chat.id

    if message.document:
        file_id = message.document.file_id
        file_name = message.document.file_name
        logging.info(f"Received file: {file_name}")

        file_info = await bot.get_file(file_id)
        logging.info(f"File info: {file_info}")

        user_directory = f'media/messages/{first_name}_{chat_id}'
        if not os.path.exists(user_directory):
            os.makedirs(user_directory)

        file_path = os.path.join(user_directory, file_name)

        await bot.download_file(file_info.file_path, file_path)
        logging.info(f"File saved at: {file_path}")

        await process_file_to_backend(first_name, username, chat_id, file_path, reason)

        await message.reply("Faylingiz yuborildi va saqlandi. Iltimos, mutaxassis javobini kuting.")
        if state:
            await state.clear()
    else:
        await message.reply("Fayl topilmadi. Iltimos, yaroqli hujjat yoki fayl yuboring.")


async def process_message_to_backend(first_name, username, chat_id, message_text, reason):
    """Send the message to the backend."""
    async with aiohttp.ClientSession() as session:
        data = {
            'first_name': first_name,
            'message': message_text,
            'chat_id': chat_id,
            'username': username,
            'reason': reason
        }
        logging.info(f'Sending data to Django: {data}')
        try:
            async with session.post(DJANGO_SAVE_URL, json=data) as response:
                response_text = await response.text()
                logging.info(f'Response status: {response.status}, Response text: {response_text}')
        except Exception as e:
            send_error_to_telegram(str(e))
            logging.error(f"Error occurred while sending data to Django: {e}")


async def process_file_to_backend(first_name, username, chat_id, file_path, reason):
    """Send the file (photo or video) information to the backend."""
    async with aiohttp.ClientSession() as session:
        data = {
            'first_name': first_name,
            'chat_id': chat_id,
            'username': username,
            'file_path': file_path,
            'reason': reason
        }
        logging.info(f'Sending file data to Django: {data}')
        try:
            async with session.post(DJANGO_SAVE_URL, json=data) as response:
                response_text = await response.text()
                logging.info(f'Response status: {response.status}, Response text: {response_text}')
        except Exception as e:
            send_error_to_telegram(str(e))
            logging.error(f"Error occurred while sending file data to Django: {e}")



@dp.message()
async def handle_non_command_message(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    user_data = await state.get_data()

    # Check the chat status
    status = user_data.get('chat_status', await check_chat_status(chat_id))

    if status == 'closed':
        await message.reply(
            "Sizning arizangiz mutaxassis tomonidan yopilgan. Iltimos qayta ariza qoldirish uchun /start tugmasini bosing.")

    elif status == 'open':
        # Handle different message types during ongoing conversation
        if message.text:
            await save_message(message, reason="Ongoing Conversation", state=None)
        elif message.photo:
            await save_photo(message, reason="Ongoing Conversation", state=None)
        elif message.video:
            await save_video(message, reason="Ongoing Conversation", state=None)
        elif message.document:
            await save_file(message, reason="Ongoing Conversation", state=None)
        else:
            await message.reply("Please send a valid text message, photo, file, or video.")

    elif status == 'new':
        await message.reply("Xush kelibsiz! Iltimos, arizangiz sababini kiriting:")
        await state.set_state(Form.waiting_for_reason)  # Set the state to wait for the reason

    elif status == 'waiting':
        # Optionally handle the 'waiting' status if needed
        await message.reply("Sizning arizangiz hali ko'rib chiqilmoqda.")
        if message.text:
            await save_message(message, reason="Ongoing Conversation", state=None)
        elif message.photo:
            await save_photo(message, reason="Ongoing Conversation", state=None)
        elif message.video:
            await save_video(message, reason="Ongoing Conversation", state=None)
        elif message.document:
            await save_file(message, reason="Ongoing Conversation", state=None)
        else:
            await message.reply("Iltimos to'g'ri matn, rasm, video yoki fayl jo'nating!!")



async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
