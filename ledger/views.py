# ledger/views.py
from django.shortcuts import render, redirect
from django.utils import timezone
from django.http import JsonResponse
from .models import DailyLedger, Expense, SavingsAccount
from decimal import Decimal
from datetime import date, timedelta
from .utils import LedgerHTMLCalendar, reverse


def daily_view(request, year=None, month=None, day=None):
    if year and month and day:
        current_date = date(year, month, day)
    else:
        current_date = timezone.now().date()

    previous_day = current_date - timedelta(days=1)
    next_day = current_date + timedelta(days=1)
    
    ledger, created = DailyLedger.objects.get_or_create(date=current_date)
    savings_account, _ = SavingsAccount.objects.get_or_create(pk=1)

    if request.method == 'POST':
        description = request.POST.get('description')
        price_str = request.POST.get('price')

        if description and price_str:
            try:
                price = Decimal(price_str)
                Expense.objects.create(daily_ledger=ledger, description=description, price=price)
                
                # Every expense is a direct deduction from your total savings
                savings_account.balance -= price
                savings_account.save()
            except (ValueError, TypeError):
                pass
        return redirect('daily_view_date', year=current_date.year, month=current_date.month, day=current_date.day)

    expenses_today = ledger.expenses.all()
    context = {
        'ledger': ledger,
        'expenses': expenses_today,
        'savings_account': savings_account,
        'current_date': current_date,
        'today_long': current_date.strftime("%m/%d/%Y | %A"),
        'previous_day': previous_day,
        'next_day': next_day,
    }
    return render(request, 'ledger/daily_view.html', context)

def update_savings(request):
    # This view only processes form submissions, so we only care about POST requests
    if request.method == 'POST':
        try:
            # 1. Get the data from the form
            amount_str = request.POST.get('amount')
            action = request.POST.get('action')
            
            if amount_str and action:
                amount = Decimal(amount_str)
                
                # 2. Get the single savings account object
                savings_account, _ = SavingsAccount.objects.get_or_create(pk=1)

                # 3. Perform the correct action based on which button was clicked
                if action == 'add':
                    savings_account.balance += amount
                elif action == 'withdraw':
                    savings_account.balance -= amount
                
                # 4. Save the changes to the database
                savings_account.save()

        except (ValueError, TypeError):
            # If the amount is not a valid number, do nothing.
            # A more advanced app might show an error message.
            pass
    
    # 5. Redirect the user back to the main page to see the updated total
    return redirect('daily_view')

def calendar_view(request, year=None, month=None):
    if year is None or month is None:
        today = timezone.now().date()
        year, month = today.year, today.month

    cal = LedgerHTMLCalendar().formatmonth(year, month)
    
    # Logic for previous/next month links
    next_month = month + 1
    next_year = year
    if next_month > 12:
        next_month = 1
        next_year += 1
        
    prev_month = month - 1
    prev_year = year
    if prev_month < 1:
        prev_month = 12
        prev_year -= 1

    context = {
        'calendar': cal,
        'current_month_name': date(year, month, 1).strftime('%B %Y'),
        'next_month_url': reverse('calendar_view', args=(next_year, next_month)),
        'prev_month_url': reverse('calendar_view', args=(prev_year, prev_month)),
    }
    return render(request, 'ledger/calendar.html', context)

def update_budget(request, year, month, day):
    if request.method == 'POST':
        try:
            current_date = date(year, month, day)
            ledger = DailyLedger.objects.get(date=current_date)
            # The input name is now 'new_base_budget'
            new_budget_str = request.POST.get('new_base_budget')
            
            if new_budget_str:
                # Update the base_budget field
                ledger.base_budget = Decimal(new_budget_str)
                ledger.save()
        except (DailyLedger.DoesNotExist, ValueError, TypeError):
            pass
    
    return redirect('daily_view_date', year=year, month=month, day=day)

def get_day_summary(request):
    """AJAX endpoint to get expense summary for a specific date"""
    if request.method == 'GET':
        year = int(request.GET.get('year'))
        month = int(request.GET.get('month'))
        day = int(request.GET.get('day'))
        
        try:
            target_date = date(year, month, day)
            ledger = DailyLedger.objects.get(date=target_date)
            
            data = {
                'total_expenses': float(ledger.total_expenses),
                'remaining_budget': float(ledger.daily_savings),
                'effective_budget': float(ledger.effective_budget),
                'status': ledger.status,
                'usage_percentage': float(ledger.budget_usage_percentage)
            }
        except DailyLedger.DoesNotExist:
            # If no ledger exists for this date, assume no expenses
            data = {
                'total_expenses': 0,
                'remaining_budget': 0,
                'effective_budget': 0,
                'status': 'No data',
                'usage_percentage': 0
            }
            
        return JsonResponse(data)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)
