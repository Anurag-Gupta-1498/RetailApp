from io import StringIO
from django.utils import timezone
from django.http import HttpResponse
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import BasicAuthentication
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Item
from .serializers import ItemSerializer, TransactionSerializer, \
    SalesTransactionSerializer, DateRangeSerializer, SalesComparisonRequestSerializer
from .utils import create_transaction, get_sales_summary_for_day, get_avg_sales_summary, get_sales_data, \
    get_sales_data_by_item, calculate_moving_average, calculate_manual_trend, get_sales_data_for_date_range
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
import pandas as pd


"""
API Endpoint: Get Item Details
Method: GET
URL: /api/items/<item_code>/

This API endpoint allows authenticated users to retrieve details of a specific item by providing the item code.

Path Parameters:
- item_code: The unique code of the item to retrieve.

Responses:
- 200 OK: Returned when the item is found. The response body contains the serialized item data.
- 404 Not Found: Returned when the item with the provided code is not found.
"""
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated, ])
class ItemDetailView(APIView):
    def get(self, request, item_code=None):
        item =  get_object_or_404(Item, item_code=item_code)
        serializer = ItemSerializer(item)
        return Response(serializer.data)


"""
API Endpoint: Add Sales Transaction
Method: POST
URL: /api/add-sales/

This API endpoint allows authenticated users to create a new sales transaction by providing the necessary data in the request body.

Request Headers:
- Authorization: Basic <credentials>

Request Body:
{
    "items": [
        {
            "item_code": "item_code",
            "quantity": 2,
            "unit_price": 9.99
        }
    ]
}

Responses:
- 201 Created: Returned when the transaction is created successfully. The response body contains the serialized transaction data.
- 400 Bad Request: Returned when the request data is invalid or when the create_transaction function raises a ValueError. The response body contains an error message.
"""
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated, ])
class AddSalesView(APIView):
    def post(self, request):
        serializer = SalesTransactionSerializer(data=request.data)
        if serializer.is_valid():
            items_data =  serializer.data.get('items')
            try:
                transaction = create_transaction(items_data)
                serializer = TransactionSerializer(transaction)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except ValueError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



"""
API Endpoint: Get Sales Summary
Method: GET
URL: /api/sales-summary/

This API endpoint allows authenticated users to retrieve the sales summary for the current day.

The sales summary is cached for 5 minutes to improve performance and reduce the load on the database.

Responses:
- 200 OK: Returned with the sales summary data in the response body.
"""
@method_decorator(cache_page(60 * 5), name='dispatch')  # Cache view for 5 minutes
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
class SalesSummaryView(APIView):
    def get(self, request):
        today = timezone.now().date()
        cache_key = f'sales_summary_{today}'
        summary = cache.get(cache_key)
        if not summary:
            summary = get_sales_summary_for_day(today)
            cache.set(cache_key, summary, timeout=60 * 5)  # Caching key for 5 minutes
        return Response(summary)


"""
API Endpoint: Get Average Sales
Method: GET
URL: /api/average-sales/

This API endpoint allows authenticated users to retrieve the average sales summary for a given date range.

The average sales summary is cached for 1 hour to improve performance and reduce the load on the database.

Query Parameters:
- start_date: The start date of the date range (format: YYYY-MM-DD).
- end_date: The end date of the date range (format: YYYY-MM-DD).

Responses:
- 200 OK: Returned with the average sales summary data in the response body.
- 400 Bad Request: Returned when the provided query parameters are invalid.
"""
@method_decorator(cache_page(60 * 60), name='dispatch')  # Cache view for 1 hour
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated, ])
class AverageSalesView(APIView):
    def get(self, request):
        serializer = DateRangeSerializer(data=request.query_params)
        if serializer.is_valid():
            start_date = serializer.validated_data['start_date']
            end_date = serializer.validated_data['end_date']
            cache_key = f'sales_summary_{start_date}_{end_date}'
            summary = cache.get(cache_key)
            if not summary:
                summary = get_avg_sales_summary(start_date, end_date)
                cache.set(cache_key, summary, timeout=60 * 60)
            return Response(summary)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


