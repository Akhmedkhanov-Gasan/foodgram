from django.contrib import admin

from .models import Interaction


@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe', 'interaction_type')
    list_filter = ('interaction_type',)
    search_fields = ('user__username', 'recipe__name')
