from rest_framework import generics
from ..models import Booking
from ..serializers import (BookingListSerializer, BookingDetailSerializer, BookingCreateSerializer,
                           BookingUpdateSerializer, BookingStatusActionSerializer)
from ..permissions import IsListingOwner, IsBookingOwner, IsAdminOrBookingOwnerOrListingOwner
from ..choices import BookingStatusChoices
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404
from apps.listings.models import Listing
from django.core.exceptions import PermissionDenied
from rest_framework.exceptions import ValidationError


class OwnerListingBookingsListView(generics.ListAPIView):
    serializer_class = BookingListSerializer
    permission_classes = [IsAuthenticated, IsListingOwner | IsAdminUser]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Booking.objects.all().order_by('-created_at')

        # Владелец видит только бронирования, кроме удаленных
        return Booking.objects.filter(
            listing__owner=user
        ).exclude(status=BookingStatusChoices.DELETED).order_by('-created_at')


class ListingBookingsListView(generics.ListAPIView):
    serializer_class = BookingListSerializer
    permission_classes = [IsAuthenticated, IsListingOwner | IsAdminUser]

    def get_queryset(self):
        user = self.request.user
        listing_id = self.kwargs.get('listing_id')

        # Проверка, что пользователь — владелец листинга или администратор
        listing = get_object_or_404(Listing, id=listing_id)
        if not (user == listing.owner or user.is_staff):
            raise PermissionDenied("You do not have permission to view bookings for this listing.")

        # Вернуть все бронирования для данного листинга
        if user.is_staff:
            return Booking.objects.filter(listing=listing).order_by('-created_at')

        # Владелец видит только бронирования, кроме удаленных
        return Booking.objects.filter(
            listing=listing
        ).exclude(status=BookingStatusChoices.DELETED).order_by('-created_at')


class UserBookingsListView(generics.ListAPIView):
    serializer_class = BookingListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            # Администратор видит все свои бронирования, включая удаленные
            return Booking.objects.filter(user=user).order_by('-created_at')

        # Обычные пользователи видят только свои бронирования, исключая удаленные
        return Booking.objects.filter(user=user).exclude(status=BookingStatusChoices.DELETED).order_by('-created_at')


class BookingDetailView(generics.RetrieveAPIView):
    serializer_class = BookingDetailSerializer
    permission_classes = [IsAuthenticated, IsAdminOrBookingOwnerOrListingOwner]
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            # Администратор видит все бронирования, включая удаленные
            return Booking.objects.all()

        # Обычные пользователи и владельцы видят только бронирования, кроме удаленных
        return Booking.objects.exclude(status=BookingStatusChoices.DELETED)


class BookingCreateView(generics.CreateAPIView):
    serializer_class = BookingCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Получаем listing_id из URL
        listing_id = self.kwargs.get('listing_id')
        listing = get_object_or_404(Listing, id=listing_id)

        # Получаем пользователя из сериализатора или устанавливаем текущего пользователя
        user = serializer.validated_data.get('user', self.request.user)

        # Проверяем доступность листинга для указанных дат
        if not listing.is_available(serializer.validated_data['start_date'], serializer.validated_data['end_date']):
            raise ValidationError('The selected dates are not available for this listing.')

        # Сохраняем бронирование с правильным пользователем и листингом
        serializer.save(user=user, listing=listing)


class BookingUpdateView(generics.UpdateAPIView):
    serializer_class = BookingUpdateSerializer
    permission_classes = [IsAuthenticated, IsBookingOwner]
    lookup_field = 'id'

    def get_queryset(self):
        return Booking.objects.all()  # Пермишен `IsBookingOwner` уже контролирует доступ

    def perform_update(self, serializer):
        booking = self.get_object()
        if booking.status == BookingStatusChoices.DELETED:
            raise ValidationError("Cannot update a deleted booking.")
        serializer.save()


class BaseBookingStatusUpdateView(generics.UpdateAPIView):
    serializer_class = BookingStatusActionSerializer
    permission_classes = [IsAuthenticated]  # Специальные пермишены устанавливаются в подклассах
    lookup_field = 'id'
    action = None  # Устанавливается в подклассах

    def get_queryset(self):
        return Booking.objects.all()  # Контроль доступа через пермишены

    def perform_update(self, serializer):
        booking = self.get_object()

        # Проверка для изменения статуса из DELETED
        if booking.status == BookingStatusChoices.DELETED:
            # Только администраторы могут менять статус из DELETED
            if not self.request.user.is_staff:
                raise ValidationError("Only administrators can change the status of a deleted booking.")

            # Разрешить изменение из DELETED только на CANCELED
            if self.action != 'cancel':
                raise ValidationError("A deleted booking can only be changed to canceled.")

        # Проверка для завершения (complete) — только из статуса CONFIRMED
        if self.action == 'complete' and booking.status != BookingStatusChoices.CONFIRMED:
            raise ValidationError("Booking can only be completed from the confirmed status.")

        # Проверка для запроса (request) — только из статуса PREVIEW
        if self.action == 'request' and booking.status != BookingStatusChoices.PENDING:
            raise ValidationError("Booking can only be requested from the preview status.")

        if self.action == 'confirm' and booking.status != BookingStatusChoices.REQUEST:
            raise ValidationError("Booking can only be confirmed from the request status.")

        serializer.save(action=self.action)


class BookingRequestView(BaseBookingStatusUpdateView):
    action = 'request'
    permission_classes = [IsAuthenticated, IsBookingOwner]


class BookingConfirmView(BaseBookingStatusUpdateView):
    action = 'confirm'
    permission_classes = [IsAuthenticated, IsListingOwner]


class BookingCompleteView(BaseBookingStatusUpdateView):
    action = 'complete'
    permission_classes = [IsAuthenticated, IsAdminOrBookingOwnerOrListingOwner]


class BookingCancelView(BaseBookingStatusUpdateView):
    action = 'cancel'
    permission_classes = [IsAuthenticated, IsAdminOrBookingOwnerOrListingOwner]


class BookingSoftDeleteView(BaseBookingStatusUpdateView):
    action = 'soft_delete'
    permission_classes = [IsAuthenticated, IsAdminUser]
