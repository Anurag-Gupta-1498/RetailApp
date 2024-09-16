import os
from datetime import timedelta, datetime

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'RetailApp.settings')
django.setup()

import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from transaction_system.models import Item, Transaction, BillItem


class CreateDummyData(BaseCommand):
    def generate_date_within_range(self, start_date, end_date):
        """
        Generate a random date within a specified range.
        """
        delta = end_date - start_date
        random_number_of_days = random.randint(0, delta.days)
        random_date = start_date + timedelta(days=random_number_of_days)
        return random_date

    def create_data(self, *args, **kwargs):

        # dummy items
        item_names = ['Burger', 'Pizza', 'Fries', 'Soda', 'Pasta', 'Juice']
        categories = ['Food', 'Beverage']
        for name in item_names:
            Item.objects.create(
                name=name,
                item_code="IT"+str(random.randint(1000, 2000)),
                price=random.randint(10, 200),
                category=random.choice(categories),
                starting_quantity=random.randint(10, 100),
                current_quantity=random.randint(5, 50)
            )

        # Create dummy transactions and bill items
        items = Item.objects.all()
        for _ in range(kwargs.get('total_transactions')):  # Generate 30 transactions
            transaction_date = self.generate_date_within_range(kwargs.get('start_date'), kwargs.get('end_date'))
            transaction = Transaction.objects.create(
                transaction_date=transaction_date,
                total_amount=0
            )

            total_amount = 0
            for _ in range(random.randint(1, 5)):  # Each transaction has 1-5 items
                item = random.choice(items)
                quantity = random.randint(1, 10)
                unit_price = item.price
                total_amount += quantity * unit_price
                BillItem.objects.create(
                    transaction=transaction,
                    item=item,
                    quantity=quantity,
                    unit_price=unit_price
                )

            transaction.total_amount = total_amount
            transaction.save()

        self.stdout.write(self.style.SUCCESS('Successfully generated dummy data'))


dummy_data_obj = CreateDummyData()
dummy_data_obj.create_data(total_transactions=1000, start_date=datetime(2024, 9, 1), end_date=datetime(2024, 9, 16))