# ledger/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.http import JsonResponse
from .models import DailyLedger, Expense, SavingsAccount
from decimal import Decimal
from datetime import date, timedelta
from .utils import LedgerHTMLCalendar, reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from .forms import RegistrationForm
from django.db.models import Sum
from django.contrib import messages


def propagate_carryover(user, start_date: date):
    """Propagate remaining budget forward to successive days until it reaches zero
    or until we hit a day that already has expenses (we won't overwrite those).

    Rules:
    - Next day base_budget becomes previous day's remaining_budget
    - Continue while remaining > 0 and next day's expenses count == 0
    - Stop at safety horizon of 60 days to avoid infinite loops
    """
    horizon_days = 60
    current_date = start_date

    for _ in range(horizon_days):
        ledger = DailyLedger.objects.filter(user=user, date=current_date).first()
        if not ledger:
            break

        remaining = ledger.remaining_budget
        next_date = current_date + timedelta(days=1)

        # Ensure next day exists (so user can see ahead) but do not overwrite days with expenses
        next_ledger, _ = DailyLedger.objects.get_or_create(user=user, date=next_date)

        # Set next day's base to today's remaining
        if next_ledger.base_budget != remaining:
            next_ledger.base_budget = remaining
            next_ledger.save()

        if remaining <= Decimal('0.00'):
            break

        current_date = next_date

@login_required(login_url='login')
def daily_view(request, year=None, month=None, day=None):
    if year and month and day:
        current_date = date(year, month, day)
    else:
        current_date = timezone.now().date()

    previous_day = current_date - timedelta(days=1)
    next_day = current_date + timedelta(days=1)
    
    ledger, created = DailyLedger.objects.get_or_create(user=request.user, date=current_date)
    # Carry over yesterday's remaining into today's base budget. Also self-heal if ledger exists but differs and has no expenses yet.
    prev_ledger = DailyLedger.objects.filter(user=request.user, date=previous_day).first()
    if prev_ledger:
        remaining_yesterday = (prev_ledger.base_budget - (prev_ledger.expenses.aggregate(total=Sum('price'))['total'] or Decimal('0.00')))
        carry = remaining_yesterday if remaining_yesterday > Decimal('0.00') else Decimal('0.00')
        # Preserve manual increases (e.g., withdrawals). Only bump up if below carry.
        if ledger.base_budget < carry:
            ledger.base_budget = carry
            ledger.save()

    # After computing today's state, propagate remaining forward to successive days
    propagate_carryover(request.user, current_date)
    savings_account, _ = SavingsAccount.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        description = request.POST.get('description')
        price_str = request.POST.get('price')

        if description and price_str:
            try:
                price = Decimal(price_str)
                # Guard: prevent adding expenses when remaining budget is zero
                if ledger.remaining_budget <= Decimal('0.00'):
                    messages.error(request, "Cannot add expense. Today's budget is exhausted.")
                else:
                    # If price exceeds remaining, allow partial? Overrule: block entirely.
                    if price > ledger.remaining_budget:
                        messages.error(request, "Expense exceeds remaining budget. Reduce the amount or add budget.")
                    else:
                        Expense.objects.create(daily_ledger=ledger, description=description, price=price)
                        # Expense changes remaining; re-run propagation from this date
                        propagate_carryover(request.user, current_date)
            except (ValueError, TypeError):
                pass
        return redirect('daily_view_date', year=current_date.year, month=current_date.month, day=current_date.day)

    expenses_today = ledger.expenses.all()
    context = {
        'ledger': ledger,
        'expenses': expenses_today,
        'savings_account': savings_account,
        'savings_non_positive': savings_account.balance <= Decimal('0.00'),
        'current_date': current_date,
        'today_long': current_date.strftime("%m/%d/%Y | %A"),
        'previous_day': previous_day,
        'next_day': next_day,
    }
    return render(request, 'ledger/daily_view.html', context)

