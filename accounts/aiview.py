import os
from django.conf import settings
from django.http import JsonResponse
import openai
import logging
from django.views import View
from ERRORS import send_error_to_telegram
from accounts.models import CharAi

API_KEY = 'sk...'


class ChatWithBotView(View):

    def get_chat_file_path(self, user):
        chat_files_dir = os.path.join(settings.MEDIA_ROOT, 'chat_files')
        if not os.path.exists(chat_files_dir):
            os.makedirs(chat_files_dir)

        if user.is_authenticated:
            file_name = f"{user.id}.txt"
        else:
            session_id = self.request.session.session_key or self.request.session.create()
            file_name = f"anonymous_{session_id}.txt"

        return os.path.join(chat_files_dir, file_name)

    def get(self, request, *args, **kwargs):
        chat_history = []
        file_path = self.get_chat_file_path(request.user)

        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                lines = file.readlines()
                for line in lines:
                    if line.startswith("User:"):
                        chat_history.append({'sender': 'user', 'text': line[len("User: "):].strip()})
                    elif line.startswith("Bot:"):
                        chat_history.append({'sender': 'bot', 'text': line[len("Bot: "):].strip()})

        return JsonResponse({'chat_history': chat_history})

    def post(self, request, *args, **kwargs):
        user_message = request.POST.get('message')
        user = request.user
        file_path = self.get_chat_file_path(user)

        with open(file_path, 'a') as file:
            file.write(f"User: {user_message}\n")

        if user.is_authenticated:
            chat_entry = CharAi(user=user, text_file_url=file_path)
            chat_entry.save()

        openai.api_key = API_KEY

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": (
                       "You are a legal consultant AI, specializing in providing advice on legal matters, "
                        "societal regulations, and judicial processes. "
                        "You offer expert guidance on areas such as civil, criminal, corporate, and international law, "
                        "and help users navigate legal frameworks, contracts, dispute resolutions, compliance issues, and rights protection. "
                        "Your responses must be relevant to legal concepts and related societal topics, "
                        "providing users with accurate legal insights. "
                        "You were developed by Cognilabs Company."
                    )},
                    {"role": "user", "content": user_message},
                ]
            )
            bot_response = response['choices'][0]['message']['content']
        except Exception as e:
            error_message = f"Error communicating with OpenAI: {str(e)}"
            logging.error(error_message)
            send_error_to_telegram(error_message)
            bot_response = "Sorry, there was an error processing your request."

        # Save bot's response to the chat file
        with open(file_path, 'a') as file:
            file.write(f"Bot: {bot_response}\n")

        return JsonResponse({'messages': [{'text': bot_response, 'sender': 'bot'}]})
