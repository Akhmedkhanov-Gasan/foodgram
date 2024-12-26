from rest_framework import serializers

from api.users.serializers import CustomUserSerializer
from api.utils import Base64ImageField
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for ingredients."""

    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags."""

    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Serializer for recipe-ingredient relation."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'name', 'measurement_unit', 'amount']


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating a recipe."""

    ingredients = RecipeIngredientSerializer(
        many=True,
        source='recipe_ingredients'
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = [
            'id',
            'name',
            'text',
            'image',
            'ingredients',
            'tags',
            'cooking_time'
        ]

    def validate_tags(self, tags):
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError("Tags must be unique.")
        return tags

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(
                "The ingredient list cannot be empty."
            )

        unique_ingredients = set()
        for ingredient in ingredients:
            if ingredient['amount'] <= 0:
                raise serializers.ValidationError(
                    "Ingredient amount must be greater than 0."
                )
            ingredient_id = ingredient['ingredient'].id
            if ingredient_id in unique_ingredients:
                raise serializers.ValidationError(
                    "Ingredients must not be duplicated."
                )
            unique_ingredients.add(ingredient_id)
        return ingredients

    def validate(self, attrs):
        if not attrs.get('recipe_ingredients'):
            raise serializers.ValidationError(
                {"ingredients": "Ingredients are required."}
            )
        if not attrs.get('tags'):
            raise serializers.ValidationError({"tags": "Tags are required."})
        return attrs

    def save_ingredients(self, recipe, ingredients_data):
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient_data['ingredient'],
                amount=ingredient_data['amount']
            ) for ingredient_data in ingredients_data
        ])

    def create(self, validated_data):
        ingredients_data = validated_data.pop('recipe_ingredients')
        tags_data = validated_data.pop('tags')

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        self.save_ingredients(recipe, ingredients_data)

        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('recipe_ingredients', None)
        tags_data = validated_data.pop('tags', None)

        instance = super().update(instance, validated_data)

        if tags_data is not None:
            instance.tags.set(tags_data)

        if ingredients_data is not None:
            self.validate_ingredients(
                ingredients_data)
            instance.recipe_ingredients.all().delete()
            self.save_ingredients(instance, ingredients_data)

        return instance

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for recipes."""

    author = CustomUserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True, source='recipe_ingredients'
    )
    tags = TagSerializer(many=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = [
            'id', 'author', 'name', 'text', 'image',
            'ingredients', 'tags', 'cooking_time',
            'is_favorited', 'is_in_shopping_cart'
        ]

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return Favorite.objects.filter(user=user, recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return ShoppingCart.objects.filter(user=user, recipe=obj).exists()
        return False


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Serializer for the shopping cart."""

    id = serializers.ReadOnlyField(source='recipe.id')
    name = serializers.ReadOnlyField(source='recipe.name')
    image = serializers.ImageField(source='recipe.image', read_only=True)
    cooking_time = serializers.ReadOnlyField(source='recipe.cooking_time')

    class Meta:
        model = ShoppingCart
        fields = ['id', 'name', 'image', 'cooking_time']

    def validate(self, attrs):
        """Check if the recipe is already in the shopping cart."""
        user = self.context['request'].user
        recipe = self.context['recipe']
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                {"detail": "Recipe is already in the shopping cart."}
            )
        return attrs

    def create(self, validated_data):
        """Ensure 'recipe' is set during creation."""
        recipe = self.context['recipe']
        user = self.context['request'].user
        return ShoppingCart.objects.create(user=user, recipe=recipe)


class FavoriteSerializer(serializers.ModelSerializer):
    """Serializer for managing favorites."""

    id = serializers.ReadOnlyField(source='recipe.id')
    name = serializers.ReadOnlyField(source='recipe.name')
    image = serializers.ImageField(source='recipe.image', read_only=True)
    cooking_time = serializers.ReadOnlyField(source='recipe.cooking_time')

    class Meta:
        model = Favorite
        fields = ['id', 'name', 'image', 'cooking_time']

    def validate(self, attrs):
        user = self.context['request'].user
        recipe = self.context.get('recipe')
        if not recipe:
            raise serializers.ValidationError(
                {"detail": "Recipe is required."}
            )
        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                {"detail": "Recipe is already in favorites."}
            )
        return attrs

    def create(self, validated_data):
        recipe = self.context['recipe']
        user = self.context['request'].user
        return Favorite.objects.create(user=user, recipe=recipe)
