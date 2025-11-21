import os
import logging
from datetime import datetime
from django.http import JsonResponse
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
from accounts.models import TelegramUserMessage, RequestHistory
from config import Admin_Dir

logger = logging.getLogger(__name__)


@user_passes_test(lambda u: u.is_superuser, login_url='/login/')
def chat_page(request):
    messages = []
    # Fetch distinct users for the logged-in staff
    users = TelegramUserMessage.objects.filter(staff=request.user).values('first_name', 'chat_id').distinct()
    staff_messages = TelegramUserMessage.objects.filter(staff=request.user)

    for chat in staff_messages:
        file_path = os.path.join(CONVERSATIONS_DIR, chat.message_file.name)
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

    # Sort messages by creation time, descending
    messages = sorted(messages, key=lambda x: (x['created_at'] is None, x['created_at']), reverse=True)

    return render(request, 'chat_history.html', {'messages': messages, 'users': users})


def fetch_messages_history(request):
    chat_id = request.GET.get('chat_id')
    first_name = request.GET.get('first_name')

    filename = f"{first_name}_{chat_id}.txt"
    file_path = os.path.join(CONVERSATIONS_DIR, filename)

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
                    print('aaaaaaaaaa', message_sender)
                else:
                    is_customer = (message_sender == 'customer')
                    if is_customer:
                        sender_name = first_name
                    else:
                        sender_name = message_sender
                    messages.append({
                        "first_name": sender_name,
                        "message_text": message_text,
                        "created_at": created_at_display,
                        "full_created_at": created_at_raw,
                        "is_assistant": is_customer,
                    })
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        return JsonResponse({"error": f"Error reading file: {str(e)}"}, status=500)

    return JsonResponse({"messages": messages, "files": files})


def fetch_users_history(request):
    if request.user.is_authenticated and request.user.is_staff:
        users = RequestHistory.objects.filter(staff=request.user).values('chat_id', 'username', 'first_name').distinct()
    else:
        return JsonResponse({"users": []})

    user_list = [
        {
            "username": user['username'],
            "chat_id": user['chat_id'],
            "first_name": user['first_name'],
        }
        for user in users
    ]

    return JsonResponse({"users": user_list})
