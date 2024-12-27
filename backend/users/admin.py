from django.contrib import admin

from .models import Subscription, User


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Admin panel for managing subscriptions."""

    list_display = ('user', 'author')
    search_fields = (
        'user__username',
        'author__username',
        'user__email',
        'author__email'
    )
    list_filter = ('user__username', 'author__username')

    def user(self, obj):
        return obj.user.username

    def author(self, obj):
        return obj.author.username


@admin.register(User)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin panel for managing user profiles."""

    list_display = ('username', 'email', 'first_name', 'last_name', 'avatar')
    search_fields = ('username', 'email', 'first_name', 'last_name')

    def username(self, obj):
        return obj.username

    def email(self, obj):
        return obj.email
