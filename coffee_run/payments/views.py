from django.shortcuts import render
from django.http import HttpResponse, HttpRequest
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from .models import User, GroupOrder, GROUP_ORDER_STATUS, OrderItem

import json

def index(request: HttpRequest) -> HttpResponse:
    context = {}
    return render(request, "payments/index.html", context)

def list_users(request: HttpRequest) -> HttpResponse:
    users = User.objects.all()
    context = {'users': users}
    return render(request, "payments/user_list.html", context)

class UserCreateView(CreateView):
    model = User
    fields= ['name']
    success_url = reverse_lazy("user_list")

class UserUpdateView(UpdateView):
    model = User
    fields = ['name']
    success_url = reverse_lazy("user_list")

class UserDeleteView(DeleteView):
    model = User
    success_url = reverse_lazy("user_list")

def list_group_orders(request: HttpRequest) -> HttpResponse:
    group_orders = GroupOrder.objects.all()
    context = {'group_orders': group_orders}
    return render(request, "payments/group_order_list.html", context)

def detail_group_order(request: HttpRequest, pk: int) -> HttpResponse:
    group_order = GroupOrder.objects.get(id=pk)
    context =  {'group_order': group_order, 'order_items': group_order.orderitem_set.all()}
    return render(request, "payments/group_order_detail.html", context)

def create_group_order(request: HttpRequest) -> HttpResponse:
    if request.method == 'GET':
        users = []
        for user in User.objects.all():
            users.append({
                'id': user.id,
                'name': user.name
            })
        context = {'users': users}
        return render(request, "payments/group_order_create.html", context)
    
    if request.method == "PUT":
        json_payload = json.loads(request.body)
        group_order = GroupOrder.objects.create()
        for order_item in json_payload:
            user = User.objects.get(pk=order_item['user'])
            OrderItem.objects.create(
                name=order_item['name'],
                price=order_item['price'],
                ordered_by=user,
                group_order=group_order
            )
        group_order.complete_order()
        detail_url = f"/group_orders/{group_order.pk}/detail/"
        return HttpResponse(detail_url)