from rest_framework import generics
from rest_framework.serializers import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404
from ..models import Review
from apps.listings.models import Listing
from apps.listings.choices import ListingStatusChoices
from ..choices import ReviewStatusChoices
from ..permissions import IsReviewerOrAdmin
from ..serializers import (ReviewListSerializer, ReviewDetailSerializer, ReviewCreateSerializer, ReviewUpdateSerializer,
                           ReviewStatusActionSerializer)


class ReviewListView(generics.ListAPIView):
    serializer_class = ReviewListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        # Получаем listing_id из URL
        listing_id = self.kwargs.get('listing_id')

        # Если пользователь - администратор, возвращаем все отзывы, независимо от статуса листинга
        if self.request.user.is_staff:
            listing = get_object_or_404(Listing, id=listing_id)
            return Review.objects.filter(listing=listing).order_by('-created_at')

        # Для обычных пользователей проверяем, что листинг существует и имеет статус "активен"
        listing = get_object_or_404(Listing, id=listing_id, status=ListingStatusChoices.ACTIVE)

        # Если пользователь - ревьюер, возвращаем все видимые отзывы и свои отзывы, кроме удаленных
        if self.request.user.is_authenticated:
            return Review.objects.filter(
                listing=listing
            ).filter(
                status=ReviewStatusChoices.VISIBLE
            ).union(
                Review.objects.filter(
                    listing=listing,
                    reviewer=self.request.user
                ).exclude(status=ReviewStatusChoices.DELETED)
            ).order_by('-created_at')

        # Возвращаем только видимые отзывы для анонимных пользователей
        return Review.objects.filter(listing=listing, status=ReviewStatusChoices.VISIBLE).order_by('-created_at')


class ReviewDetailView(generics.RetrieveAPIView):
    serializer_class = ReviewDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id'

    def get_object(self):
        # Получаем review_id из URL
        review_id = self.kwargs.get('id')

        # Получаем отзыв
        review = get_object_or_404(Review, id=review_id)

        # Если пользователь - администратор, возвращаем отзыв независимо от статуса
        if self.request.user.is_staff:
            return review

        # Если пользователь - ревьюер, возвращаем отзыв, если листинг активен и отзыв не удален
        if (
            self.request.user == review.reviewer and
            review.listing.status == ListingStatusChoices.ACTIVE and
            review.status != ReviewStatusChoices.DELETED
        ):
            return review

        # Проверяем, что листинг активен и отзыв видимый для обычных пользователей
        if review.listing.status == ListingStatusChoices.ACTIVE and review.status == ReviewStatusChoices.VISIBLE:
            return review

        # Если условия не выполняются, запрещаем доступ
        self.permission_denied(self.request, message="You do not have permission to view this review.")


class ReviewCreateView(generics.CreateAPIView):
    serializer_class = ReviewCreateSerializer

    def get_listing(self):
        listing_id = self.kwargs['listing_id']
        try:
            return Listing.objects.get(id=listing_id)
        except Listing.DoesNotExist:
            raise ValidationError('Listing not found.')

    def perform_create(self, serializer):
        listing = self.get_listing()
        serializer.save(reviewer=self.request.user, listing=listing)


class ReviewUpdateView(generics.UpdateAPIView):
    serializer_class = ReviewUpdateSerializer
    queryset = Review.objects.all()
    permission_classes = [IsAuthenticated, IsReviewerOrAdmin]
    lookup_field = 'id'

    def get_object(self):
        review = super().get_object()
        self.check_object_permissions(self.request, review)
        return review


class BaseReviewStatusUpdateView(generics.UpdateAPIView):
    serializer_class = ReviewStatusActionSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    action = None

    def get_queryset(self):
        return Review.objects.all()

    def perform_update(self, serializer):
        review = self.get_object()

        if self.action == 'apply_shadow_ban':
            if review.listing.status == ListingStatusChoices.ACTIVE and review.status != ReviewStatusChoices.DELETED:
                serializer.save(action=self.action)
            else:
                raise ValidationError("Cannot apply shadow ban: listing is not active or review is deleted.")

        elif self.action == 'soft_delete':
            serializer.save(action=self.action)


class ReviewApplyShadowBanView(BaseReviewStatusUpdateView):
    action = 'apply_shadow_ban'
    permission_classes = [IsAuthenticated, IsAdminUser]


class ReviewSoftDeleteView(BaseReviewStatusUpdateView):
    action = 'soft_delete'
    permission_classes = [IsAuthenticated, IsReviewerOrAdmin]
