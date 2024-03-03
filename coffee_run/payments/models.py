from django.db import models

class User(models.Model):
    name = models.CharField(unique=True, max_length=255)
    last_payment_date = models.DateField(default=None, null=True)
    # positive number means they've spent more than they've paid, negative number the opposite
    net_credit = models.DecimalField(decimal_places=2, max_digits=4, default=0)

class OrderItem(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(decimal_places=2, max_digits=4)
    ordered_by = models.ForeignKey("User", on_delete=models.CASCADE)
    group_order = models.ForeignKey('GroupOrder', on_delete=models.CASCADE)

class GroupOrder(models.Model):
    order_date = models.DateField(auto_now_add=True)
    payer = models.ForeignKey("User", on_delete=models.CASCADE)
    total_price = models.DecimalField(decimal_places=2, max_digits=4)