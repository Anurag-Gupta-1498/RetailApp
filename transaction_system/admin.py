from django.contrib import admin
from .models import *


# Register your models here.

@admin.register(Users)
class Users(admin.ModelAdmin):
    list_display = ('id', 'username', 'admin')
    search_fields = ('username',)


@admin.register(Item)
class Item(admin.ModelAdmin):
    list_display = ('name', 'item_code', 'price', 'category', 'starting_quantity', 'current_quantity')
    search_fields = ('item_code','category', 'current_quantity')

@admin.register(Transaction)
class Transaction(admin.ModelAdmin):
    list_display = ('transaction_date', 'transaction_id', 'transaction_time', 'total_amount')
    search_fields = ('transaction_id', 'transaction_date')

@admin.register(BillItem)
class BillItem(admin.ModelAdmin):
    list_display = ('quantity', 'unit_price', 'transaction', 'item')
    search_fields = ('transaction',)