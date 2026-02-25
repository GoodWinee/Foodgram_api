from django.contrib import admin

from api.constants import EXTRA_FIELD, MIN_VALUE
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)


class RecipeIngredientInline(admin.TabularInline):
    """Вспомогательный класс для отображения ингредиентов рецепта."""

    model = RecipeIngredient
    extra = EXTRA_FIELD
    min_num = MIN_VALUE


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админ-панель для модели Recipe."""

    list_display = ('name', 'author', 'cooking_time', 'pub_date')
    list_filter = ('tags',)
    search_fields = ('name', 'author__username', 'author__email')
    inlines = (RecipeIngredientInline,)
    readonly_fields = ('pub_date',)

    def get_queryset(self, request):
        """Возвращает оптимизированный QuerySet."""
        return super().get_queryset(request).select_related('author')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Админ-панель для модели Tag."""

    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')
    list_filter = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админ-панель для модели Ingredient."""

    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Админ-панель для модели Favorite."""

    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Админ-панель для модели ShoppingCart."""

    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