@login_required(login_url='login')
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
                savings_account, _ = SavingsAccount.objects.get_or_create(user=request.user)

                # 3. Perform the correct action based on which button was clicked
                if action == 'add':
                    # Must be a whole positive number
                    if amount <= 0:
                        messages.error(request, "Amount must be a whole, positive number.")
                        return redirect('daily_view_today')
                    # ensure whole number
                    if amount != amount.to_integral_value():
                        messages.error(request, "Amount must be a whole number (no decimals).")
                        return redirect('daily_view_today')
                    savings_account.balance += amount
                    messages.success(request, f"Added ₱{amount} to savings.")
                elif action == 'withdraw':
                    if savings_account.balance <= Decimal('0.00'):
                        messages.error(request, "Cannot withdraw. Savings is zero or negative.")
                        return redirect('daily_view_today')
                    if amount > savings_account.balance:
                        messages.error(request, "Cannot withdraw more than available savings.")
                        return redirect('daily_view_today')
                    # Decrease savings and move cash to today's effective budget (base_budget)
                    savings_account.balance -= amount
                    
                    # Ensure today's ledger exists and add withdrawn amount to base budget
                    today = timezone.now().date()
                    today_ledger, _ = DailyLedger.objects.get_or_create(user=request.user, date=today)
                    today_ledger.base_budget += amount
                    today_ledger.save()

                    # Changing today's base affects future carryover
                    propagate_carryover(request.user, today)
                    
                    messages.success(request, f"Withdrew ₱{amount} from savings and added to today's budget.")
                
                # 4. Save the changes to the database
                savings_account.save()

        except (ValueError, TypeError):
            # If the amount is not a valid number, do nothing.
            # A more advanced app might show an error message.
            pass
    
    # 5. Redirect the user back to the main page to see the updated total
    return redirect('daily_view_today')

@login_required(login_url='login')
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

@login_required(login_url='login')
def update_budget(request, year, month, day):
    if request.method == 'POST':
        try:
            current_date = date(year, month, day)
            ledger = DailyLedger.objects.get(user=request.user, date=current_date)
            # Allow explicit base budget update for the selected date
            new_budget_str = request.POST.get('new_base_budget')
            
            if new_budget_str:
                ledger.base_budget = Decimal(new_budget_str)
                ledger.save()
        except (DailyLedger.DoesNotExist, ValueError, TypeError):
            pass
    
    return redirect('daily_view_date', year=year, month=month, day=day)

@login_required(login_url='login')
def get_day_summary(request):
    """AJAX endpoint to get expense summary for a specific date"""
    if request.method == 'GET':
        year = int(request.GET.get('year'))
        month = int(request.GET.get('month'))
        day = int(request.GET.get('day'))
        
        try:
            target_date = date(year, month, day)
            ledger = DailyLedger.objects.get(user=request.user, date=target_date)
            
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


@login_required(login_url='login')
def edit_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id, daily_ledger__user=request.user)
    ledger_date = expense.daily_ledger.date
    if request.method == 'POST':
        description = request.POST.get('description')
        price_str = request.POST.get('price')
        try:
            if description:
                expense.description = description
            if price_str:
                new_price = Decimal(price_str)
                # Ensure the edit keeps expenses within budget (optional strictness)
                ledger = expense.daily_ledger
                current_total_minus_this = ledger.total_expenses - expense.price
                if new_price + current_total_minus_this > ledger.base_budget:
                    messages.error(request, "Edited amount exceeds remaining budget. Reduce the amount or add budget.")
                else:
                    expense.price = new_price
                    expense.save()
                    messages.success(request, "Expense updated.")
                    # Re-propagate from edited day
                    propagate_carryover(request.user, ledger_date)
        except (ValueError, TypeError):
            pass
    return redirect('daily_view_date', year=ledger_date.year, month=ledger_date.month, day=ledger_date.day)


@login_required(login_url='login')
def delete_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id, daily_ledger__user=request.user)
    ledger_date = expense.daily_ledger.date
    if request.method == 'POST':
        expense.delete()
        messages.success(request, "Expense removed.")
        # Re-propagate from deletion day
        propagate_carryover(request.user, ledger_date)
    return redirect('daily_view_date', year=ledger_date.year, month=ledger_date.month, day=ledger_date.day)

def register(request):
    if request.user.is_authenticated:
        return redirect('daily_view_today')
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            # Initialize per-user savings account lazily on first use
            return redirect('daily_view_today')
    else:
        form = RegistrationForm()
    return render(request, 'auth/register.html', {'form': form})
