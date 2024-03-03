from django.contrib import admin
from .models import User, OrderItem, GroupOrder

admin.site.register(User)
admin.site.register(OrderItem)
admin.site.register(GroupOrder)