from pyexpat.errors import messages
from django.http import JsonResponse
from accounts.models import TelegramUserMessage, ChatRequest, RequestHistory

def check_chat_status(request):
    chat_id = request.GET.get('chat_id')
    if chat_id:
        telegram_message = TelegramUserMessage.objects.filter(chat_id=chat_id).first()
        request_chat = ChatRequest.objects.filter(chat_id=chat_id).first()
        chat_history = RequestHistory.objects.filter(chat_id=chat_id).first()

        if telegram_message:
            return JsonResponse({"status": "open"})

        if request_chat:
            return JsonResponse({"status": "waiting"})

        if not request_chat and not telegram_message:
            if chat_history:
                return JsonResponse({"status": "closed"})
            else:
                return JsonResponse({"status": "new"})

        if not request_chat and telegram_message:
            if not chat_history:
                return JsonResponse({"status": "new"})

    return JsonResponse({"status": "error", "message": "Chat ID is None"}, status=400)

