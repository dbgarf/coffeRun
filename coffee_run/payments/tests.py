from django.test import TestCase
from .models import User, OrderItem, GroupOrder, GROUP_ORDER_STATUS
from datetime import date as date

class FairnessAlgorithmTests(TestCase):
    def test_can_save_models(self):
        user1 = User.objects.create(name='Dan')
        user2 = User.objects.create(name='Jim')
        group_order_1 = GroupOrder.objects.create()
        order_item_1 = OrderItem.objects.create(name='black coffee', price=1, ordered_by=user1, group_order=group_order_1)
        order_item_2 = OrderItem.objects.create(name='cappucino', price=5, ordered_by=user2, group_order=group_order_1)

        self.assertEqual(
            sum([order_item_1.price, order_item_2.price]),
            group_order_1.total_price
        )
        self.assertEqual(group_order_1.status, GROUP_ORDER_STATUS['pending'])

    def test_group_order_complete_order_basic(self):
        """
        Scenario: Dan has the highest net credit before the group order and should pay for this one
        """
        user1 = User.objects.create(name='Dan', net_credit=10, last_payment_date=date(2024, 3, 1))
        user2 = User.objects.create(name='Jim', net_credit=-5, last_payment_date=date(2024, 3, 2))
        group_order_1 = GroupOrder.objects.create()
        OrderItem.objects.create(name='black coffee', price=1, ordered_by=user1, group_order=group_order_1)
        OrderItem.objects.create(name='cappucino', price=5, ordered_by=user2, group_order=group_order_1)

        self.assertEqual(group_order_1.status, GROUP_ORDER_STATUS['pending'])

        group_order_1.complete_order()

        # refresh the users for new values after the order is completed
        user1.refresh_from_db()
        user2.refresh_from_db()
        self.assertEqual(group_order_1.payer, user1)
        self.assertEqual(user1.net_credit, 4) # 10 to begin with minus 6 for this order
        self.assertEqual(user2.net_credit, 0) # -5 to begin with plus 5 for the price of their order item
        self.assertEqual(user1.last_payment_date, group_order_1.order_date)
        self.assertEqual(group_order_1.status, GROUP_ORDER_STATUS['complete'])

    def test_group_order_complete_order_resolves_ties_by_last_payment_date(self):
        """
        Scenario: Dan and Jim are tied on net_credit, but Dan paid least recently, so he should pay
        """
        user1 = User.objects.create(name='Dan', net_credit=10, last_payment_date=date(2024, 3, 1))
        user2 = User.objects.create(name='Jim', net_credit=10, last_payment_date=date(2024, 3, 2))
        group_order_1 = GroupOrder.objects.create()
        OrderItem.objects.create(name='black coffee', price=1, ordered_by=user1, group_order=group_order_1)
        OrderItem.objects.create(name='cappucino', price=5, ordered_by=user2, group_order=group_order_1)

        self.assertEqual(group_order_1.status, GROUP_ORDER_STATUS['pending'])
        group_order_1.complete_order()

        # refresh the users for new values after the order is completed
        user1.refresh_from_db()
        user2.refresh_from_db()
        self.assertEqual(group_order_1.payer, user1)
        self.assertEqual(user1.net_credit, 4)
        self.assertEqual(user2.net_credit, 15)
        self.assertEqual(user1.last_payment_date, group_order_1.order_date)
        self.assertEqual(user2.last_payment_date, date(2024, 3, 2))
        self.assertEqual(group_order_1.status, GROUP_ORDER_STATUS['complete'])