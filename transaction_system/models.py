import uuid

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError


def validate_interval_for_price(value):
    """
    Function to check value for popularity
    """
    if value < 0.0:
        raise ValidationError(('%(value)s must be in the range [0.0, 100.0]'), params={'value': value}, )


class Users(AbstractUser):
    """
    Primary user model
    """
    admin = models.BooleanField(default=False)

    def __str__(self):
        return self.username


# Item model
class Item(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    item_code = models.CharField(max_length=50, primary_key=True)
    price = models.DecimalField(max_digits=10, decimal_places=2,  validators=[validate_interval_for_price])
    category = models.CharField(max_length=255)
    starting_quantity = models.PositiveIntegerField()
    current_quantity = models.PositiveIntegerField()

    def __str__(self):
        return self.name

# Transaction model (with total_amount)
class Transaction(models.Model):
    transaction_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction_date = models.DateField(db_index=True)
    transaction_time = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[validate_interval_for_price])  # Total Bill Amount

    def __str__(self):
        return f'Transaction {self.transaction_id} on {self.transaction_date}'

# BillItem model
class BillItem(models.Model):
    transaction = models.ForeignKey(Transaction, related_name='bill_items', on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[validate_interval_for_price])

    def __str__(self):
        return f'{self.quantity} of {self.item.name}'

