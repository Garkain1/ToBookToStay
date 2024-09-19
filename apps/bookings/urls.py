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
    path('listings/', OwnerListingBookingsListView.as_view(), name='owner-listing-bookings-list'),
    path('listings/<int:listing_id>/', ListingBookingsListView.as_view(), name='listing-bookings-list'),
    path('', UserBookingsListView.as_view(), name='user-bookings-list'),

    # Детальный просмотр, создание и обновление бронирования
    path('create/<int:listing_id>/', BookingCreateView.as_view(), name='booking-create'),
    path('<int:id>/', BookingDetailView.as_view(), name='booking-detail'),
    path('update/<int:id>/', BookingUpdateView.as_view(), name='booking-update'),

    # Статусные действия над бронированием
    path('<int:id>/request/', BookingRequestView.as_view(), name='booking-request'),
    path('<int:id>/confirm/', BookingConfirmView.as_view(), name='booking-confirm'),
    path('<int:id>/complete/', BookingCompleteView.as_view(), name='booking-complete'),
    path('<int:id>/cancel/', BookingCancelView.as_view(), name='booking-cancel'),
    path('<int:id>/soft-delete/', BookingSoftDeleteView.as_view(), name='booking-soft-delete'),
]
