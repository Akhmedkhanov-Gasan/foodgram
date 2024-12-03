from django.contrib import admin

from .models import Subscription, UserProfile

admin.site.register(Subscription)
admin.site.register(UserProfile)
