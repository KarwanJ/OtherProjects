from django.db import models


class Footer(models.Model):
    address = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    phone = models.CharField(max_length=50)
    email = models.EmailField()
    whatsapp = models.CharField(max_length=50)
    telegram = models.CharField(max_length=50)
    instagram = models.CharField(max_length=50)
    def __str__(self):
        return self.email

# Create your models here.
class Ticket(models.Model):
    name = models.CharField(max_length=50)
    subject = models.CharField(max_length=100)
    message = models.TextField()
    email = models.EmailField()
    def __str__(self):
        return self.subject

