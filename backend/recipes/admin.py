from django.contrib import admin

from .models import Ingredient, Recipe, RecipeIngredient, Tag

admin.site.register(Tag)
admin.site.register(Ingredient)
admin.site.register(Recipe)


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ['recipe', 'ingredient', 'amount']
