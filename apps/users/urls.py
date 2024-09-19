from django.urls import path
from .views import (CreateUserView, UserListView, UserDetailView, UserUpdateView, ChangePasswordView, ActivateUserView,
                    DeactivateUserView, DeleteUserView)

urlpatterns = [
    path('register/', CreateUserView.as_view(), name='user-register'),
    path('', UserListView.as_view(), name='user-list'),
    path('<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('<int:pk>/update/', UserUpdateView.as_view(), name='user-update'),
    path('<int:pk>/change-password/', ChangePasswordView.as_view(), name='user-change-password'),
    path('<int:pk>/activate/', ActivateUserView.as_view(), name='user-activate'),
    path('<int:pk>/deactivate/', DeactivateUserView.as_view(), name='user-deactivate'),
    path('<int:pk>/delete/', DeleteUserView.as_view(), name='user-delete'),
]
