# ledger/views.py
from django.shortcuts import render, redirect
from django.utils import timezone
from .models import DailyLedger, Expense, SavingsAccount
from decimal import Decimal

def daily_view(request):
    today = timezone.now().date()
    ledger, created = DailyLedger.objects.get_or_create(date=today)
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
        return redirect('daily_view')

    expenses_today = ledger.expenses.all()
    context = {
        'ledger': ledger,
        'expenses': expenses_today,
        'savings_account': savings_account,
        'today_long': today.strftime("%m/%d/%Y | %A")
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