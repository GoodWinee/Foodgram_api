from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from api.constants import (COOKING_TIME_MAX, INGREDIENT_AMOUNT_MAX, MIN_VALUE,
                           RECIPES_LIMIT)
from api.mixins import AvatarMixin, ImageMixin, IsSubscribedMixin
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from users.models import User


class RecipeShortSerializer(ImageMixin, serializers.ModelSerializer):
    """Краткий сериализатор для рецептов в подписках."""

    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserSerializer(AvatarMixin, IsSubscribedMixin, DjoserUserSerializer):
    """Сериализатор для отображения — некоторые поля необязательны."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        fields = DjoserUserSerializer.Meta.fields + ('is_subscribed', 'avatar')


class AvatarUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления аватара с поддержкой base64."""

    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ('avatar',)


class SubscriptionSerializer(UserSerializer):
    """Сериализатор для подписок."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, obj):
        """Получает список рецептов автора для отображения в подписках."""
        request = self.context.get('request')
        recipes_limit = request.query_params.get(
            'recipes_limit') if request else None
        recipes = obj.recipes.all()
        if recipes_limit and recipes_limit.isdigit():
            recipes = recipes[:int(recipes_limit)]
        else:
            recipes = recipes[:RECIPES_LIMIT]
        return RecipeShortSerializer(
            recipes,
            many=True,
            context=self.context
        ).data

    def get_recipes_count(self, obj):
        """Возвращает количество рецептов у автора."""
        return obj.recipes.count()


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')
        read_only_fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов в рецепте."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientCreateSerializer(serializers.Serializer):
    """Сериализатор для создания ингредиентов в рецепт."""

    id = serializers.IntegerField()
    amount = serializers.IntegerField(
        min_value=MIN_VALUE,
        max_value=INGREDIENT_AMOUNT_MAX
    )

    def validate_id(self, value):
        """Проверка существования ингредиента."""
        if not Ingredient.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                f'Ингредиент с id {value} не существует.'
            )
        return value


class RecipeListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка рецептов."""

    tags = TagSerializer(many=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True, source='recipe_ingredients'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )

    def _check_user_relation(self, obj, relation_manager):
        """Проверка наличия связи у текущего пользователя."""
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and relation_manager.filter(user=request.user).exists()
        )

    def get_is_favorited(self, obj):
        """True, если рецепт в избранном у текущего пользователя."""
        return self._check_user_relation(obj, obj.favorites)

    def get_is_in_shopping_cart(self, obj):
        """True, если рецепт в корзине у текущего пользователя."""
        return self._check_user_relation(obj, obj.shopping_carts)


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления рецептов."""

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True
    )
    ingredients = IngredientCreateSerializer(many=True, required=True)
    image = Base64ImageField()
    author = UserSerializer(read_only=True)
    cooking_time = serializers.IntegerField(
        min_value=MIN_VALUE,
        max_value=COOKING_TIME_MAX
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'name', 'image', 'text', 'cooking_time'
        )

    def validate_image(self, value):
        """Проверка изображения."""
        if not value:
            raise serializers.ValidationError(
                'Поле изображения обязательно.'
            )
        return value

    def validate(self, data):
        """Общая валидация тегов и ингредиентов."""
        tags = data.get('tags')
        ingredients = data.get('ingredients')
        if not tags:
            raise serializers.ValidationError(
                'Рецепт должен содержать хотя бы один тег.'
            )
        tag_ids = [tag.id for tag in tags]
        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError(
                'Теги не должны повторяться.'
            )
        if not ingredients:
            raise serializers.ValidationError(
                'Рецепт должен содержать хотя бы один ингредиент.'
            )
        ingredient_ids = [item['id'] for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться.'
            )

        return data

    def create_ingredients(self, ingredients, recipe):
        """Создание связей ингредиентов с рецептом через bulk_create."""
        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=ingredient['id'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def create(self, validated_data):
        """Создает рецепт с автором текущего пользователя."""
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        validated_data['author'] = self.context['request'].user
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        """Обновление рецепта."""
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance.recipe_ingredients.all().delete()
        self.create_ingredients(ingredients, instance)
        instance.tags.set(tags)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """Преобразование экземпляра рецепта."""
        return RecipeListSerializer(instance, context=self.context).data
