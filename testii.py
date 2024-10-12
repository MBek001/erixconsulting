# import os
# import aiohttp
# import logging
# import asyncio
# from aiogram import Bot, Dispatcher, types
# from aiogram.filters import Command
# from aiogram.fsm.context import FSMContext
# from aiogram.fsm.state import State, StatesGroup
# from aiogram.fsm.storage.memory import MemoryStorage
# from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
#
# from config import API_TOKEN
#
# # Set the Django URLs
# DJANGO_SAVE_URL = 'http://localhost:8000/save-message'
# CHECK_CHAT_STATUS_URL = 'http://localhost:8000/check-chat-status/'  # Check chat status in Django
#
# # Configure logging
# logging.basicConfig(level=logging.INFO)
#
# # Initialize bot and dispatcher with state storage
# bot = Bot(token=API_TOKEN)
# storage = MemoryStorage()
# dp = Dispatcher(storage=storage)
#
#
# # Define states
# class Form(StatesGroup):
#     waiting_for_reason = State()
#     waiting_for_message = State()
#
#
# # Create inline keyboard
# def main_menu_keyboard() -> InlineKeyboardMarkup:
#     """Creates the main menu inline keyboard."""
#     keyboard = InlineKeyboardMarkup(inline_keyboard=[
#         [
#             InlineKeyboardButton(text="Aloqa", callback_data='write_to_assistant'),
#             InlineKeyboardButton(text="Question & Answer", callback_data='question_answer')
#         ]
#     ])
#     return keyboard
#
#
# async def check_chat_status(chat_id: int) -> str:
#     """Check the chat status (open, closed, etc.) by calling the backend API."""
#     async with aiohttp.ClientSession() as session:
#         params = {'chat_id': chat_id}
#         async with session.get(CHECK_CHAT_STATUS_URL, params=params) as response:
#             if response.status == 200:
#                 data = await response.json()
#                 return data['status']
#             return "closed"
#
#
# @dp.message(Command("start"))
# async def start_command(message: Message, state: FSMContext):
#     await message.reply("Welcome! Please choose an option:", reply_markup=main_menu_keyboard())
#
#
# @dp.callback_query()
# async def handle_inline_buttons(callback: types.CallbackQuery, state: FSMContext):
#     if callback.data == 'write_to_assistant':
#         chat_id = callback.message.chat.id
#         status = await check_chat_status(chat_id)
#
#         if status == "open":
#             await callback.message.reply("Siz mutaxassis bilan aloqadasiz xabaringizni yozishingiz mumkin 😊.")
#             await state.set_state(Form.waiting_for_message)
#         if status == "new":
#             await callback.message.reply("Mutaxassis bilan bog'lanish uchun avval iltimos arizangiz sababini kiriting! ")
#             await state.set_state(Form.waiting_for_reason)
#         if status == "closed":
#             await callback.message.reply("Avvalgi aloqa mutaxassis tomonidan yopilgan. Iltimos arizangiz sababini kiriting!")
#             await state.set_state(Form.waiting_for_reason)  # Set state to waiting for reason
#     elif callback.data == 'question_answer':
#         await callback.message.reply("Please type your question.")
#
#
# @dp.message(Form.waiting_for_reason)
# async def ask_reason(message: types.Message, state: FSMContext):
#     await state.update_data(reason=message.text)  # Save the reason
#     await message.reply("Rahmat! Endi, iltimos, xabaringizni yuboring.")
#     await state.set_state(Form.waiting_for_message)
#
#
# @dp.message(Form.waiting_for_message)
# async def receive_text_message(message: types.Message, state: FSMContext):
#     user_data = await state.get_data()
#     reason = user_data.get('reason', None)  # Get reason if available
#
#     if message.text:
#         await save_message(message, reason, state)
#     elif message.document:
#         await save_file(message, reason, state)
#     elif message.video:
#         await save_video(message, reason, state)  # Handle video file
#     elif message.photo:
#         await save_photo(message, reason, state)  # Handle photo file
#     else:
#         await message.reply("Please send a valid text message, photo, file, or video.")
#
# async def save_photo(message: types.Message, reason: str, state: FSMContext):
#     first_name = message.from_user.first_name
#     username = message.from_user.username or "Unknown"
#     chat_id = message.chat.id
#
#     # Check if the message contains a photo
#     if message.photo:
#         photo_id = message.photo[-1].file_id  # Get the highest resolution photo
#         photo_info = await bot.get_file(photo_id)
#
#         # Create user directory for saving the photo
#         user_directory = f'media/messages/{first_name}_{chat_id}'
#         if not os.path.exists(user_directory):
#             os.makedirs(user_directory)
#
#         # Save the photo locally
#         photo_path = os.path.join(user_directory, f"photo_{photo_id}.jpg")
#
#         # Download the photo
#         await bot.download_file(photo_info.file_path, photo_path)
#         logging.info(f"Photo saved at: {photo_path}")  # Log the saved photo path
#
#         # Process and send the photo information to the backend
#         await process_file_to_backend(first_name, username, chat_id, photo_path, reason)
#
#         await message.reply("Suratingiz yuborildi va saqlandi. Iltimos, mutaxassis javobini kuting.")
#         await state.clear()
#     else:
#         await message.reply("No photo detected. Please send a valid photo.")
#
#
# async def save_video(message: types.Message, reason: str, state: FSMContext):
#     first_name = message.from_user.first_name
#     username = message.from_user.username or "Unknown"
#     chat_id = message.chat.id
#
#     # Check if the message contains a video
#     if message.video:
#         video_id = message.video.file_id
#         video_info = await bot.get_file(video_id)
#
#         # Create user directory for saving the video
#         user_directory = f'media/messages/{first_name}_{chat_id}'
#         if not os.path.exists(user_directory):
#             os.makedirs(user_directory)
#
#         # Save the video locally
#         video_path = os.path.join(user_directory, f"{message.video.file_name or 'video.mp4'}")
#
#         # Download the video
#         await bot.download_file(video_info.file_path, video_path)
#         logging.info(f"Video saved at: {video_path}")  # Log the saved video path
#
#         # Process and send the video information to the backend
#         await process_file_to_backend(first_name, username, chat_id, video_path, reason)
#
#         # Send confirmation message after the video is saved and sent
#         await message.reply("Videongiz yuborildi va saqlandi. Iltimos, mutaxassis javobini kuting.")
#         await state.clear()
#     else:
#         await message.reply("No video detected. Please send a valid video.")
#
#
#
# async def save_message(message: types.Message, reason: str, state: FSMContext):
#     first_name = message.from_user.first_name
#     username = message.from_user.username or "Unknown"
#     chat_id = message.chat.id
#     await process_message_to_backend(first_name, username, chat_id, message.text, reason)
#     await message.reply("Xabaringiz Yuborildi Iltimos Mutaxassis Javobini Kuting!")
#     if state is not None:
#         await state.clear()
#
#
# async def save_file(message: types.Message, reason: str, state: FSMContext):
#     first_name = message.from_user.first_name
#     username = message.from_user.username or "Unknown"
#     chat_id = message.chat.id
#
#     # Check if the message contains a document (file)
#     if message.document:
#         file_id = message.document.file_id
#         file_name = message.document.file_name
#         logging.info(f"Received file: {file_name}")
#
#         file_info = await bot.get_file(file_id)
#         logging.info(f"File info: {file_info}")
#
#         # Create user directory for saving the file
#         user_directory = f'media/messages/{first_name}_{chat_id}'
#         if not os.path.exists(user_directory):
#             os.makedirs(user_directory)
#
#         # Save the file locally
#         file_path = os.path.join(user_directory, file_name)  # Use the original filename
#
#         # Download the file using the file_id
#         await bot.download_file(file_info.file_path, file_path)
#         logging.info(f"File saved at: {file_path}")  # Log the saved file path
#
#         # Process and send the file information to the backend
#         await process_file_to_backend(first_name, username, chat_id, file_path, reason)
#
#         await message.reply("Faylingiz yuborildi va saqlandi. Iltimos, mutaxassis javobini kuting.")
#         await state.clear()
#     else:
#         await message.reply("Fayl topilmadi. Iltimos, yaroqli hujjat yoki fayl yuboring.")
#
#
# async def process_message_to_backend(first_name, username, chat_id, message_text, reason):
#     """Send the message to the backend."""
#     async with aiohttp.ClientSession() as session:
#         data = {
#             'first_name': first_name,
#             'message': message_text,
#             'chat_id': chat_id,
#             'username': username,
#             'reason': reason
#         }
#         logging.info(f'Sending data to Django: {data}')
#         try:
#             async with session.post(DJANGO_SAVE_URL, json=data) as response:
#                 response_text = await response.text()
#                 logging.info(f'Response status: {response.status}, Response text: {response_text}')
#         except Exception as e:
#             logging.error(f"Error occurred while sending data to Django: {e}")
#
#
# async def process_file_to_backend(first_name, username, chat_id, file_path, reason):
#     """Send the file (photo or video) information to the backend."""
#     async with aiohttp.ClientSession() as session:
#         data = {
#             'first_name': first_name,
#             'chat_id': chat_id,
#             'username': username,
#             'file_path': file_path,
#             'reason': reason
#         }
#         logging.info(f'Sending file data to Django: {data}')
#         try:
#             async with session.post(DJANGO_SAVE_URL, json=data) as response:
#                 response_text = await response.text()
#                 logging.info(f'Response status: {response.status}, Response text: {response_text}')
#         except Exception as e:
#             logging.error(f"Error occurred while sending file data to Django: {e}")
#
#
#
# @dp.message()
# async def handle_non_command_message(message: types.Message, state: FSMContext):
#     chat_id = message.chat.id
#     user_data = await state.get_data()
#
#     # Check the chat status
#     status = user_data.get('chat_status', await check_chat_status(chat_id))
#
#     if status == 'closed':
#         await message.reply(
#             "Sizning arizangiz mutaxassis tomonidan yopilgan. Iltimos qayta ariza qoldirish uchun /start tugmasini bosing.")
#
#     elif status == 'open':
#         await save_message(message, reason="Ongoing Conversation", state=None)
#
#     elif status == 'new':
#         await message.reply("Xush kelibsiz! Iltimos, arizangiz sababini kiriting:")
#         await state.set_state(Form.waiting_for_reason)  # Set the state to wait for the reason
#
#     elif status == 'waiting':
#         # Optionally handle the 'waiting' status if needed
#         await message.reply("Sizning arizangiz hali ko'rib chiqilmoqda.")
#
#
# async def main():
#     await dp.start_polling(bot)
#
#
# if __name__ == '__main__':
#     asyncio.run(main())
