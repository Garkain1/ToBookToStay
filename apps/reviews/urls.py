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
        'listings/<int:listing_id>/',
        ReviewListView.as_view(),
        name='review-list'
    ),
    path(
        'create/<int:listing_id>/',
        ReviewCreateView.as_view(),
        name='review-create'
    ),
    path(
        '<int:id>/',
        ReviewDetailView.as_view(),
        name='review-detail'
    ),
    path(
        'update/<int:id>/',
        ReviewUpdateView.as_view(),
        name='review-update'
    ),
    path(
        '<int:id>/apply-shadow-ban/',
        ReviewApplyShadowBanView.as_view(),
        name='review-apply-shadow-ban'
    ),
    path(
        '<int:id>/soft-delete/',
        ReviewSoftDeleteView.as_view(),
        name='review-soft-delete'
    ),
]
