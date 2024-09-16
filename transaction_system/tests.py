import base64

from django.test import TestCase
from .utils import parse_date_range, calculate_total_amount, create_transaction
from django.core.exceptions import ValidationError
from datetime import datetime
from rest_framework.test import APITestCase
from django.urls import reverse
from .models import Item, Users



class TestUtilityFunctions(TestCase):

    def test_parse_date_range_valid(self):
        start_date, end_date = parse_date_range('2024-01-01', '2024-01-31')
        self.assertEqual(start_date, datetime(2024, 1, 1).date())
        self.assertEqual(end_date, datetime(2024, 1, 31).date())

    def test_parse_date_range_invalid_format(self):
        with self.assertRaises(ValidationError):
            parse_date_range('invalid-date', '2024-01-31')

    def test_parse_date_range_logic_error(self):
        with self.assertRaises(ValidationError):
            parse_date_range('2024-01-31', '2024-01-01')

    def test_calculate_total_amount(self):
        item1 = Item.objects.create(name="Pizza", item_code="P001", price=10.0, starting_quantity = 100, current_quantity=50)
        item2 = Item.objects.create(name="Burger", item_code="B001", price=5.0, starting_quantity = 100, current_quantity=50)

        items_data = [
            {'item_code': 'P001', 'quantity': 2},
            {'item_code': 'B001', 'quantity': 3}
        ]
        total_amount = calculate_total_amount(items_data)
        self.assertEqual(total_amount, 35.0)


    def test_create_transaction(self):
        item1 = Item.objects.create(name="Pizza", item_code="P001", price=10.0, starting_quantity=100, current_quantity=50)
        items_data = [{'item_code': 'P001', 'quantity': 2}]

        transaction = create_transaction(items_data)
        self.assertEqual(transaction.total_amount, 20.0)
        item1.refresh_from_db()
        self.assertEqual(item1.current_quantity, 48)



class TransactionAPITests(APITestCase):

    def setUp(self):
        Item.objects.create(name="Pizza", item_code="P001", price=10.0, starting_quantity=100, current_quantity=50)
        self.user = Users.objects.create_user(username='testuser', password='testpass')


    def test_add_sales(self):
        url = reverse('add-sales')  # This should match the name of your endpoint
        data = {
            'items': [
                {'item_code': 'P001', 'quantity': 2}
            ]
        }
        credentials = base64.b64encode(b'testuser:testpass').decode('utf-8')
        response = self.client.post(url, data, format='json', HTTP_AUTHORIZATION='Basic ' + credentials)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(float(response.data['total_amount']), 20.0)


    def test_for_failed_authentication(self):
        url = reverse('add-sales')  # This should match the name of your endpoint
        data = {
            'items': [
                {'item_code': 'P001', 'quantity': 2}
            ]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 401)


    def test_for_failed_sales_transaction(self):
        url = reverse('add-sales')
        item = Item.objects.get(item_code='P001')
        current_item_count = Item.objects.get(item_code='P001').current_quantity
        data = {
            'items': [
                {'item_code': 'P001', 'quantity': 2},
                {'item_code': 'P111', 'quantity': 4}
            ]
        }
        credentials = base64.b64encode(b'testuser:testpass').decode('utf-8')
        response = self.client.post(url, data, format='json', HTTP_AUTHORIZATION='Basic ' + credentials)
        item.refresh_from_db()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(current_item_count, item.current_quantity) #The quantity should remain same after a failed sales transaction

    def test_sales_summary(self):
        # First create a transaction
        url = reverse('add-sales')
        data = {'items': [{'item_code': 'P001', 'quantity': 2}]}
        credentials = base64.b64encode(b'testuser:testpass').decode('utf-8')
        self.client.post(url, data, format='json')

        # Now fetch the summary
        summary_url = reverse('sales-summary')
        response = self.client.get(summary_url, HTTP_AUTHORIZATION='Basic ' + credentials)
        self.assertEqual(response.status_code, 200)
        self.assertIn('total_sales', response.data)

    def test_fetch_item_details(self):
        url = reverse('item-details', args=['P001'])  # Replace with the correct view name
        credentials = base64.b64encode(b'testuser:testpass').decode('utf-8')
        response = self.client.get(url, HTTP_AUTHORIZATION='Basic ' + credentials)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 6)
        self.assertEqual(response.data['name'], 'Pizza')


class ItemTransactionIntegrationTests(APITestCase):

    def setUp(self):
        self.user = Users.objects.create_user(username='testuser', password='testpass')

    def test_create_item_and_add_transaction(self):
        # Step 1: Create an item
        item = Item.objects.create(name="Pizza", item_code="P001", price=10.0, starting_quantity = 100, current_quantity=50)

        # Step 2: Make a transaction
        url = reverse('add-sales')
        data = {'items': [{'item_code': 'P001', 'quantity': 5}]}
        credentials = base64.b64encode(b'testuser:testpass').decode('utf-8')

        response = self.client.post(url, data, format='json', HTTP_AUTHORIZATION='Basic ' + credentials)
        self.assertEqual(response.status_code, 201)
        # Step 3: Check if item stock is updated
        item.refresh_from_db()
        self.assertEqual(item.current_quantity, 45)
