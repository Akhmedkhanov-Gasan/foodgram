from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(_('name'), max_length=32, unique=True)
    slug = models.SlugField(_('slug'), max_length=32, unique=True)

    class Meta:
        verbose_name = _('tag')
        verbose_name_plural = _('tags')

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(_('name'), max_length=100)
    measurement_unit = models.CharField(_('measurement unit'), max_length=50)

    class Meta:
        verbose_name = _('ingredient')
        verbose_name_plural = _('ingredients')

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name=_('author')
    )
    name = models.CharField(_('name'), max_length=256, unique=True)
    text = models.TextField(_('description'))
    image = models.ImageField(_('image'), upload_to='recipes/images/')
    ingredients = models.ManyToManyField(
        'Ingredient',
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name=_('ingredients')
    )
    tags = models.ManyToManyField(
        'Tag',
        related_name='recipes',
        verbose_name=_('tags')
    )
    cooking_time = models.PositiveSmallIntegerField(
        _('cooking time (minutes)'),
        validators=[
            MinValueValidator(1, _('Cooking time must be at least 1 minute')),
            MaxValueValidator(1440, _('Cooking time cannot exceed 24 hours'))
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True,
                                      verbose_name=_('created at'))
    updated_at = models.DateTimeField(auto_now=True,
                                      verbose_name=_('updated at'))

    class Meta:
        verbose_name = _('recipe')
        verbose_name_plural = _('recipes')
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name=_('recipe')
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_recipes',
        verbose_name=_('ingredient')
    )
    amount = models.PositiveSmallIntegerField(
        _('amount'),
        validators=[
            MinValueValidator(1, _('Amount must be at least 1')),
            MaxValueValidator(10000, _('Amount cannot exceed 10000'))
        ]
    )

    class Meta:
        verbose_name = _('recipe ingredient')
        verbose_name_plural = _('recipe ingredients')

    def __str__(self):
        return f"{self.ingredient.name} ({self.amount})"


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name=_('user')
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name=_('recipe')
    )

    class Meta:
        unique_together = ('user', 'recipe')
        verbose_name = _('favorite')
        verbose_name_plural = _('favorites')

    def __str__(self):
        return f"{self.user.email} - {self.recipe.name}"


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name=_('user')
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name=_('recipe')
    )

    class Meta:
        unique_together = ('user', 'recipe')
        verbose_name = _('shopping cart')
        verbose_name_plural = _('shopping carts')

    def __str__(self):
        return f"{self.user.email} - {self.recipe.name}"
