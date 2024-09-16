from datetime import datetime

import numpy as np
from django.core.exceptions import ValidationError
from django.db.models.functions import Coalesce
from .models import Item, Transaction, BillItem
from django.utils import timezone
from django.db.models import Sum, Avg, ExpressionWrapper, F, FloatField


def parse_date_range(start_date_str, end_date_str):
    """
    Parse and validate date range strings.
    """
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        if start_date > end_date:
            raise ValidationError("Start date must be before end date.")
        return start_date, end_date
    except ValueError:
        raise ValidationError("Invalid date format. Use YYYY-MM-DD.")

def calculate_total_amount(items_data):
    """
    Calculate the total amount for a list of items.
    """
    total_amount = 0
    for item_data in items_data:
        item_code = item_data.get('item_code')
        quantity = item_data.get('quantity')

        try:
            item = Item.objects.get(item_code=item_code)
        except Item.DoesNotExist:
            raise ValueError(f"Item with code {item_code} not found.")

        if item.current_quantity < quantity:
            raise ValueError(f"Insufficient stock for item: {item.name}")

        total_amount += quantity * item.price
    return total_amount

def undo_transaction(transaction):
    """
    Undo a transaction by restoring the stock of items.
    """
    for bill_item in transaction.bill_items.all():
        item = bill_item.item
        item.current_quantity += bill_item.quantity
        item.save()

    transaction.delete()
    return True

def create_transaction(items_data):
    """
    Create a new transaction and associated bill items.
    """
    transaction = Transaction.objects.create(transaction_date=timezone.now().date())
    total_amount = 0

    for item_data in items_data:
        item_code = item_data.get('item_code')
        quantity = item_data.get('quantity')

        try:
            item = Item.objects.get(item_code=item_code)
        except Item.DoesNotExist:
            undo_transaction(transaction)
            raise ValueError(f"Item with code {item_code} not found.")

        if item.current_quantity < quantity:
            undo_transaction(transaction)
            raise ValueError(f"Insufficient stock for item: {item.name} with item_code: {item_code}")

        BillItem.objects.create(
            transaction=transaction,
            item=item,
            quantity=quantity,
            unit_price=item.price
        )

        total_amount += quantity * item.price
        item.current_quantity -= quantity
        item.save()

    transaction.total_amount = total_amount
    transaction.save()

    return transaction


def get_sales_summary_for_day(date):
    """
    Calculate the  sales summary for a given date.
    """
    total_sales = Transaction.objects.filter(transaction_date=date).aggregate(total_sales=Sum('total_amount'))['total_sales'] or 0
    items_quantity = BillItem.objects.select_related('item', 'transaction').filter(transaction__transaction_date=date) \
        .values('item__name') \
        .annotate(total_quantity_sold=Sum('quantity')) \
        .order_by('item__name')

    categories_quantity = BillItem.objects.select_related('item', 'transaction').filter(transaction__transaction_date=date) \
        .values('item__category') \
        .annotate(total_quantity_sold=Sum('quantity')) \
        .order_by('item__category')

    return  {
        "total_sales": total_sales,
        "items_quantity": list(items_quantity),
        "categories_quantity": list(categories_quantity)
    }


def get_avg_sales_summary(start_date, end_date):
    """
    Calculate the Avg sales summary for a given date range.
    """
    total_sales_amount = Transaction.objects.filter(transaction_date__range=(start_date, end_date)) \
                             .aggregate(total_amount=Avg('total_amount'))['total_amount'] or 0

    item_data = (BillItem.objects.select_related('item', 'transaction').filter(
        transaction__transaction_date__range=(start_date, end_date))
        .values('item__name')
        .annotate(
        avg_quantity_sold=Avg('quantity'),
        avg_item_sales=Avg(F('quantity') * F('unit_price'))
    ))

    category_data = BillItem.objects.select_related('item', 'transaction').filter(
        transaction__transaction_date__range=(start_date, end_date)) \
        .values('item__category') \
        .annotate(
        avg_quantity_sold=Avg('quantity'),
        avg_category_sales=Avg(F('quantity') * F('unit_price'))
    )

    return {
        'avg_sales_amount': total_sales_amount,
        'items': list(item_data),
        'categories': list(category_data)
    }


def get_sales_data(start_date, end_date):
    """
    Calculate the sales data for a given date range.
    """
    transactions = Transaction.objects.filter(transaction_date__range=(start_date, end_date))

    total_sales = transactions.aggregate(
        total_sales=Coalesce(Sum('total_amount', output_field=FloatField()), 0.0)
    )['total_sales']

    avg_sales = transactions.aggregate(
        avg_sales=Coalesce(Avg('total_amount', output_field=FloatField()), 0.0)
    )['avg_sales']

    item_sales = BillItem.objects.select_related('item', 'transaction') \
        .filter(transaction__transaction_date__range=(start_date, end_date)).order_by('transaction__transaction_date') \
        .values(transaction_date=F('transaction__transaction_date'),
        name=F('item__name'),
        category=F('item__category') ) \
        .annotate(
        total_quantity_sold=Sum('quantity'),
        total_sales=Coalesce(
            Sum(ExpressionWrapper(
                F('quantity') * F('unit_price'),
                output_field=FloatField()
            )),
            0.0,
            output_field=FloatField()
        )
    )
    return total_sales, avg_sales, item_sales



def get_sales_data_by_item(start_date, end_date):
    # Group and aggregate data by day, item, and category
    sales_data = BillItem.objects.select_related('item', 'transaction') \
        .filter(transaction__transaction_date__range=(start_date, end_date)) \
        .values('transaction__transaction_date', 'item__name', 'item__category') \
        .annotate(
            total_quantity_sold=Sum('quantity'),
            total_sales=ExpressionWrapper(
                Sum(F('quantity') * F('unit_price')),
                output_field=FloatField()
            )
        ) \
        .order_by('item__name', 'transaction__transaction_date')  # Order by item and date
    return list(sales_data)

def calculate_moving_average(sales_df, window=3):
    # Calculate moving average for each item day-wise
    sales_df['moving_avg_sales'] = sales_df.groupby('item__name')['total_sales'].transform(
        lambda x: x.rolling(window=window, min_periods=1).mean()
    )
    return sales_df

def calculate_manual_trend(sales_df):
    # Calculate day-wise sales trend
    sales_df['sales_trend'] = sales_df.groupby('item__name')['total_sales'].diff().fillna(0)
    sales_df['trend'] = np.where(
        sales_df['sales_trend'] > 0, 'Increasing',
        np.where(sales_df['sales_trend'] < 0, 'Decreasing', '-')
    )
    return sales_df



def get_sales_data_for_date_range(start_date, end_date):
    """
    Fetch sales data for given date range.
    """
    sales_data = BillItem.objects.select_related('item', 'transaction') \
        .filter(transaction__transaction_date__range=(start_date, end_date)) \
        .aggregate(
        total_sales=Coalesce(
            Sum(ExpressionWrapper(
                F('quantity') * F('unit_price'),
                output_field=FloatField()
            )),
            0.0,
            output_field=FloatField()
        ),
        total_quantity_sold=Sum('quantity')
    )

    return sales_data