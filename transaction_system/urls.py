from django.urls import path
from .views import ItemDetailView, AddSalesView, SalesSummaryView, AverageSalesView, SalesReportView, TrendAnalysisView, SalesComparisonView

urlpatterns = [
    path('items/<str:item_code>', ItemDetailView.as_view(), name='item-details'),
    path('add-sales', AddSalesView.as_view(), name='add-sales'),
    path('sales-summary', SalesSummaryView.as_view(), name='sales-summary'),
    path('average-sales-summary', AverageSalesView.as_view(), name='average-sales'),
    path('sales-report', SalesReportView.as_view(), name='sales-report'),
    path('trend-analysis', TrendAnalysisView.as_view(), name='trend-analysis'),
    path('sales-comparison', SalesComparisonView.as_view(), name='sales-comparison'),
]
