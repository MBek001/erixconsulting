# import asyncio
# import json
# from datetime import datetime
# import os
#
# from aiogram import Bot
# from django.contrib.auth.decorators import user_passes_test
# from django.shortcuts import render
# from django.http import JsonResponse
# from erixconsulting import settings
# from main import notify_customer
# from .models import TelegramUserMessage, ChatRequest
# from django.contrib.auth import get_user_model
# from django.views.decorators.csrf import csrf_exempt
# import logging
# from config import API_TOKEN
# User = get_user_model()
#
# bot = Bot(token=API_TOKEN)
#
# @csrf_exempt
# def save_message(request):
#     if request.method == 'POST':
#         # Load JSON data from the request body
#         data = json.loads(request.body)
#
#         first_name = data.get('first_name')
#         username = data.get('username')
#         message = data.get('message')
#         chat_id = data.get('chat_id')
#         reason = data.get('reason')
#         print('reason',reason)
#         print('message',message)
#         print('chat_id',chat_id)
#         print('username',username)
#
#         # Log incoming data
#         logging.info(f'Received data: {first_name}, {username}, {message}, {chat_id}')
#
#         # Validate input data
#         if not all([first_name, username, message, chat_id,reason]):
#             logging.error('Invalid data received')
#             return JsonResponse({'status': 'error', 'message': 'Invalid data'}, status=400)
#
#         # Always save the message to a text file
#         filename = f'{first_name}_{chat_id}.txt'
#         file_path = os.path.join('media/messages', filename)
#         os.makedirs(os.path.dirname(file_path), exist_ok=True)
#
#         with open(file_path, 'a') as file:
#             file.write(f'customer: {message}\ncreated_at: {datetime.now()}\n')
#
#         # Mark all previous messages for this chat_id as read
#         TelegramUserMessage.objects.filter(chat_id=chat_id, is_read=True).update(is_read=False)
#
#         # Check for any existing request for this customer
#         existing_request = ChatRequest.objects.filter(chat_id=chat_id).first()
#
#         # If there is no existing request or the existing request is closed, create a new one
#         if existing_request is None or existing_request.status == 'closed':
#             ChatRequest.objects.create(
#                 first_name=first_name,
#                 username="@" + username,
#                 chat_id=chat_id,
#                 reason=reason,
#                 status='open'
#             )
#             status = 'new_request'
#         else:
#             status = 'existing_request'
#
#         return JsonResponse({'status': status, 'message': 'Chat request processed.'})
#
#     logging.error('Invalid method')
#     return JsonResponse({'status': 'invalid method'}, status=405)
#
#
# @user_passes_test(lambda u: u.is_superuser, login_url='/home')
# def request_page(request):
#     # Get all requests for admin, both open and closed
#     requests = ChatRequest.objects.all()
#     staff_members = User.objects.filter(is_staff=True)
#
#     if request.method == 'POST':
#         # Assign chat request to staff
#         request_id = request.POST.get('request_id')
#         staff_id = request.POST.get('staff_id')
#
#         if request_id and staff_id:
#             try:
#                 chat_request = ChatRequest.objects.get(id=request_id)
#                 staff_member = User.objects.get(id=staff_id)
#
#                 # Assign staff to the chat request
#                 chat_request.staff_id = staff_member
#                 chat_request.status = 'assigned'
#                 chat_request.save()
#
#                 message = f"You have been connected to assistant {staff_member.first_name} {staff_member.last_name}."
#                 asyncio.run(notify_customer(chat_request.chat_id, message))
#
#                 # Create the file path based on the assigned chat request
#                 filename = f'{chat_request.first_name}_{chat_request.chat_id}.txt'
#                 file_path = os.path.join('media/messages', filename)
#
#                 # Move request to TelegramUserMessage
#                 TelegramUserMessage.objects.create(
#                     first_name=chat_request.first_name,
#                     username=chat_request.username,
#                     chat_id=chat_request.chat_id,
#                     message_file=file_path,
#                     staff=staff_member,
#                     status='open'
#                 )
#
#                 return JsonResponse({'status': 'success', 'assigned_to': f'{staff_member.first_name} {staff_member.last_name}'})
#
#             except ChatRequest.DoesNotExist:
#                 logging.error(f'ChatRequest with id {request_id} does not exist.')
#                 return JsonResponse({'status': 'error', 'message': 'Chat request not found.'}, status=404)
#
#             except User.DoesNotExist:
#                 logging.error(f'User with id {staff_id} does not exist.')
#                 return JsonResponse({'status': 'error', 'message': 'Staff member not found.'}, status=404)
#
#     return render(request, 'requests.html', {'requests': requests, 'staff_members': staff_members, 'active_page': 'chat2'})
#
#
#
# @csrf_exempt
# def notify_bot(request):
#     if request.method == "POST":
#         chat_id = request.POST.get("chat_id")
#         message = request.POST.get("message")
#
#         if chat_id and message:
#             # Send message to the customer using Telegram
#             asyncio.run(bot.send_message(chat_id=chat_id, text=message))
#             return JsonResponse({"status": "success", "message": "Notification sent."})
#
#         return JsonResponse({"status": "error", "message": "Chat ID and message are required."})
#     return JsonResponse({"status": "error", "message": "Only POST requests are allowed."})
#
#
# def check_chat_status(request):
#     chat_id = request.GET.get('chat_id')
#     if chat_id:
#         chat_request = ChatRequest.objects.filter(chat_id=chat_id).first()
#         if chat_request:
#             return JsonResponse({"status": chat_request.status})
#     return JsonResponse({"status": "closed"})
#
