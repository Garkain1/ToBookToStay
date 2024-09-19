from django.urls import path
from .views.review_views import (
    ReviewListView,
    ReviewDetailView,
    ReviewCreateView,
    ReviewUpdateView,
    ReviewApplyShadowBanView,
    ReviewSoftDeleteView,
)

urlpatterns = [
    path(
        'listings/<int:listing_id>/reviews/',
        ReviewListView.as_view(),
        name='review-list'
    ),
    path(
        'reviews/create/<int:listing_id>/',
        ReviewCreateView.as_view(),
        name='review-create'
    ),
    path(
        'reviews/<int:id>/',
        ReviewDetailView.as_view(),
        name='review-detail'
    ),
    path(
        'reviews/update/<int:id>/',
        ReviewUpdateView.as_view(),
        name='review-update'
    ),
    path(
        'reviews/<int:id>/apply-shadow-ban/',
        ReviewApplyShadowBanView.as_view(),
        name='review-apply-shadow-ban'
    ),
    path(
        'reviews/<int:id>/soft-delete/',
        ReviewSoftDeleteView.as_view(),
        name='review-soft-delete'
    ),
]
