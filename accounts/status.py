from django.http import JsonResponse

from accounts.models import TelegramUserMessage, ChatRequest


def check_chat_status(request):
    chat_id = request.GET.get('chat_id')

    if chat_id:
        # Check if the chat_id exists in TelegramUserMessage (open)
        telegram_message = TelegramUserMessage.objects.filter(chat_id=chat_id).first()

        if telegram_message:
            return JsonResponse({"status": "open"})  # Chat is currently open

        # Check if the chat_id exists in ChatRequest with status 'open' (waiting)
        chat_request = ChatRequest.objects.filter(chat_id=chat_id, status='open').first()

        if chat_request:
            return JsonResponse({"status": "waiting"})  # Chat is waiting to be assigned or processed

    # If the chat_id is not found in TelegramUserMessage or ChatRequest, it's closed
    return JsonResponse({"status": "closed"})
