# ledger/models.py
from django.db import models
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
import uuid
from django.core.validators import RegexValidator

# Default category definitions that should exist for every user.
# Each item is a tuple of (title, hex_color).
# These are not placeholder data; they are initial options to streamline UX.
DEFAULT_CATEGORY_DEFINITIONS = [
    ("Savings", "#22C55E"),           # green-500
    ("Emergency Funds", "#EF4444"),   # red-500
    ("Food Fund", "#F59E0B"),         # amber-500
]

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
    # When True, auto-carry logic in the view will not overwrite base_budget for this date
    # allowing manual changes such as savings withdrawal or reset to persist.
    is_manual_override = models.BooleanField(default=False)

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
        # Overspent: 100% or more of allocated budget
        if self.total_expenses >= self.base_budget:
            return "Overspent"
        # Balanced: 50% up to below 100% of allocated budget
        if usage >= Decimal('50') and usage < Decimal('100'):
            return "Balanced"
        return "Underspent"
    
    class Meta:
        unique_together = (('user', 'date'),)
        indexes = [
            models.Index(fields=['user', 'date']),
        ]

class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='categories')
    title = models.CharField(max_length=100)
    color = models.CharField(
        max_length=7,
        default="#3B82F6",
        validators=[
            RegexValidator(
                regex=r'^#(?:[0-9a-fA-F]{3}){1,2}$',
                message='Color must be a hex code like #AABBCC'
            )
        ],
        help_text="Hex color like #AABBCC"
    )

    class Meta:
        unique_together = (('user', 'title'),)
        indexes = [
            models.Index(fields=['user', 'title']),
        ]

    def __str__(self):
        return self.title


def ensure_default_categories_for_user(user):
    """Create the project's default categories for a user if missing.

    This is idempotent and safe to call on every request. It will only
    create what does not already exist for the given user.
    """
    for title, color in DEFAULT_CATEGORY_DEFINITIONS:
        try:
            Category.objects.get_or_create(user=user, title=title, defaults={"color": color})
        except Exception:
            # In case of race condition during concurrent creation, continue
            pass

class Expense(models.Model):
    daily_ledger = models.ForeignKey(DailyLedger, on_delete=models.CASCADE, related_name='expenses')
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses')
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