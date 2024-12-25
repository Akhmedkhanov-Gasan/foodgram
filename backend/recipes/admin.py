from django.contrib import admin
from django.db.models import Count

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)


class RecipeIngredientInline(admin.TabularInline):
    """Inline display of ingredients in recipes."""
    model = RecipeIngredient
    extra = 0


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Admin panel for managing recipes."""
    list_display = ('name', 'author', 'get_favorites_count', 'cooking_time')
    search_fields = ('name', 'author__username', 'author__email')
    list_filter = ('tags', 'author')
    inlines = [RecipeIngredientInline]

    def get_queryset(self, request):
        """Annotate queryset with the number of times recipes are favorited."""
        queryset = super().get_queryset(request)
        return queryset.annotate(
            favorites_count=Count('favorited_by')
        )

    def get_favorites_count(self, obj):
        """Display the annotated favorites count."""
        return getattr(obj, 'favorites_count', 0)

    get_favorites_count.short_description = 'Favorites Count'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Admin panel for managing tags."""
    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Admin panel for managing ingredients."""
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Admin panel for managing favorites."""
    list_display = ('user', 'recipe')
    search_fields = ('user__email', 'recipe__name')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Admin panel for managing shopping carts."""
    list_display = ('user', 'recipe')
    search_fields = ('user__email', 'recipe__name')
