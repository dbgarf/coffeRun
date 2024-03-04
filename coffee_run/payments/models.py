from django.db import models
from decimal import Decimal
from django.urls import reverse

class User(models.Model):
    name = models.CharField(unique=True, max_length=255)
    last_payment_date = models.DateField(default=None, null=True)
    # positive number means they've spent more than they've paid, negative number the opposite
    net_credit = models.DecimalField(decimal_places=2, max_digits=6, default=0)
    
    def __str__(self) -> str:
        return f"CoffeeRun User {self.name}"

    def get_absolute_url(self):
        return reverse("user_update", kwargs={"pk": self.pk})

class OrderItem(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(decimal_places=2, max_digits=6)
    ordered_by = models.ForeignKey("User", on_delete=models.CASCADE)
    group_order = models.ForeignKey('GroupOrder', on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"CoffeeRun OrderItem #{self.id} {self.name}"

GROUP_ORDER_STATUS = {
    'pending': 'pending',
    'complete': 'complete'
}

class GroupOrder(models.Model):
    order_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=255, choices=GROUP_ORDER_STATUS, default=GROUP_ORDER_STATUS['pending'])
    payer = models.ForeignKey("User", on_delete=models.CASCADE, null=True, default=None)

    def __str__(self) -> str:
        return f"CoffeeRun GroupOrder #{self.id} {self.order_date} ${self.total_price}"
    
    @property
    def total_price(self) -> Decimal:
        return sum([item.price for item in self.orderitem_set.all()])

    def complete_order(self) -> 'GroupOrder':
        # compute the user participating in the order who should pay
        order_items = self.orderitem_set.all().select_related('ordered_by')
        max_credit = order_items.aggregate(max_value=models.Max('ordered_by__net_credit'))['max_value']
        payer = order_items.filter(ordered_by__net_credit=max_credit).order_by("ordered_by__last_payment_date").first().ordered_by

        # update the net_credit and last_payment_date of the users
        updated_users = []
        for item in order_items:
            user = item.ordered_by
            if user == payer:
                user.net_credit = user.net_credit - self.total_price + item.price
                user.last_payment_date = self.order_date
            else:
                user.net_credit = user.net_credit + item.price
            updated_users.append(user)

        User.objects.bulk_update(updated_users, ["net_credit", "last_payment_date"])

        # and then finally complete the group order
        self.payer = payer
        self.status = GROUP_ORDER_STATUS['complete']
        self.save()
        return self