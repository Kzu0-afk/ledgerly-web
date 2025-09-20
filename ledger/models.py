# ledger/models.py
from django.db import models
from django.utils import timezone
from decimal import Decimal

class SavingsAccount(models.Model):
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('38000.00'))
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Total Savings: {self.balance}"

# ledger/models.py

class DailyLedger(models.Model):
    date = models.DateField(primary_key=True, default=timezone.now)
    base_budget = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('100.00'))

    def __str__(self):
        return self.date.strftime('%Y-%m-%d')

    @property
    def total_expenses(self):
        return self.expenses.aggregate(total=models.Sum('price'))['total'] or Decimal('0.00')

    @property
    def total_rollover(self):
        """Sum of previous days' savings (base minus expenses),
        only up to today, never using future days.
        Uses Decimal arithmetic throughout to avoid float mixing.
        """
        today = timezone.now().date()
        cutoff_date = self.date if self.date <= today else today
        previous_ledgers = DailyLedger.objects.filter(date__lt=cutoff_date)

        total_saved: Decimal = Decimal('0.00')
        for ledger in previous_ledgers:
            expenses_total = ledger.expenses.aggregate(total=models.Sum('price'))['total'] or Decimal('0.00')
            total_saved += (ledger.base_budget - expenses_total)
        return total_saved

    @property
    def effective_budget(self):
        """Budget for the day including rollover from past days only.
        Future days do not anticipate rollover.
        """
        today = timezone.now().date()
        if self.date <= today:
            return self.base_budget + self.total_rollover
        return self.base_budget

    @property
    def daily_savings(self):
        """Savings relative to the day's base budget only (no rollover)."""
        return self.base_budget - self.total_expenses

    @property
    def budget_usage_percentage(self):
        """Percentage of effective budget spent (Decimal-safe)."""
        effective = self.effective_budget
        if effective > 0:
            return (self.total_expenses / effective) * Decimal('100')
        return Decimal('0.00')

    @property
    def status(self):
        usage = self.budget_usage_percentage
        if usage < 50:
            return "Underspent"
        elif 50 <= usage <= 90:
            return "Balanced"
        else:
            return "Overspent"
        
class Expense(models.Model):
    daily_ledger = models.ForeignKey(DailyLedger, on_delete=models.CASCADE, related_name='expenses')
    description = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.description} - {self.price}"