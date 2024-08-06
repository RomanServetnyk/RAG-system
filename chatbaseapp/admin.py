from django.contrib import admin
from .models import (Document, User, Billing, Product, Chat, Verification)

# Register your models here.
admin.site.register(Document)
admin.site.register(User)
admin.site.register(Billing)
admin.site.register(Product)
admin.site.register(Chat)
admin.site.register(Verification)
