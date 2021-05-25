from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class User(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, primary_key=True)
    password = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name}"

    def serialize(self):
        return {
            'name' : self.name,
            'email' : self.email
        }

