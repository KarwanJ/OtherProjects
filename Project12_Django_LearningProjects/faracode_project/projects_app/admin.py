from django.contrib import admin
from . import models
from .models import Project

# Register your models here.
admin.site.register(Project)