"""
API Endpoint: Generate Sales Report
Method: GET
URL: /api/sales-report/

This API endpoint allows authenticated users to generate a sales report in CSV format for a given date range.

Query Parameters:
- start_date: The start date of the date range (format: YYYY-MM-DD).
- end_date: The end date of the date range (format: YYYY-MM-DD).

Responses:
- 200 OK: Returned with the sales report in CSV format as an attachment.
- 400 Bad Request: Returned when the provided query parameters are invalid.
"""
@method_decorator(cache_page(60 * 60), name='dispatch')
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated, ])
class SalesReportView(APIView):

    def get(self, request):
        serializer = DateRangeSerializer(data=request.query_params)
        if serializer.is_valid():
            total_sales, avg_sales, item_sales = get_sales_data(serializer.data.get('start_date'), serializer.data.get('end_date'))

            item_sales_df = pd.DataFrame(list(item_sales))

            csv_buffer = StringIO()
            item_sales_df.to_csv(csv_buffer, index=False)

            csv_buffer.write("\nTotal Sales:, {}\n".format(total_sales))
            csv_buffer.write("Average Sales:, {}\n".format(avg_sales))

            response = HttpResponse(csv_buffer.getvalue(), content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="sales_report.csv"'

            return response
        else:
            return Response(serializer.errors, status=400)


"""
API Endpoint: Trend Analysis
Method: GET
URL: /api/trend-analysis/

This API endpoint allows authenticated users to perform trend analysis on sales data for a given date range.

Query Parameters:
- start_date: The start date of the date range (format: YYYY-MM-DD).
- end_date: The end date of the date range (format: YYYY-MM-DD).

Responses:
- 200 OK: Returned with the trend analysis data in the response body.
- 400 Bad Request: Returned when the provided query parameters are invalid.
"""
# @method_decorator(cache_page(60 * 60), name='dispatch')
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated, ])
class TrendAnalysisView(APIView):
    def get(self, request):

        serializer = DateRangeSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        start_date = serializer.validated_data['start_date']
        end_date = serializer.validated_data['end_date']

        sales_data = get_sales_data_by_item(start_date, end_date)
        sales_df = pd.DataFrame(sales_data)

        if sales_df.empty:
            return Response({"message": "No sales data found for the given date range."},
                            status=status.HTTP_200_OK)

        sales_df = calculate_moving_average(sales_df)
        sales_df = calculate_manual_trend(sales_df)

        # Prepare the trend analysis result for response
        trend_analysis_result = {
            "trend_data": sales_df.to_dict(orient='records'),
        }

        return Response(trend_analysis_result, status=status.HTTP_200_OK)

"""
API Endpoint: Sales Comparison
Method: GET
URL: /api/sales-comparison/

This API endpoint allows authenticated users to compare sales data between two date ranges.

Query Parameters:
- start_date_1: The start date of the first date range (format: YYYY-MM-DD).
- end_date_1: The end date of the first date range (format: YYYY-MM-DD).
- start_date_2: The start date of the second date range (format: YYYY-MM-DD).
- end_date_2: The end date of the second date range (format: YYYY-MM-DD).

Responses:
- 200 OK: Returned with the sales comparison data in the response body.
- 400 Bad Request: Returned when the provided query parameters are invalid.
"""
@method_decorator(cache_page(60 * 60), name='dispatch')
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated, ])
class SalesComparisonView(APIView):
    def get(self, request):
        serializer = SalesComparisonRequestSerializer(data=request.query_params)
        if serializer.is_valid():
            data = serializer.validated_data

            sales_data_1 = get_sales_data_for_date_range(data['start_date_1'], data['end_date_1'])
            sales_data_2 = get_sales_data_for_date_range(data['start_date_2'], data['end_date_2'])

            comparison = {
                f"date_range_from_{data['start_date_1']} to {data['end_date_1']}": {
                    'total_sales': sales_data_1['total_sales'],
                    'total_quantity_sold': sales_data_1['total_quantity_sold'],
                    'average_sales': sales_data_1['total_sales'] / (
                                (data['end_date_1'] - data['start_date_1']).days + 1)
                },
                f"date_range_from_{data['start_date_2']} to {data['end_date_2']}": {
                    'total_sales': sales_data_2['total_sales'],
                    'total_quantity_sold': sales_data_2['total_quantity_sold'],
                    'average_sales': sales_data_2['total_sales'] / (
                                (data['end_date_2'] - data['start_date_2']).days + 1)
                },
                'comparison': {
                    'sales_difference': sales_data_1['total_sales'] - sales_data_2['total_sales'],
                    'quantity_difference': sales_data_1['total_quantity_sold'] - sales_data_2['total_quantity_sold'],
                    'percentage_change_sales': (
                                (sales_data_1['total_sales'] - sales_data_2['total_sales']) / sales_data_2[
                            'total_sales'] * 100) if sales_data_2['total_sales'] != 0 else 0,
                    'percentage_change_quantity': (
                                (sales_data_1['total_quantity_sold'] - sales_data_2['total_quantity_sold']) /
                                sales_data_2['total_quantity_sold'] * 100) if sales_data_2[
                                                                                  'total_quantity_sold'] != 0 else 0,
                }
            }

            return Response(comparison, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)