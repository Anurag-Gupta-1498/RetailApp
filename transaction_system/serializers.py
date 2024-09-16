from rest_framework import serializers
from .models import Item, Transaction, BillItem

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['item_code', 'name', 'price', 'starting_quantity', 'current_quantity', 'category']

class BillItemSerializer(serializers.ModelSerializer):
    item = ItemSerializer()

    class Meta:
        model = BillItem
        fields = ['item', 'quantity', 'unit_price']

class TransactionSerializer(serializers.ModelSerializer):
    bill_items = BillItemSerializer(many=True, read_only=True)

    class Meta:
        model = Transaction
        fields = ['transaction_id', 'transaction_date', 'total_amount', 'bill_items']


class SalesSummarySerializer(serializers.Serializer):
    total_sales = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_items_sold = serializers.IntegerField()

class AverageSalesSerializer(serializers.Serializer):
    average_sales = serializers.DecimalField(max_digits=10, decimal_places=2)
    start_date = serializers.DateField()
    end_date = serializers.DateField()

class TrendAnalysisSerializer(serializers.Serializer):
    date = serializers.DateField()
    total_sales = serializers.DecimalField(max_digits=10, decimal_places=2)


class SalesItemSerializer(serializers.Serializer):
    item_code = serializers.CharField(max_length=50)
    quantity = serializers.IntegerField(min_value=1)

    def validate_item_code(self, value):
        try:
            # Check if the item exists in the database
            item = Item.objects.get(item_code=value)
        except Item.DoesNotExist:
            raise serializers.ValidationError(f"Item with code {value} does not exist.")
        return value

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value

class SalesTransactionSerializer(serializers.Serializer):
    items = SalesItemSerializer(many=True)

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("At least one item is required for a transaction.")
        return items


class DateRangeSerializer(serializers.Serializer):
    start_date = serializers.DateField()
    end_date = serializers.DateField()

    def validate(self, data):
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if start_date > end_date:
            raise serializers.ValidationError("start_date must be before end_date.")

        return data


class SalesComparisonRequestSerializer(serializers.Serializer):
    start_date_1 = serializers.DateField()
    end_date_1 = serializers.DateField()
    start_date_2 = serializers.DateField()
    end_date_2 = serializers.DateField()

    def validate(self, data):
        start_date_1 = data.get('start_date_1')
        end_date_1 = data.get('end_date_1')
        start_date_2 = data.get('start_date_2')
        end_date_2 = data.get('end_date_2')

        if start_date_1 > end_date_1:
            raise serializers.ValidationError("The first date range is invalid.")
        if start_date_2 > end_date_2:
            raise serializers.ValidationError("The second date range is invalid.")

        return data