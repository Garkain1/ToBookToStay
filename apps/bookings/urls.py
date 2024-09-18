from django.urls import path
from .views.booking_views import (
    OwnerListingBookingsListView,
    ListingBookingsListView,
    UserBookingsListView,
    BookingRequestView,
    BookingConfirmView,
    BookingCompleteView,
    BookingCancelView,
    BookingSoftDeleteView,
    BookingCreateView,
    BookingUpdateView,
    BookingDetailView,
)

urlpatterns = [
    # Список бронирований
    path('listings/bookings/', OwnerListingBookingsListView.as_view(), name='owner-listing-bookings-list'),
    path('listings/<int:listing_id>/bookings/', ListingBookingsListView.as_view(), name='listing-bookings-list'),
    path('bookings/', UserBookingsListView.as_view(), name='user-bookings-list'),

    # Детальный просмотр, создание и обновление бронирования
    path('bookings/create/<int:listing_id>/', BookingCreateView.as_view(), name='booking-create'),
    path('bookings/<int:id>/', BookingDetailView.as_view(), name='booking-detail'),
    path('bookings/update/<int:id>/', BookingUpdateView.as_view(), name='booking-update'),

    # Статусные действия над бронированием
    path('bookings/<int:id>/request/', BookingRequestView.as_view(), name='booking-request'),
    path('bookings/<int:id>/confirm/', BookingConfirmView.as_view(), name='booking-confirm'),
    path('bookings/<int:id>/complete/', BookingCompleteView.as_view(), name='booking-complete'),
    path('bookings/<int:id>/cancel/', BookingCancelView.as_view(), name='booking-cancel'),
    path('bookings/<int:id>/soft-delete/', BookingSoftDeleteView.as_view(), name='booking-soft-delete'),
]
