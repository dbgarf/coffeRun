from django.shortcuts import render
from django.http import HttpResponse, HttpRequest, JsonResponse
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

def validate_order_item_json(order_items):
    errors = {}
    if not order_items:
        errors['general'] = "Form cannot be blank"
    for idx, item in enumerate(order_items):
        row_errors = {}
        if 'name' not in item:
            row_errors['name'] = f'Name is required for row {idx}'
        if not item['name']:
            row_errors['name'] = f'Name is required for row {idx}'
        if 'price' not in item:
            row_errors['price'] = f'Price is required for row {idx}'
        if not item['price']:
            row_errors['price'] = f'Price is required for row {idx}'
        if float(item['price']) > 99:
            row_errors['price'] = f'Price must be less than 100 for row {idx}'
        if 'user' not in item:
            row_errors['user'] = f'User is required for row {idx}'
        if not item['user']:
            row_errors['user'] = f'User is required for row {idx}'
        if 'user' in item and item['user'] and not User.objects.filter(pk=item['user']).exists():
            row_errors['user'] = f'User does not exist for row {idx}'
        if row_errors:
            errors[idx] = row_errors
    if not errors:
        return True, {}
    return False, errors

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
        valid, errors = validate_order_item_json(json_payload)
        if not valid:
            return JsonResponse(errors, status=400)

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