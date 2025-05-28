from contactus_app.models import Footer, Ticket
from projects_app.models import Project
from . import urls
from django.http import HttpResponse, Http404
from django.shortcuts import render


def home(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        email = request.POST.get('email')
        if name and subject and message and email:
            Ticket.objects.create(name=name, subject=subject, email=email, message=message)
    footer = Footer.objects.all().last()
    projects = Project.objects.all()
    return render(request, 'index.html', {'footer': footer , 'projects':projects})
