from django.contrib import admin
from django.db.models import Count
from admin_auto_filters.filters import AutocompleteFilter

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)


class AuthorFilter(AutocompleteFilter):
    title = 'Author'
    field_name = 'author'


class TagFilter(AutocompleteFilter):
    title = 'Tags'
    field_name = 'tags'


class RecipeIngredientInline(admin.TabularInline):
    """Inline display of ingredients in recipes."""

    model = RecipeIngredient
    extra = 0


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Admin panel for managing recipes."""

    list_display = (
        'name',
        'author',
        'get_favorites_count',
        'cooking_time',
        'created_at',
        'updated_at'
    )
    search_fields = ('name', 'author__username', 'author__email')
    list_filter = (TagFilter, AuthorFilter)
    inlines = [RecipeIngredientInline]

    def get_queryset(self, request):
        """Optimize queries for the admin panel."""
        queryset = super().get_queryset(request)
        return queryset.select_related(
            'author'
        ).prefetch_related(
            'tags', 'ingredients'
        ).annotate(favorites_count=Count(
            'favorited_by')
        )

    def get_favorites_count(self, obj):
        """Display the number of times the recipe was added to favorites."""
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
    list_filter = ('measurement_unit',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Admin panel for managing favorites."""

    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'user__email', 'recipe__name')
    list_filter = ('user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Admin panel for managing shopping carts."""

    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'user__email', 'recipe__name')
    list_filter = ('user', 'recipe')
