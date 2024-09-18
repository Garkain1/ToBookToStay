from django.urls import path
from .views import (
    ListingListView,
    ListingDetailView,
    ListingCreateView,
    ListingUpdateView,
    MyListingsView,
    ListingActivateView,
    ListingDeactivateView,
    ListingSoftDeleteView,
    AvailableDatesByMonthView
)

urlpatterns = [
    path('listings/', ListingListView.as_view(), name='listing-list'),
    path('listings/<int:id>/', ListingDetailView.as_view(), name='listing-detail'),
    path('listings/<int:listing_id>/available-dates/', AvailableDatesByMonthView.as_view(), name='available-dates-by-month'),
    path('listings/create/', ListingCreateView.as_view(), name='listing-create'),
    path('listings/<int:id>/update/', ListingUpdateView.as_view(), name='listing-update'),
    path('listings/my/', MyListingsView.as_view(), name='my-listings'),
    path('listings/my/<int:user_id>/', MyListingsView.as_view(), name='user-listings'),
    path('listings/<int:id>/activate/', ListingActivateView.as_view(), name='listing-activate'),
    path('listings/<int:id>/deactivate/', ListingDeactivateView.as_view(), name='listing-deactivate'),
    path('listings/<int:id>/soft_delete/', ListingSoftDeleteView.as_view(), name='listing-soft-delete'),
]
