import asyncio
import base64
import json
from datetime import datetime
import os

from aiogram import Bot
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
from django.http import JsonResponse
from accounts.models import TelegramUserMessage, ChatRequest, RequestHistory, ChatFile
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
import logging
from config import API_TOKEN

User = get_user_model()
bot = Bot(token=API_TOKEN)

@csrf_exempt
def save_message(request):
    if request.method == 'POST':
        # Load JSON data from the request body
        data = json.loads(request.body)

        first_name = data.get('first_name')
        username = data.get('username')
        message = data.get('message')  # This can be text or None if a file is sent
        chat_id = data.get('chat_id')
        reason = data.get('reason')
        file = data.get('file_path')  # Expecting a file field if one is sent

        logging.info(f'Received data: {first_name}, {username}, {message}, {chat_id}, {file}')

        if not all([first_name, username, chat_id, reason]) or (not message and not file):
            logging.error('Invalid data received')
            return JsonResponse({'status': 'error', 'message': 'Invalid data'}, status=400)

        # Save message to file
        filename = f'{first_name}_{chat_id}.txt'
        file_path = os.path.join('media/messages', filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Save the text message if provided
        if message:
            with open(file_path, 'a') as file_handle:
                file_handle.write(f'customer: {message}\ncreated_at: {datetime.now()}\n')

        # Check if a file is being sent
        if file:
            # Append file information to the same text file
            with open(file_path, 'a') as file_handle:
                file_handle.write(f'file: {file}\ncreated_at: {datetime.now()}\n')

        # Update message read status
        TelegramUserMessage.objects.filter(chat_id=chat_id, is_read=True).update(is_read=False)

        # Check if there's an existing request
        existing_request = ChatRequest.objects.filter(chat_id=chat_id).first()

        if not existing_request:
            ChatRequest.objects.create(
                first_name=first_name,
                username="@" + username,
                chat_id=chat_id,
                reason=reason,
                status='open'
            )
            status = 'new_request'
        else:
            status = 'existing_request'

        return JsonResponse({'status': status, 'message': 'Chat request processed.'})

    return JsonResponse({'status': 'invalid method'}, status=405)


@user_passes_test(lambda u: u.is_superuser, login_url='/home')
def request_page(request):
    requests = ChatRequest.objects.filter(status__in=['open', 'assigned'])
    staff_members = User.objects.filter(is_staff=True)
    request_history = RequestHistory.objects.all()

    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        staff_id = request.POST.get('staff_id')

        if request_id and staff_id:
            try:
                chat_request = ChatRequest.objects.get(id=request_id)
                staff_member = User.objects.get(id=staff_id)

                # Assign staff to chat request
                chat_request.staff_id = staff_member  # Update to 'staff' from 'staff_id'
                chat_request.status = 'assigned'
                chat_request.save()

                # Notify customer of the assignment
                message = f"You have been connected to assistant {staff_member.first_name} {staff_member.last_name}."
                asyncio.run(notify_customer(chat_request.chat_id, message))

                filename = f'{chat_request.first_name}_{chat_request.chat_id}.txt'
                file_path = os.path.join('media/messages', filename)

                # Move the request to TelegramUserMessage
                TelegramUserMessage.objects.create(
                    first_name=chat_request.first_name,
                    username=chat_request.username,
                    chat_id=chat_request.chat_id,
                    message_file=file_path,
                    staff=staff_member,
                    status='open'
                )

                return JsonResponse(
                    {'status': 'success', 'assigned_to': f'{staff_member.first_name} {staff_member.last_name}'})

            except ChatRequest.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Chat request not found.'}, status=404)

            except User.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Staff member not found.'}, status=404)

    return render(request, 'requests.html', {'requests': requests, 'staff_members': staff_members, 'request_history': request_history})


async def notify_customer(chat_id, message):
    """Send notification message to the customer"""
    try:
        await bot.send_message(chat_id, message)
    except Exception as e:
        logging.error(f"Error sending notification to customer: {e}")



