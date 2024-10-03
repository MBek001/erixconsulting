import json
import os
import logging
from datetime import datetime

import requests

from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

from erixconsulting import settings
from .models import TelegramUserMessage

TELEGRAM_API_URL = f"https://api.telegram.org/bot7334080838:AAECrnJlcDbhrdWVmSAK85VVre2z1fV-6p4/sendMessage"
CHAT_ID = '497640654'

# Set up logging
logger = logging.getLogger(__name__)


@csrf_exempt
def save_message(request):
    """
    Handles messages received from Telegram and saves them as 'customer' in a text file.
    """
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        message = request.POST.get('message')
        chat_id = request.POST.get('chat_id')

        if first_name and message and chat_id:
            # Check if the chat ID already exists to prevent duplicate files
            message_instance, created = TelegramUserMessage.objects.get_or_create(
                first_name=first_name,
                chat_id=chat_id,
                defaults={'username': first_name, 'message_file': None}
            )

            # If the message instance is new, create a new file
            if not message_instance.message_file:
                filename = f'{first_name}_{chat_id}.txt'
                file_path = os.path.join('media/messages', filename)
                message_instance.message_file.name = f'messages/{filename}'
                message_instance.save()

            # Append the new message to the file with 'customer' label
            file_path = os.path.join('media', message_instance.message_file.name)
            with open(file_path, 'a') as file:
                file.write(f'customer: {message}\ncreated_at: {datetime.now()}\n')

            return JsonResponse({'status': 'success', 'file_url': message_instance.message_file.url}, status=200)
        return JsonResponse({'status': 'error', 'message': 'Invalid data'}, status=400)
    return JsonResponse({'status': 'invalid method'}, status=405)


@user_passes_test(lambda u: u.is_staff, login_url='/login/')
def chat_page(request):
    messages = []
    users = TelegramUserMessage.objects.values('first_name', 'chat_id').distinct()

    # Fetch all messages from the database
    for chat in TelegramUserMessage.objects.all():
        file_path = os.path.join(settings.MEDIA_ROOT, chat.message_file.name)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as file:
                    content = file.read()
                    messages.append({
                        'chat_id': chat.chat_id,
                        'first_name': chat.first_name,
                        'message': content,
                        'created_at': chat.created_at
                    })
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

    messages = sorted(messages, key=lambda x: x['created_at'], reverse=True)

    return render(request, 'chat_page.html', {'messages': messages, 'users': users})


@csrf_exempt
def send_message_to_bot(request):
    """
    Sends a message to the Telegram bot and saves it to the corresponding chat file as 'assistant'.
    """
    if request.method == 'POST':
        message = request.POST.get('message')
        chat_id = request.POST.get('chat_id')  # Get the chat ID from the request
        first_name = request.POST.get('first_name')  # Get the first name from the request

        if message and chat_id and first_name:
            # Prepare the data to be sent to the bot
            payload = {
                'chat_id': chat_id,  # Use the chat ID from the request
                'text': message,
            }

            logger.debug(f"Sending message to Telegram: {payload}")  # Log the payload

            try:
                # Send the message to the bot
                response = requests.post(TELEGRAM_API_URL, json=payload)
                logger.debug(f"Telegram response status code: {response.status_code}")  # Log status code
                logger.debug(f"Telegram response text: {response.text}")  # Log response text

                # Check if the response from Telegram is successful
                if response.status_code == 200:
                    response_data = response.json()
                    if response_data.get('ok'):
                        # Save the message to the file with the 'assistant' label
                        filename = f'{first_name}_{chat_id}.txt'
                        file_path = os.path.join('media/messages', filename)

                        # Create the 'messages' directory if it doesn't exist
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)

                        # Append the assistant message to the file
                        with open(file_path, 'a') as file:
                            file.write(f'assistant: {message}\ncreated_at: {datetime.now()}\n')

                        logger.info(f"Message saved to file: {file_path}")
                        return JsonResponse({'status': 'success'}, status=200)
                    else:
                        error_message = response_data.get('description', 'Unknown error')
                        logger.error(f"Telegram API error: {error_message}")
                        return JsonResponse({'status': 'error', 'message': error_message}, status=500)
                else:
                    logger.error(f"Failed to send message to Telegram bot: {response.text}")
                    return JsonResponse({'status': 'error', 'message': 'Failed to send message to bot'}, status=500)
            except Exception as e:
                logger.error(f"Exception occurred while sending message: {str(e)}")
                return JsonResponse({'status': 'error', 'message': 'An error occurred while sending the message.'},
                                    status=500)
        else:
            logger.warning("No message, chat ID, or first name provided.")
            return JsonResponse({'status': 'error', 'message': 'No message, chat ID, or first name provided'},
                                status=400)

    return JsonResponse({'status': 'invalid method'}, status=405)



def fetch_messages(request):
    chat_id = request.GET.get('chat_id')
    first_name = request.GET.get('first_name')

    # Define the file path based on first_name and chat_id
    filename = f"{first_name}_{chat_id}.txt"
    file_path = os.path.join('media/messages', filename)

    # Check if the file exists
    if not os.path.exists(file_path):
        return JsonResponse({"error": "Chat file does not exist"}, status=404)

    messages = []
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()

            # Ensure there are an even number of lines (message and created_at)
            if len(lines) % 2 != 0:
                return JsonResponse({"error": "Error reading file: file format is incorrect"}, status=400)

            for i in range(0, len(lines), 2):
                message_line = lines[i].strip().split(': ', 1)
                created_at_line = lines[i + 1].strip().split(': ', 1)

                if len(message_line) < 2 or len(created_at_line) < 2:
                    return JsonResponse({"error": "Error reading file: data format is incorrect"}, status=400)

                message_sender = message_line[0].lower()  # Either 'customer' or 'assistant'
                message_text = message_line[1]  # Get message text
                created_at_raw = created_at_line[1]  # Get the raw created_at timestamp

                # Format the created_at timestamp (YYYY-MM-DD HH:MM)
                try:
                    created_at = datetime.strptime(created_at_raw, '%Y-%m-%d %H:%M:%S.%f').strftime('%Y-%m-%d %H:%M')
                except ValueError:
                    # Fallback in case the format is different
                    created_at = created_at_raw

                # Identify if the message is from the assistant or the customer
                is_assistant = (message_sender == 'assistant')

                # Append the parsed message to the list
                messages.append({
                    "first_name": first_name if not is_assistant else 'Assistant',  # Display the correct name
                    "message_text": message_text,
                    "created_at": created_at,  # Formatted timestamp
                    "is_assistant": is_assistant  # Boolean flag to identify sender
                })
    except Exception as e:
        return JsonResponse({"error": f"Error reading file: {str(e)}"}, status=500)

    return JsonResponse({"messages": messages})


def fetch_users(request):
    users = TelegramUserMessage.objects.all()
    user_list = [{"chat_id": user.chat_id, "first_name": user.first_name} for user in users]
    return JsonResponse({"users": user_list})

