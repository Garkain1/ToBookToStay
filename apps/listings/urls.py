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
    path('', ListingListView.as_view(), name='listing-list'),
    path('<int:id>/', ListingDetailView.as_view(), name='listing-detail'),
    path('<int:listing_id>/available-dates/', AvailableDatesByMonthView.as_view(), name='available-dates-by-month'),
    path('create/', ListingCreateView.as_view(), name='listing-create'),
    path('<int:id>/update/', ListingUpdateView.as_view(), name='listing-update'),
    path('my/', MyListingsView.as_view(), name='my-listings'),
    path('my/<int:user_id>/', MyListingsView.as_view(), name='user-listings'),
    path('<int:id>/activate/', ListingActivateView.as_view(), name='listing-activate'),
    path('<int:id>/deactivate/', ListingDeactivateView.as_view(), name='listing-deactivate'),
    path('<int:id>/soft_delete/', ListingSoftDeleteView.as_view(), name='listing-soft-delete'),
]
