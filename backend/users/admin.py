from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Subscription, User


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Admin panel for managing subscriptions."""

    list_display = ('user', 'author')
    search_fields = (
        'user__username',
        'author__username',
        'user__email',
        'author__email',
    )
    list_filter = ('user', 'author')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin panel for managing user profiles."""

    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'is_active',
        'is_superuser'
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_active', 'is_superuser')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': (
            'is_active',
            'is_staff',
            'is_superuser',
            'groups',
            'user_permissions'
        )}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )

    ordering = ('username',)
