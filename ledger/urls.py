from django.urls import path
from .views import daily_view

urlpatterns = [
  path('', daily_view, name='daily_view'),  
]