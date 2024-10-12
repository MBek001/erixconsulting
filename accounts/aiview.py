from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views import View
import os
import openai
from ERRORS import send_error_to_telegram
from erixconsulting import settings
from accounts.models import CharAi

import logging

API_KEY = os.getenv("API_KEY")

class ChatWithBotView(View):

    def get_chat_file_path(self, user):
        """Helper function to determine file path for chat history."""
        chat_files_dir = os.path.join(settings.MEDIA_ROOT, 'chat_files')
        if not os.path.exists(chat_files_dir):
            os.makedirs(chat_files_dir)

        if user.is_authenticated:
            file_name = f"{user.id}.txt"
        else:
            # Use session ID or some other unique identifier for unauthenticated users
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

        # Save user's message in the text file
        with open(file_path, 'a') as file:
            file.write(f"User: {user_message}\n")
        # Saving file in the database (for authenticated users)
        if user.is_authenticated:
            chat_entry = CharAi(user=user, text_file_url=file_path)
            chat_entry.save()

        openai.api_key = API_KEY

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": (
                        "You are a legal consultant AI, specializing in law consulting, "
                        "society consulting, and juridical consulting. "
                        "You must respond only to legal queries or related topics, "
                        "and avoid any responses outside the domain of legal consulting."
                        "You have created by Developers of Cognilabs Company"
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
        # Save bot's response in the text file
        with open(file_path, 'a') as file:
            file.write(f"Bot: {bot_response}\n")

        return JsonResponse({'messages': [{'text': bot_response, 'sender': 'bot'}]})
