import json
import datetime
from datetime import datetime, timedelta
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
from django.http import JsonResponse, HttpResponseRedirect
from django.utils.timezone import now
from accounts.message_sending import *
from accounts.models import TelegramUserMessage, ChatRequest, RequestHistory
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
import logging
from accounts.message_sending import BOT_TOKEN
load_dotenv()


User = get_user_model()
bot = Bot(token=BOT_TOKEN)
BASE_DIR = Base_Dir


@csrf_exempt
def save_message(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        first_name = data.get('first_name')
        username = data.get('username')
        message = data.get('message')
        chat_id = data.get('chat_id')
        reason = data.get('reason')
        file = data.get('file_path')

        logging.info(f'Received data: {first_name}, {username}, {message}, {chat_id}, {file}')

        chat_request = ChatRequest.objects.filter(chat_id=chat_id).first()
        telegramuser = TelegramUserMessage.objects.filter(chat_id=chat_id).first()

        if not chat_request and telegramuser:
            if not all([first_name, username, chat_id, reason]) or (not message and not file):
                logging.error('Invalid data received')
                return JsonResponse({'status': 'error', 'message': 'Invalid data'}, status=400)

        if not all([first_name, username, chat_id]) or (not message and not file):
            logging.error('Invalid data received')
            return JsonResponse({'status': 'error', 'message': 'Invalid data'}, status=400)

        filename = f'{first_name}_{chat_id}.txt'
        file_path = os.path.join(BASE_DIR, filename)
        admin_path = os.path.join(Admin_Dir,filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        os.makedirs(os.path.dirname(admin_path), exist_ok=True)

        if message:
            with open(file_path, 'a') as file_handle:
                file_handle.write(f'customer: {message}\n created_at: {datetime.utcnow() + timedelta(hours=5)}\n')
            with open(admin_path, 'a') as file_hand:
                file_hand.write(f'customer: {message}\n created_at: {datetime.utcnow() + timedelta(hours=5)}\n')
        if file:
            with open(file_path, 'a') as file_handle:
                file_handle.write(f'file: {file}\n created_at: {datetime.now() + timedelta(hours=5)}\n')

        TelegramUserMessage.objects.filter(chat_id=chat_id, is_read=True).update(is_read=False)
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


@user_passes_test(lambda u: u.is_superuser, login_url='/login')
def request_page(request):
    requests = ChatRequest.objects.filter(status__in=['open', 'assigned'])
    staff_members = User.objects.filter(is_staff=True)
    request_history = RequestHistory.objects.all()

    three_days_ago = now() - timedelta(days=3)
    delayed_requests = TelegramUserMessage.objects.filter(created_at__lt=three_days_ago, status='open')

    if request.method == 'POST' and 'send_to_channel' in request.POST:
        delayed_request_id = request.POST.get('delayed_request_id')
        if delayed_request_id:
            delayed_request = TelegramUserMessage.objects.filter(id=delayed_request_id).first()

            if delayed_request:
                chat_request = ChatRequest.objects.filter(chat_id=delayed_request.chat_id).first()
                staff_member = delayed_request.staff

                if chat_request and staff_member:
                    channel_message = (
                        f"#DelayedRequest\n"
                        f"Customer: {chat_request.first_name} \n"
                        f"Assigned to: {staff_member.first_name} {staff_member.last_name}\n"
                        f"Created at: {delayed_request.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    send_info_to_channel(channel_message)
                    messages.success(request, 'Message has been sent successfully.')
                return HttpResponseRedirect(request.path_info)
            return JsonResponse({'status': 'error', 'message': 'Delayed request not found.'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No delayed request ID provided.'})

    if request.method == 'POST' and 'request_id' in request.POST and 'staff_id' in request.POST:
        request_id = request.POST.get('request_id')
        staff_id = request.POST.get('staff_id')

        if request_id and staff_id:
            try:
                chat_request = ChatRequest.objects.get(id=request_id)
                staff_member = User.objects.get(id=staff_id)
                chat_request.staff_id = staff_member
                chat_request.status = 'assigned'
                chat_request.save()

                message = f"Sizga {staff_member.first_name} {staff_member.last_name} ulandi murojat qilishingiz mumkin."
                notify_customer(chat_request.chat_id, message)

                filename = f'{chat_request.first_name}_{chat_request.chat_id}.txt'
                file_path = os.path.join(BASE_DIR, filename)

                TelegramUserMessage.objects.create(
                    first_name=chat_request.first_name,
                    username=chat_request.username,
                    chat_id=chat_request.chat_id,
                    message_file=file_path,
                    staff=staff_member,
                    status='open'
                )

                channel_message2 = (
                    f"#NewAssignment\n"
                    f"Customer: {chat_request.first_name} \n"
                    f"Assigned to: {staff_member.first_name} {staff_member.last_name}\n"
                    f"Please do not forget to contact your customer!"
                )
                send_info_to_channel(channel_message2)

                return JsonResponse(
                    {'status': 'success', 'assigned_to': f'{staff_member.first_name} {staff_member.last_name}'}
                )
            except ChatRequest.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Chat request not found.'}, status=404)
            except User.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Staff member not found.'}, status=404)

    return render(request, 'requests.html', {
        'requests': requests,
        'staff_members': staff_members,
        'request_history': request_history,
        'delayed_requests': delayed_requests
    })
