from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("users/", views.list_users, name="user_list"),
    path("users/create/", views.UserCreateView.as_view(), name="user_create"),
    path("users/<int:pk>/update/", views.UserUpdateView.as_view(), name="user_update"),
    path("users/<int:pk>/delete/", views.UserDeleteView.as_view(), name="user_delete"),
]