from django.shortcuts import render
from django.http import HttpResponse, HttpRequest
from django.shortcuts import render


from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from .models import User, GroupOrder, GROUP_ORDER_STATUS, OrderItem


def index(request: HttpRequest) -> HttpResponse:
    return HttpResponse("Index Page for CoffeeRun")

def list_users(request: HttpRequest) -> HttpResponse:
    users = User.objects.all()
    context = {'users': users}
    return render(request, "payments/user_list.html", context)

class UserCreateView(CreateView):
    model = User
    fields= ['name']

class UserUpdateView(UpdateView):
    model = User
    fields = ['name']

class UserDeleteView(DeleteView):
    model = User
    success_url = reverse_lazy("list_users")