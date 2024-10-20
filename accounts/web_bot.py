import asyncio
import os
import logging
import shutil
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.utils import timezone
from flask.cli import load_dotenv
from ERRORS import send_error_to_telegram
from accounts.message_sending import notify_customer
from accounts.models import TelegramUserMessage, ChatRequest, RequestHistory
import requests
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
load_dotenv()
from config import *


BASE_DIR = '/home/tuya/erixconsulting/media/messages/'
TELEGRAM_API_URL = TELEGRAM_API_URL
logger = logging.getLogger(__name__)

@user_passes_test(lambda u: u.is_staff, login_url='/login/')
def chat_page(request):
    messages = []
    users = TelegramUserMessage.objects.filter(staff=request.user).values('first_name', 'chat_id').distinct()
    staff_messages = TelegramUserMessage.objects.filter(staff=request.user)

    for chat in staff_messages:
        file_path = os.path.join(BASE_DIR, chat.message_file.name)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as file:
                    content = file.read()
                    messages.append({
                        'chat_id': chat.chat_id,
                        'first_name': chat.first_name,
                        'message': content,
                        'created_at': chat.created_at,
                        'is_read': chat.is_read
                    })
            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")

    messages = sorted(messages, key=lambda x: x['created_at'], reverse=True)

    return render(request, 'chat_page.html', {'messages': messages, 'users': users})


@csrf_exempt
def send_message_to_bot(request):
    if request.method == 'POST':
        message_text = request.POST.get('message')
        chat_id = request.POST.get('chat_id')
        first_name = request.POST.get('first_name')

        if message_text and chat_id and first_name:
            # Prepare the data to be sent to the bot
            payload = {
                'chat_id': chat_id,
                'text': message_text,
            }
            logger.debug(f"Sending message to Telegram: {payload}")
            try:
                response = requests.post(TELEGRAM_API_URL, json=payload)
                if response.status_code == 200:
                    response_data = response.json()
                    logger.debug(f"Response data: {response_data}")

                    if response_data.get('ok'):
                        try:
                            query = TelegramUserMessage.objects.filter(first_name=first_name)
                            query.update(is_read=True)
                        except Exception as e:
                            logger.error(f"Database update error: {str(e)}")
                            return JsonResponse({'status': 'error', 'message': 'An error occurred while updating the message status.'}, status=500)

                        filename = f'{first_name}_{chat_id}.txt'
                        file_path = os.path.join(BASE_DIR, filename)

                        os.makedirs(os.path.dirname(file_path), exist_ok=True)

                        with open(file_path, 'a') as file:
                            file.write(f'assistant: {message_text}\ncreated_at: {datetime.now()+timedelta(hours=5)}\n')
                        logger.info(f"Message saved to file: {file_path}")
                        return JsonResponse({'status': 'success'}, status=200)
                    else:
                        error_message = response_data.get('description', 'Unknown error')
                        logger.error(f"Telegram API error: {error_message}")
                        return render(request, 'chat_page.html')
                else:
                    logger.error(f"Failed to send message to Telegram bot: {response.text}")
                    return render(request, 'chat_page.html')
            except Exception as e:
                send_error_to_telegram(e)
                logger.error(f"Exception occurred while sending message: {str(e)}")
                return render(request, 'chat_page.html')
        else:
            logger.warning("No message, chat ID, or first name provided.")
            return render(request, 'chat_page.html', {'active_page': 'chat1'})

    return JsonResponse({'status': 'invalid method'}, status=405)


