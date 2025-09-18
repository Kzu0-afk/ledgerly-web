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