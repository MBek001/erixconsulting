from django.shortcuts import render


def request_messages(request):
    return render(request, 'requests.html')