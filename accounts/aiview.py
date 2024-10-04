from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views import View
import os
import openai

from ERRORS import send_error_to_telegram
from erixconsulting import settings
from .models import CharAi

import logging

API_KEY = os.getenv("API_KEY")

class ChatWithBotView(View):

    def get(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            messages.error(request, "User not authenticated")
            return HttpResponse("User not authenticated", status=401)

        chat_files_dir = os.path.join(settings.MEDIA_ROOT, 'chat_files')
        file_name = f"{user.id}.txt"
        file_path = os.path.join(chat_files_dir, file_name)

        chat_history = []
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
        """Handles sending messages to the bot and returning its response."""
        user_message = request.POST.get('message')
        user = request.user
        chat_files_dir = os.path.join(settings.MEDIA_ROOT, 'chat_files')

        # Check if the user is authenticated
        if not user.is_authenticated:
            # Return an error message to the frontend instead of AI response
            bot_response = "You must log in or register to use the chatbot."
            return JsonResponse({'messages': [{'text': bot_response, 'sender': 'bot'}]}, status=401)

        # Ensure the chat_files directory exists
        if not os.path.exists(chat_files_dir):
            os.makedirs(chat_files_dir)

        # Saving user's message in txt file
        file_name = f"{user.id}.txt"
        file_path = os.path.join(chat_files_dir, file_name)

        with open(file_path, 'a') as file:
            file.write(f"User: {user_message}\n")

        # Saving file in database
        chat_entry = CharAi(user=user, text_file_url=file_path)
        chat_entry.save()

        openai.api_key = API_KEY

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    # System message with restricted consulting topics
                    {"role": "system", "content": (
                        "You are a legal consultant AI, specializing in law consulting, "
                        "society consulting, and juridical consulting. "
                        "You must respond only to legal queries or related topics, "
                        "and avoid any responses outside the domain of legal consulting."
                    )},
                    {"role": "user", "content": user_message},
                ]
            )

            bot_response = response['choices'][0]['message']['content']

        except Exception as e:
            error_message = f"Error communicating with OpenAI: {str(e)}"
            logging.error(error_message)  # Log the error
            send_error_to_telegram(error_message)  # Send the error to Telegram
            bot_response = "Sorry, there was an error processing your request."

        # Saving bot's response in the same file
        with open(file_path, 'a') as file:
            file.write(f"Bot: {bot_response}\n")

        return JsonResponse({'messages': [{'text': bot_response, 'sender': 'bot'}]})
