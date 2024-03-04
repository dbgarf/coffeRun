from django.test import TestCase
from .models import User, OrderItem, GroupOrder, GROUP_ORDER_STATUS
from datetime import date as date
from datetime import timedelta
import random
from typing import Optional

class TestGroupOrder(TestCase):
    def test_can_save_models(self):
        """
        basically a smoke test, just to catch any invalid model configuration that would prevent saving to the db
        """
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
        self.assertEqual(user1.net_credit, 5) # 10 to begin with -6 (the order) +1 (their item) for this order
        self.assertEqual(user2.net_credit, 0) # -5 to begin with plus 5 (their item) for the price of their order item
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
        self.assertEqual(user1.net_credit, 5) # 10 to begin with -6 (the order) +1 (their item)
        self.assertEqual(user2.net_credit, 15) # 10 to begin with +5 (their item)
        self.assertEqual(user1.last_payment_date, group_order_1.order_date)
        self.assertEqual(user2.last_payment_date, date(2024, 3, 2))
        self.assertEqual(group_order_1.status, GROUP_ORDER_STATUS['complete'])

class TestFairness(TestCase):

    def make_order_item(self, 
        group_order: GroupOrder, 
        ordered_by: User,
        item_name: Optional[str]=None
    )-> OrderItem:
        menu = {
            'cappucino': 5,
            'black': 1,
            'chai': 2.5,
            'espresso': 3
        }
        if item_name is None:
            item_name = random.choice(list(menu.keys()))

        order_item = OrderItem.objects.create(
            name=item_name,
            price=menu[item_name],
            ordered_by=ordered_by,
            group_order=group_order
        )
        return order_item

    def test_simulation_1(self):
        """
        scenario: a group of 7 users, each with particular coffee ordering habits, places 100 orders

        after 365 orders, we'll examine the net_credits of each user and consider if the system is fair
        where fair means that the net credit of any user is not far from 0
        and not far from 0 means abs(net_credit) <= max(order_prices)
        """
        bob = User.objects.create(name='Bob') # always gets a $5 cappucino
        jeremy = User.objects.create(name='Jeremy') # always gets a $1 black coffee
        pat = User.objects.create(name='Pat') # always orders a $2.50 chai
        dan = User.objects.create(name='Dan') # randomly orders a drink
        alice = User.objects.create(name='Alice') # randomly orders a drink
        marisol = User.objects.create(name='Marisol') # randomly orders a drink
        sam = User.objects.create(name='Sam') # randomly orders a drink

        # simulate 1 year worth of coffee runs
        # NOTE: 365 is chosen because it's a human time scale and makes sense
        # and because it's small enough that the test runs in reasonable time
        # have manually tested this with larger iterations and it still holds up
        day_of_order = date.today()
        for _ in range(365):
            day_of_order = day_of_order + timedelta(days=1)
            group_order = GroupOrder.objects.create(order_date=day_of_order)
            self.make_order_item(group_order, bob, 'cappucino')
            self.make_order_item(group_order, jeremy, 'black')
            self.make_order_item(group_order, pat, 'chai')
            self.make_order_item(group_order, dan)
            self.make_order_item(group_order, alice)
            self.make_order_item(group_order, marisol)
            self.make_order_item(group_order, sam)
            group_order.complete_order()

        group_orders = GroupOrder.objects.all()
        max_order_price = max([order.total_price for order in group_orders])
        payer_count = {
            bob: 0,
            jeremy: 0,
            pat: 0,
            dan: 0,
            alice: 0,
            marisol: 0,
            sam: 0
        }
        for order in group_orders:
            payer_count[order.payer] +=1

        # test that bob has paid the most times and jeremy has paid the least times
        # this is what we would expect based on the prices of their preferred orders
        # not going to test the other users payer counts because of randomization, but they should all be similar, on average
        self.assertEqual(
            payer_count[bob],
            max(list(payer_count.values()))
        )
        self.assertEqual(
            payer_count[jeremy],
            min(list(payer_count.values()))
        )

        # test that net credit is never further from zero than the max order price
        # this should converge towards zero as iterations increase
        # but the inequality should be true at all times, max_order_price is an absolute ceiling
        for user in [bob, jeremy, pat, dan, alice, marisol, sam]:
            user.refresh_from_db()
            self.assertTrue(abs(user.net_credit) < max_order_price)



