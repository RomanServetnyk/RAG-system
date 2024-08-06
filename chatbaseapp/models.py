from django.db import models
from datetime import datetime
import os
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    customer_id = models.CharField(default='', max_length=50)

# Create your models here.
# def facility_path(instance, filename):
#     return f'attachments/employee/emp{instance.employee.id}/emp{instance.employee.id}.pdf'

class Document(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    def upload_path(self, filename):
        now = datetime.now().strftime('_%Y_%m_%d_%H_%M_%S_%f')
        return f'{self.user.id}/{os.path.splitext(filename)[0] + now + ".pdf"}'
    file = models.FileField(upload_to=upload_path)
    name = models.CharField(default="", max_length=100)
    size = models.CharField(default="", max_length=10)
    deleted = models.BooleanField(default=False)
    need_ocr = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=datetime.now)

class Billing(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product_id = models.CharField(max_length=50, default="")
    status = models.CharField(max_length=50, default='paid') # 'paid', 'disputed'
    payment_intent_id = models.CharField(max_length=50, default="")
    created_at = models.DateTimeField(default=datetime.now)

class Product(models.Model):
    product_id = models.CharField(max_length=50, default="")
    name = models.CharField(max_length=100, default='')
    level = models.IntegerField(default=1)
    plan = models.CharField(max_length=50, default='monthly')
    duration = models.IntegerField(default = 1)
    created_at = models.DateTimeField(default=datetime.now)

class Chat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=datetime.now)

    
class Verification(models.Model):
    email = models.CharField(max_length=50, default="")
    password = models.CharField(max_length=100, default="")
    count = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)