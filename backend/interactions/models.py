from django.contrib.auth import get_user_model
from django.db import models
from recipes.models import Recipe

User = get_user_model()


class Interaction(models.Model):
    FAVORITE = 'favorite'
    SHOPPING_CART = 'shopping_cart'

    INTERACTION_CHOICES = [
        (FAVORITE, 'Favorite'),
        (SHOPPING_CART, 'Shopping Cart'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='interactions'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='interactions'
    )
    interaction_type = models.CharField(
        max_length=20,
        choices=INTERACTION_CHOICES
    )

    class Meta:
        unique_together = ('user', 'recipe', 'interaction_type')
        indexes = [
            models.Index(fields=['user', 'interaction_type']),
            models.Index(fields=['recipe', 'interaction_type']),
        ]

    def __str__(self):
        return (
            f"{self.user} {self.get_interaction_type_display()} {self.recipe}"
        )
