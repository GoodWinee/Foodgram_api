import django_filters
from django_filters.rest_framework import BooleanFilter

from recipes.models import Ingredient, Recipe, Tag


class IngredientFilter(django_filters.FilterSet):
    """Фильтр для ингредиентов."""

    name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(django_filters.FilterSet):
    """Фильтр для рецептов."""

    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
        conjoined=False
    )
    is_favorited = BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = BooleanFilter(method='filter_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')

    def filter_is_favorited(self, queryset, name, value):
        """Фильтрация по избранному."""
        request = getattr(self, 'request', None)
        if value and request and request.user.is_authenticated:
            return queryset.filter(
                favorites__user=request.user
            )
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Фильтрация по корзине покупок."""
        request = getattr(self, 'request', None)
        if value and request and request.user.is_authenticated:
            return queryset.filter(
                shopping_carts__user=request.user
            )
        return queryset