def fetch_messages(request):
    chat_id = request.GET.get('chat_id')
    first_name = request.GET.get('first_name')

    filename = f"{first_name}_{chat_id}.txt"
    file_path = os.path.join(BASE_DIR, filename)

    if not os.path.exists(file_path):
        logger.error(f"Chat file does not exist for {chat_id}")
        return JsonResponse({"error": "Chat file does not exist"}, status=404)

    messages = []
    files = []
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()

            if len(lines) % 2 != 0:
                return JsonResponse({"error": "Error reading file: file format is incorrect"}, status=400)

            for i in range(0, len(lines), 2):
                message_line = lines[i].strip().split(': ', 1)
                created_at_line = lines[i + 1].strip().split(': ', 1)

                if len(message_line) < 2 or len(created_at_line) < 2:
                    return JsonResponse({"error": "Error reading file: data format is incorrect"}, status=400)

                message_sender = message_line[0].lower()
                message_text = message_line[1]
                created_at_raw = created_at_line[1]

                try:
                    full_created_at = datetime.strptime(created_at_raw, '%Y-%m-%d %H:%M:%S.%f')
                    created_at_display = full_created_at.strftime('%Y-%m-%d %H:%M')
                except ValueError:
                    created_at_display = created_at_raw
                    full_created_at = None

                if message_text.startswith('/home/tuya/erixconsulting/media/'):
                    relative_path = message_text.replace('/home/tuya/erixconsulting/media/', '')
                    files.append({
                        "file_path": relative_path,
                        "created_at": created_at_display,
                        "full_created_at": created_at_raw
                    })
                else:
                    is_assistant = (message_sender == 'assistant')

                    messages.append({
                        "first_name": first_name if not is_assistant else 'Assistant',
                        "message_text": message_text,
                        "created_at": created_at_display,
                        "full_created_at": created_at_raw,
                        "is_assistant": is_assistant,
                    })
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        return JsonResponse({"error": f"Error reading file: {str(e)}"}, status=500)

    return JsonResponse({"messages": messages, "files": files})



def fetch_users(request):
    if request.user.is_authenticated and request.user.is_staff:
        users = TelegramUserMessage.objects.filter(staff=request.user)
    else:
        return JsonResponse({"users": []})

    user_list = [
        {
            "chat_id": user.chat_id,
            "first_name": user.first_name,
            "is_read": bool(user.is_read)
        }
        for user in users
    ]
    return JsonResponse({"users": user_list})


@csrf_exempt
def mark_messages_as_read(request):
    if request.method == 'POST':
        chat_id = request.POST.get('chat_id')
        first_name = request.POST.get('first_name')

        if chat_id and first_name:
            updated_count = TelegramUserMessage.objects.filter(chat_id=chat_id, first_name=first_name, is_read=False).update(is_read=True)
            return JsonResponse({'success': True, 'updated_count': updated_count})
        return JsonResponse({'success': False, 'error': 'Missing chat_id or first_name'}, status=400)

    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)


@csrf_exempt
def close_chat(request):
    if request.method == 'POST':
        if request.user.is_authenticated and request.user.is_staff:
            try:
                messages = TelegramUserMessage.objects.filter(staff=request.user, status='open')

                if messages.exists():
                    chat_id = request.POST.get('chat_id')
                    first_name = request.POST.get('first_name')

                    # Notify the customer about the closure
                    message = "Chat mutaxassis tomonidan yopildi iltimos qayta ariza qoldirish uchun /start tugmasini bosing"
                    notify_customer(chat_id, message)

                    request_user = ChatRequest.objects.filter(chat_id=chat_id).first()

                    if not request_user:
                        return JsonResponse({'success': False, 'error': 'Chat request not found.'}, status=404)

                    filename = f'{first_name}_{chat_id}.txt'
                    file_path = os.path.join(BASE_DIR, filename)
                    if os.path.exists(file_path):
                        os.remove(file_path)

                    user_directory = os.path.join(BASE_DIR, f'{first_name}_{chat_id}')
                    if os.path.exists(user_directory):
                        shutil.rmtree(user_directory)

                    RequestHistory.objects.create(
                        chat_id=chat_id,
                        first_name=request_user.first_name,
                        username=request_user.username,
                        reason=request_user.reason,
                        staff_id=request.user.id,
                        created_at=request_user.created_at,
                        closed_at=timezone.now(),
                    )

                    TelegramUserMessage.objects.filter(chat_id=chat_id).delete()
                    ChatRequest.objects.filter(chat_id=chat_id).delete()

                    return JsonResponse({'success': True}, status=200)
                else:
                    return JsonResponse({'success': False, 'error': 'No open messages found for the current staff.'}, status=404)

            except Exception as e:
                logger.error(f"Error occurred while closing the chat: {str(e)}")
                return JsonResponse({'success': False, 'error': str(e)}, status=500)

        return JsonResponse({'success': False, 'error': 'User not authenticated or not staff'}, status=403)

    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)
