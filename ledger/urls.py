# ledger/urls.py

from django.urls import path
from .views import daily_view, update_savings, calendar_view, update_budget, get_day_summary, register, delete_expense, reset_budget, monthly_summary, hide_patch_notes, user_settings

urlpatterns = [
    # URL for today's ledger (the homepage)
    path('', daily_view, name='daily_view_today'),

    # URL for a specific date's ledger
    path('<int:year>/<int:month>/<int:day>/', daily_view, name='daily_view_date'),
    
    # URL for the savings update action
    path('update-savings/', update_savings, name='update_savings'),
    
    # URL for the default calendar view
    path('calendar/', calendar_view, name='calendar_view_default'),
    
    # URL for a specific month in the calendar
    path('calendar/<int:year>/<int:month>/', calendar_view, name='calendar_view'),
    # Monthly expense summary with percentages
    path('summary/<int:year>/<int:month>/', monthly_summary, name='monthly_summary'),
    # Patch notes preference
    path('hide-patch-notes/', hide_patch_notes, name='hide_patch_notes'),
    
    # URL for the budget update action
    path('<int:year>/<int:month>/<int:day>/update-budget/', update_budget, name='update_budget'),
    path('<int:year>/<int:month>/<int:day>/reset-budget/', reset_budget, name='reset_budget'),
    
    # AJAX endpoint for getting day summary
    path('api/day-summary/', get_day_summary, name='get_day_summary'),
    path('register/', register, name='register'),
    path('settings/', user_settings, name='user_settings'),
    # Expense delete (edit removed)
    path('expense/<int:expense_id>/delete/', delete_expense, name='delete_expense'),
]