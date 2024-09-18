import os
from pyexpat.errors import messages
from tempfile import template
from traceback import print_tb

import requests
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views import View

from .models import CharAi
from erixconsulting import settings


class ChatWithBotView(View):
    template_name = 'test.html'

    def get(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
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

        print("Chat history:", chat_history)  # Debugging line
        return render(request, self.template_name, {'chat_history': chat_history})

    def post(self, request, *args, **kwargs):
        user_message = request.POST.get('message')
        user = request.user
        chat_files_dir = os.path.join(settings.MEDIA_ROOT, 'chat_files')

        # Ensure the chat_files directory exists
        if not os.path.exists(chat_files_dir):
            os.makedirs(chat_files_dir)

        if user.is_authenticated:
            # Handle authenticated user
            file_name = f"{user.id}.txt"
            file_path = os.path.join(chat_files_dir, file_name)

            # Save the user's message to the chat history
            with open(file_path, 'a') as file:
                file.write(f"User: {user_message}\n")

            # Save the chat entry in the database
            chat_entry = CharAi(user=user, text_file_url=file_path)
            chat_entry.save()

        rasa_url = "http://localhost:5005/webhooks/rest/webhook"
        payload = {"sender": "user123", "message": user_message}

        try:
            response = requests.post(rasa_url, json=payload)
            response.raise_for_status()
            messages = [msg['text'] for msg in response.json()]
        except requests.RequestException as e:
            print(f"Error communicating with Rasa: {e}")
            messages = ["Sorry, there was an error processing your request."]

        # Save the bot's response to the chat history if the user is authenticated
        if user.is_authenticated:
            with open(file_path, 'a') as file:
                for msg in messages:
                    file.write(f"Bot: {msg}\n")

        return JsonResponse({'messages': [{'text': msg} for msg in messages]})