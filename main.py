import aiohttp
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

from config import API_TOKEN

# Set the Django URLs
DJANGO_SAVE_URL = 'http://localhost:8000/save-message'
CHECK_CHAT_STATUS_URL = 'http://localhost:8000/check-chat-status/'  # Check chat status in Django

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher with state storage
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Define states
class Form(StatesGroup):
    waiting_for_reason = State()
    waiting_for_message = State()

# Create inline keyboard
def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Creates the main menu inline keyboard."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Write to Assistant", callback_data='write_to_assistant'),
            InlineKeyboardButton(text="Question & Answer", callback_data='question_answer')
        ]
    ])
    return keyboard

async def check_chat_status(chat_id: str) -> str:
    """Check the chat status (open, closed, etc.) by calling the backend API."""
    async with aiohttp.ClientSession() as session:
        params = {'chat_id': chat_id}
        async with session.get(CHECK_CHAT_STATUS_URL, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return data['status']
            return "closed"  # Default to closed if there's an issue

@dp.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    chat_id = message.chat.id
    status = await check_chat_status(chat_id)

    if status == "open":
        await message.reply("Your chat is open. You can continue your conversation.", reply_markup=main_menu_keyboard())
        await state.clear()  # Clear any previous state
    else:
        await message.reply("Welcome! Please provide the reason for your message using the inline keyboard.", reply_markup=main_menu_keyboard())

@dp.callback_query()
async def handle_inline_buttons(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == 'write_to_assistant':
        await callback.message.reply("Please provide the reason for your message.")
        await state.set_state(Form.waiting_for_reason)  # Set state to waiting for reason
    elif callback.data == 'question_answer':
        await callback.message.reply("Please type your question.")

@dp.message(Form.waiting_for_reason)
async def ask_reason(message: types.Message, state: FSMContext):
    # Store the reason and ask for the actual message
    await state.update_data(reason=message.text)
    logging.info(f"Stored reason: {message.text}")

    await message.reply("Thank you! Now, please send your message.")
    await state.set_state(Form.waiting_for_message)  # Move to waiting for the message

@dp.message(Form.waiting_for_message)
async def receive_text_message(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    reason = user_data.get('reason')
    await save_message(message, reason, state)

@dp.message(Form.waiting_for_message)
async def receive_document_message(message: types.Message, state: FSMContext):
    if message.document:
        user_data = await state.get_data()
        reason = user_data.get('reason')

        # Instead of replying, just send the file to the backend
        await save_file(message, reason, state)

async def save_message(message: types.Message, reason: str, state: FSMContext):
    first_name = message.from_user.first_name
    username = message.from_user.username or "Unknown"
    chat_id = message.chat.id

    if reason and message.text:
        # Send the message to the backend
        await process_message_to_backend(first_name, username, chat_id, message.text, reason)
        await message.reply("Your message has been sent. Please wait for an assistant to respond.")
        if state:
            await state.clear()
    else:
        await message.reply("Please provide a reason before sending your message.")

async def save_file(message: types.Message, reason: str, state: FSMContext):
    first_name = message.from_user.first_name
    username = message.from_user.username or "Unknown"
    chat_id = message.chat.id

    # Get the file ID
    file_id = message.document.file_id

    # Download the file and get the file path
    file = await bot.get_file(file_id)

    # Send the file to your backend or save it
    await process_file_to_backend(first_name, username, chat_id, file.file_path, reason)

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
            logging.error(f"Error occurred while sending data to Django: {e}")

async def process_file_to_backend(first_name, username, chat_id, file_path, reason):
    """Send the file information to the backend."""
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
            logging.error(f"Error occurred while sending file data to Django: {e}")

@dp.message()
async def handle_non_command_message(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    status = await check_chat_status(chat_id)

    if status == 'closed':
        # If the chat is closed and user sends a message without starting, inform them to use /start
        await message.reply("Your chat is closed. Please press /start to begin a new request.")
    else:
        # If chat is open, handle the message and send it to the backend
        await save_message(message, reason="Ongoing Conversation", state=None)

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
