import io

from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.pagination import LimitPagination
from api.permissions import IsAuthorOrReadOnly, IsAuthenticatedOrRegistration
from api.serializers import (AvatarUpdateSerializer, IngredientSerializer,
                             RecipeCreateSerializer, RecipeListSerializer,
                             SubscriptionSerializer, RecipeShortSerializer,
                             TagSerializer, UserSerializer)
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from users.models import Subscription, User


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для рецептов."""

    permission_classes = [IsAuthorOrReadOnly]
    pagination_class = LimitPagination
    filterset_class = RecipeFilter
    filter_backends = [DjangoFilterBackend]

    def get_serializer_class(self):
        """Определяет сериализатор в зависимости от действия."""
        if self.action in ['list', 'retrieve']:
            return RecipeListSerializer
        return RecipeCreateSerializer

    def get_queryset(self):
        """Оптимизируем запросы для уменьшения количества запросов к БД."""
        queryset = Recipe.objects.all()
        queryset = queryset.select_related('author')
        queryset = queryset.prefetch_related(
            'tags',
            'recipe_ingredients__ingredient',
            'favorites',
            'shopping_carts'
        )
        return queryset

    def _handle_add_action(self, request, recipe, model_class, error_message):
        """Добавить рецепт в список (избранное или корзину)."""
        obj, created = model_class.objects.get_or_create(
            user=request.user,
            recipe=recipe
        )
        if not created:
            return Response(
                {'errors': error_message},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = RecipeShortSerializer(
            recipe,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _handle_remove_action(
            self, request, recipe, model_class, error_message):
        """Удалить рецепт из списка (избранное или корзину)."""
        deleted, _ = model_class.objects.filter(
            user=request.user,
            recipe=recipe
        ).delete()
        if not deleted:
            return Response(
                {'errors': error_message},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _get_shopping_cart_ingredients(self, user):
        """Получить ингредиенты из корзины пользователя с группировкой."""
        return (
            Ingredient.objects.filter(
                recipe_ingredients__recipe__shopping_carts__user=user
            )
            .values(
                'name',
                'measurement_unit'
            )
            .annotate(
                amount=Sum('recipe_ingredients__amount')
            )
            .order_by('name')
        )

    def _format_shopping_list(self, ingredients):
        """Отформатировать список ингредиентов для текстового файла."""
        if not ingredients:
            return 'Список покупок пуст.\n'
        lines = ['Список покупок:\n\n']
        for ingredient in ingredients:
            name = ingredient['name']
            unit = ingredient['measurement_unit']
            amount = ingredient['amount']
            lines.append(f'• {name} ({unit}) — {amount}\n')
        return ''.join(lines)

    def _create_download_response(self, content, filename):
        """Создать HTTP-ответ для скачивания файла."""
        file_like = io.BytesIO(content.encode('utf-8'))
        return FileResponse(
            file_like,
            as_attachment=True,
            filename=filename,
            content_type='text/plain; charset=utf-8'
        )

    @action(
        detail=True,
        methods=['get'],
        permission_classes=[AllowAny],
        url_path='get-link'
    )
    def get_link(self, request, pk=None):
        """Получить прямую ссылку на рецепт."""
        recipe = self.get_object()
        host = request.get_host()
        link = f"{host}/recipes/{recipe.id}/"
        return Response({'short-link': link})

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        """Добавить/удалить рецепт из избранного."""
        recipe = self.get_object()
        if request.method == 'POST':
            return self._handle_add_action(
                request,
                recipe,
                Favorite,
                'Рецепт уже в избранном'
            )
        return self._handle_remove_action(
            request,
            recipe,
            Favorite,
            'Рецепт не был в избранном'
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='shopping_cart',
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        """Добавить/удалить рецепт из списка покупок."""
        recipe = self.get_object()
        if request.method == 'POST':
            return self._handle_add_action(
                request,
                recipe,
                ShoppingCart,
                'Рецепт уже в списке покупок'
            )
        return self._handle_remove_action(
            request,
            recipe,
            ShoppingCart,
            'Рецепт не был в списке покупок'
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Скачать список покупок текущего пользователя."""
        ingredients = self._get_shopping_cart_ingredients(request.user)
        content = self._format_shopping_list(ingredients)
        return self._create_download_response(content, 'shopping_list.txt')


class UserViewSet(DjoserUserViewSet):
    """Вьюсет для управления пользователями, аватарами и подписками."""

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedOrRegistration]
    pagination_class = LimitPagination

    @action(
        detail=False,
        methods=['get', 'patch'],
        url_path='me',
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        """Получить или обновить профиль текущего пользователя."""
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)
        serializer = self.get_serializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['put', 'delete'],
        url_path='me/avatar',
        permission_classes=[IsAuthenticated]
    )
    def avatar(self, request):
        """Управление аватаром текущего пользователя."""
        if request.method == 'DELETE':
            if request.user.avatar:
                request.user.avatar.delete()
                request.user.avatar = None
                request.user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        if 'avatar' not in request.data:
            return Response(
                {'errors': 'Поле avatar обязательно для заполнения'},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = AvatarUpdateSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'avatar': request.build_absolute_uri(request.user.avatar.url)},
            status=status.HTTP_200_OK
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id=None):
        """Подписаться/отписаться от автора."""
        user = request.user
        author = get_object_or_404(User, id=id)
        if request.method == 'POST':
            if user == author:
                return Response(
                    {'errors': 'Нельзя подписаться на самого себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if Subscription.objects.filter(
                user=user,
                author=author
            ).exists():
                return Response(
                    {'errors': 'Вы уже подписаны на этого автора'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Subscription.objects.create(user=user, author=author)
            serializer = SubscriptionSerializer(
                author,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        deleted, _ = Subscription.objects.filter(
            user=user,
            author=author
        ).delete()
        if not deleted:
            return Response(
                {'errors': 'Вы не были подписаны на этого автора'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        """Получить список подписок текущего пользователя."""
        authors = User.objects.filter(
            following__user=request.user
        ).select_related().prefetch_related(
            'recipes'
        )
        page = self.paginate_queryset(authors)
        if page is not None:
            serializer = SubscriptionSerializer(
                page,
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        serializer = SubscriptionSerializer(
            authors,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)
