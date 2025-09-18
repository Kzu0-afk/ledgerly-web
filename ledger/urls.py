from django.urls import path
from .views import daily_view, update_savings

urlpatterns = [
  path('', daily_view, name='daily_view'),  
  path('update-savings/', update_savings, name='update_savings'),
]