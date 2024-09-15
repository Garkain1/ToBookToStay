from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework_simplejwt.tokens import RefreshToken
from ..serializers import (CreateUserSerializer, UserListSerializer, UserDetailSerializer, UpdateUserSerializer,
                           ChangePasswordSerializer, ActivateUserSerializer, DeactivateUserSerializer,
                           DeleteUserSerializer)
from ..models import User
from ..choices import UserStatusChoices


class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = CreateUserSerializer
    permission_classes = []

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        refresh = RefreshToken.for_user(user)

        response_data = {
            'id': user.id,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

        return Response(response_data, status=status.HTTP_201_CREATED)


class UserListView(generics.ListAPIView):
    queryset = User.objects.all().order_by('email')
    serializer_class = UserListSerializer
    permission_classes = [permissions.IsAdminUser]


class UserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        obj = super().get_object()

        # Если пользователь - администратор, он может просматривать любые профили, независимо от статуса
        if self.request.user.is_staff:
            return obj

        # Если профиль, к которому пытается получить доступ пользователь, имеет статус DELETED
        if obj.status == UserStatusChoices.DELETED:
            # Профили со статусом DELETED возвращают 404 для всех, кроме администратора
            raise NotFound("The profile you are looking for does not exist.")

        # Проверяем, запрашивает ли пользователь свой собственный профиль
        if self.request.user == obj:
            # Пользователь со статусами PENDING и DEACTIVATED может видеть свой собственный профиль
            if obj.status in [UserStatusChoices.PENDING, UserStatusChoices.DEACTIVATED]:
                return obj
            return obj

        # Обычные пользователи не могут видеть профили со статусами PENDING, DEACTIVATED
        if obj.status in [UserStatusChoices.PENDING, UserStatusChoices.DEACTIVATED]:
            raise PermissionDenied("You do not have permission to access this profile.")

        # Если пользователь имеет статус DELETED, он не может просматривать чужие профили
        if self.request.user.status == UserStatusChoices.DELETED:
            raise PermissionDenied("Deleted users cannot access other profiles.")

        return obj


class UserUpdateView(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UpdateUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        obj = super().get_object()

        if self.request.user != obj and not self.request.user.is_staff:
            raise PermissionDenied("You do not have permission to update this user's information.")

        if self.request.user == obj and obj.status == UserStatusChoices.DELETED:
            raise PermissionDenied("You cannot update a deleted account.")

        return obj

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


class ChangePasswordView(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        obj = super().get_object()

        if self.request.user != obj and not self.request.user.is_staff:
            raise PermissionDenied("You do not have permission to change this user's password.")

        if self.request.user == obj and obj.status == UserStatusChoices.DELETED:
            raise PermissionDenied("You cannot change the password of a deleted account.")

        return obj

    def update(self, request, *args, **kwargs):
        if request.user.is_staff:
            serializer = self.get_serializer(data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({"detail": "Password updated successfully."})

        return super().update(request, *args, **kwargs)


class ActivateUserView(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = ActivateUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        obj = super().get_object()

        if self.request.user != obj and not self.request.user.is_staff:
            raise PermissionDenied("You do not have permission to activate this user's account.")

        return obj


class DeactivateUserView(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = DeactivateUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Получаем объект пользователя
        obj = super().get_object()

        # Проверяем права доступа (только владелец или администратор)
        if self.request.user != obj and not self.request.user.is_staff:
            raise PermissionDenied("You do not have permission to deactivate this user's account.")

        return obj


class DeleteUserView(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = DeleteUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        obj = super().get_object()

        if self.request.user != obj and not self.request.user.is_staff:
            raise PermissionDenied("You do not have permission to delete this user's account.")

        return obj
