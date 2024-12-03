import base64
import uuid

from django.core.files.base import ContentFile
from interactions.models import Interaction
from rest_framework import serializers
from users.serializers import CustomUserSerializer

from .models import Ingredient, Recipe, RecipeIngredient, Tag


class Base64ImageField(serializers.ImageField):
    """Field for decoding an image from Base64."""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(
                base64.b64decode(imgstr),
                name=f'{uuid.uuid4()}.{ext}'
            )
        return super().to_internal_value(data)


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
    amount = serializers.FloatField()

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
            'id', 'name', 'text', 'image',
            'ingredients', 'tags', 'cooking_time'
        ]

    def validate_ingredients(self, ingredients):
        """Validate ingredients for correctness."""
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
        """General validation of recipe data."""
        if not attrs.get('recipe_ingredients'):
            raise serializers.ValidationError(
                {"ingredients": "Ingredients are required."}
            )
        if not attrs.get('tags'):
            raise serializers.ValidationError({"tags": "Tags are required."})
        return attrs

    def save_ingredients(self, recipe, ingredients_data):
        """Save ingredients for the recipe."""
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

        # Update recipe data
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time',
            instance.cooking_time
        )
        if validated_data.get('image'):
            instance.image = validated_data.get('image')
        instance.save()

        # Update tags
        if tags_data is not None:
            instance.tags.set(tags_data)

        # Update ingredients
        if ingredients_data is not None:
            self.validate_ingredients(ingredients_data)
            instance.recipe_ingredients.all().delete()
            self.save_ingredients(instance, ingredients_data)

        return instance

    def to_representation(self, instance):
        """Use detailed RecipeSerializer for data representation."""
        return RecipeSerializer(instance, context=self.context).data


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for recipes."""
    author = CustomUserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='recipe_ingredients'
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
            return Interaction.objects.filter(
                user=user,
                recipe=obj,
                interaction_type=Interaction.FAVORITE
            ).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return Interaction.objects.filter(
                user=user, recipe=obj,
                interaction_type=Interaction.SHOPPING_CART
            ).exists()
        return False
