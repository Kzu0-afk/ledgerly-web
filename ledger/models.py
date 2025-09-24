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
    def remaining_budget(self):
        """Remaining budget for the day (can be zero but never negative for display)."""
        remaining = self.base_budget - self.total_expenses
        return remaining if remaining > Decimal('0.00') else Decimal('0.00')

    @property
    def effective_budget(self):
        """Expose remaining budget as the effective budget shown in UI."""
        return self.remaining_budget

    @property
    def daily_savings(self):
        """Savings relative to the day's base budget only (no rollover)."""
        return self.base_budget - self.total_expenses

    @property
    def budget_usage_percentage(self):
        """Percentage of the allocated base budget that has been spent."""
        allocated = self.base_budget
        if allocated > Decimal('0.00'):
            return (self.total_expenses / allocated) * Decimal('100')
        # No budget allocated: if anything was spent, treat as 100%+ usage
        return Decimal('100.00') if self.total_expenses > Decimal('0.00') else Decimal('0.00')

    @property
    def status(self):
        # Determine status relative to base budget (not remaining).
        if self.base_budget == Decimal('0.00'):
            return "Overspent" if self.total_expenses > Decimal('0.00') else "Underspent"

        usage = (self.total_expenses / self.base_budget) * Decimal('100')
        if self.total_expenses > self.base_budget:
            return "Overspent"
        if usage <= Decimal('90') and usage >= Decimal('50'):
            return "Balanced"
        return "Underspent"
    
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