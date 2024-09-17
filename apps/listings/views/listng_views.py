from rest_framework import generics
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from ..models import Listing
from ..choices import ListingStatusChoices
from ..serializers import (ListingListSerializer, ListingDetailSerializer, ListingCreateSerializer,
                           ListingUpdateSerializer, ListingStatusActionSerializer)
from ..permissions import IsOwnerOrReadOnly, IsBusinessAccount
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework import status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, ValidationError

User = get_user_model()


class ListingListView(generics.ListAPIView):
    serializer_class = ListingListSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['price', 'location', 'rooms', 'property_type', 'status']
    search_fields = ['title', 'description', 'location', 'address']

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.is_staff:
            return Listing.objects.all().order_by('-created_at')
        return Listing.objects.filter(status=ListingStatusChoices.ACTIVE).order_by('-created_at')

    def get_ordering_fields(self, request):
        user = self.request.user
        if user.is_authenticated and user.is_staff:
            return ['status', 'price', 'created_at']
        return ['price', 'created_at']


class ListingDetailView(generics.RetrieveAPIView):
    serializer_class = ListingDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.is_staff:
                return Listing.objects.all()

            return Listing.objects.filter(owner=user).exclude(status=ListingStatusChoices.DELETED) | \
                Listing.objects.filter(status=ListingStatusChoices.ACTIVE)

        return Listing.objects.filter(status=ListingStatusChoices.ACTIVE)


# Создание объявления
class ListingCreateView(generics.CreateAPIView):
    serializer_class = ListingCreateSerializer
    permission_classes = [IsAuthenticated, IsBusinessAccount | IsAdminUser]

    def perform_create(self, serializer):
        # Данные верифицированы и 'owner' установлен в сериализаторе
        serializer.save()


class ListingUpdateView(generics.UpdateAPIView):
    serializer_class = ListingUpdateSerializer
    permission_classes = [IsAuthenticated, IsAdminUser | (IsOwnerOrReadOnly & IsBusinessAccount)]
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.is_staff:
            return Listing.objects.all()
        return Listing.objects.exclude(status=ListingStatusChoices.DELETED)

    def perform_update(self, serializer):
        listing = self.get_object()
        if not self.request.user.is_staff and listing.status == ListingStatusChoices.DELETED:
            return Response({"detail": "Cannot update a deleted listing."}, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()


class MyListingsView(generics.ListAPIView):
    serializer_class = ListingListSerializer
    permission_classes = [IsAuthenticated, IsAdminUser | IsBusinessAccount]

    def get_queryset(self):
        user = self.request.user
        user_id = self.kwargs.get('user_id')

        if user.is_staff:
            if user_id:
                owner = get_object_or_404(User, id=user_id)
                return Listing.objects.filter(owner=owner).order_by('-created_at')
            return Listing.objects.all().order_by('-created_at')

        if user_id and not user.is_staff:
            raise NotFound("Not found.")

        return Listing.objects.filter(owner=user).exclude(status=ListingStatusChoices.DELETED).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)

        for result in response.data['results']:
            if 'status' not in result:
                listing_id = result['id']
                listing = Listing.objects.get(id=listing_id)
                result['status'] = listing.status

        return response


class BaseListingStatusUpdateView(generics.UpdateAPIView):
    queryset = Listing.objects.all()
    serializer_class = ListingStatusActionSerializer
    permission_classes = [IsAuthenticated, IsAdminUser | (IsOwnerOrReadOnly & IsBusinessAccount)]
    lookup_field = 'id'

    action = None  # Будет устанавливаться в подклассах

    def perform_update(self, serializer):
        listing = self.get_object()
        if not self.request.user.is_staff and listing.status == ListingStatusChoices.DELETED:
            # Выбрасываем исключение вместо возврата Response
            raise ValidationError({"detail": "Cannot modify the status of a deleted listing."})

        # Передаем действие в сериализатор
        serializer.save(action=self.action)


# Вьюха для активации объявления
class ListingActivateView(BaseListingStatusUpdateView):
    action = 'activate'


# Вьюха для деактивации объявления
class ListingDeactivateView(BaseListingStatusUpdateView):
    action = 'deactivate'

    def perform_update(self, serializer):
        listing = self.get_object()
        if listing.status == ListingStatusChoices.DELETED:
            raise ValidationError({"detail": "Cannot deactivate a deleted listing."})

        serializer.save()


# Вьюха для мягкого удаления объявления
class ListingSoftDeleteView(BaseListingStatusUpdateView):
    action = 'soft_delete'
