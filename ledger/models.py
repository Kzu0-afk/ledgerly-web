# ledger/models.py
from django.db import models
from django.utils import timezone
from decimal import Decimal

class SavingsAccount(models.Model):
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=38000.00)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Total Savings: {self.balance}"

class DailyLedger(models.Model):
    date = models.DateField(primary_key=True, default=timezone.now)
    budget_allocated = models.DecimalField(max_digits=10, decimal_places=2, default=100.00)

    def __str__(self):
        return self.date.strftime('%Y-%m-%d')

    @property
    def total_expenses(self):
        return self.expenses.aggregate(total=models.Sum('price'))['total'] or Decimal('0.00')

    @property
    def daily_savings(self):
        return self.budget_allocated - self.total_expenses

    @property
    def budget_usage_percentage(self):
        if self.budget_allocated > 0:
            return (self.total_expenses / self.budget_allocated) * 100
        return 0

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