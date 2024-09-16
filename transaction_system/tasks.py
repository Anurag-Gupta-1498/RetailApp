from django.utils import timezone

from django.core.cache import cache

from RetailApp.celery import app
import logging

from transaction_system.utils import get_sales_summary_for_day

db_logger = logging.getLogger('db')


@app.task
def cache_sales_data_for_current_data():
    """
    Used for populating the cache with sales summary for the current day.
    This task is scheduled to run every 5 mins using celery beat scheduler for updating sales data.
    """
    today = timezone.now().date()
    cache_key = f'sales_summary_{today}'
    summary = get_sales_summary_for_day(today)
    cache.set(cache_key, summary, timeout=60 * 5)  # Cache for 5 minutes
    return True
