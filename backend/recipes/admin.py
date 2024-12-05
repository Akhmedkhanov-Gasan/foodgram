from django.contrib import admin
from django.db.models import Count, Q

from .models import Ingredient, Recipe, RecipeIngredient, Tag


class RecipeIngredientInline(admin.TabularInline):
    """Inline display of ingredients in recipes."""
    model = RecipeIngredient
    extra = 0


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Admin panel for managing recipes."""
    list_display = ('name', 'author', 'get_favorites_count')
    search_fields = ('name', 'author__username', 'author__email')
    list_filter = ('tags', 'author')
    inlines = [RecipeIngredientInline]

    def get_queryset(self, request):
        """Annotate queryset with the number of times recipes are favorited."""
        queryset = super().get_queryset(request)
        return queryset.annotate(
            favorites_count=Count(
                'interactions',
                filter=Q(interactions__interaction_type='favorite')
            )
        )

    def get_favorites_count(self, obj):
        """Display the annotated favorites count."""
        return getattr(obj, 'favorites_count', 0)

    get_favorites_count.short_description = 'Favorites Count'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
