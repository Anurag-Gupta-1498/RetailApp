from __future__ import absolute_import
import os
from celery import Celery
from django.conf import settings
from celery.schedules import crontab

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'RetailApp.settings')
app = Celery('retail_app', broker= 'redis://127.0.0.1:6379/1')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')

# disable UTC so that Celery can use local time

# Load task modules from all registered Django app configs.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# app.conf.timezone = 'Asia/Kolkata'
app.conf.beat_schedule = {

	# Executes API call to restrict background service from going to sleep.
	'tokenApiCall': {
		'task': 'transaction_system.tasks.cache_sales_data_for_current_data',
		'schedule': crontab(minute='*/5')
	}
}
