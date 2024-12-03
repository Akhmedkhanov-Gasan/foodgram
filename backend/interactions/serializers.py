from recipes.models import Recipe
from rest_framework import serializers

from .models import Interaction


class InteractionSerializer(serializers.ModelSerializer):
    """Universal serializer for interactions."""
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    recipe_name = serializers.ReadOnlyField(source='recipe.name')
    recipe_image = serializers.ImageField(
        source='recipe.image',
        read_only=True
    )

    class Meta:
        model = Interaction
        fields = [
            'id',
            'user',
            'recipe',
            'recipe_name',
            'recipe_image',
            'interaction_type'
        ]
        read_only_fields = ['user', 'recipe_name', 'recipe_image']


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Serializer for working with the shopping cart."""
    id = serializers.IntegerField(source='recipe.id', read_only=True)
    name = serializers.CharField(source='recipe.name', read_only=True)
    image = serializers.ImageField(source='recipe.image', read_only=True)
    cooking_time = serializers.IntegerField(
        source='recipe.cooking_time',
        read_only=True
    )

    class Meta:
        model = Interaction
        fields = ['id', 'name', 'image', 'cooking_time']
