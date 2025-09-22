# ledger/models.py
from django.db import models
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
import uuid

class SavingsAccount(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='savings_account', null=True, blank=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Total Savings: {self.balance}"

# ledger/models.py

class DailyLedger(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='daily_ledgers', null=True, blank=True)
    date = models.DateField(default=timezone.now)
    base_budget = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        return self.date.strftime('%Y-%m-%d')

    @property
    def total_expenses(self):
        return self.expenses.aggregate(total=models.Sum('price'))['total'] or Decimal('0.00')

    @property
    def total_rollover(self):
        """Rollover disabled in overrule mode. Always zero."""
        return Decimal('0.00')

    @property
    def effective_budget(self):
        """Effective budget equals today's base budget in overrule mode."""
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
    
    class Meta:
        unique_together = (('user', 'date'),)
        indexes = [
            models.Index(fields=['user', 'date']),
        ]
        
class Expense(models.Model):
    daily_ledger = models.ForeignKey(DailyLedger, on_delete=models.CASCADE, related_name='expenses')
    description = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.description} - {self.price}"


class UserProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile for {self.user.username}"