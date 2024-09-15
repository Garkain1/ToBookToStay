from django.urls import path
from .views import (CreateUserView, UserListView, UserDetailView, UserUpdateView, ChangePasswordView, ActivateUserView,
                    DeactivateUserView, DeleteUserView)

urlpatterns = [
    path('register/', CreateUserView.as_view(), name='user-register'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('users/<int:pk>/update/', UserUpdateView.as_view(), name='user-update'),
    path('users/<int:pk>/change-password/', ChangePasswordView.as_view(), name='user-change-password'),
    path('users/<int:pk>/activate/', ActivateUserView.as_view(), name='user-activate'),
    path('users/<int:pk>/deactivate/', DeactivateUserView.as_view(), name='user-deactivate'),
    path('users/<int:pk>/delete/', DeleteUserView.as_view(), name='user-delete'),
]
