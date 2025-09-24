# ledger/utils.py
from calendar import HTMLCalendar
from django.urls import reverse
from django.utils import timezone
from datetime import date

class LedgerHTMLCalendar(HTMLCalendar):
    def formatday(self, day, weekday):
        if day == 0:
            return '<td class="noday">&nbsp;</td>'  # day outside month
        else:
            url = reverse('daily_view_date', args=(self.year, self.month, day))
            
            # Check if this day is in the past
            today = timezone.now().date()
            current_day = date(self.year, self.month, day)
            
            # Determine CSS classes
            css_classes = ["calendar-day-link"]
            if current_day < today:
                css_classes.append("past-day")
            elif current_day == today:
                css_classes.append("today")
            
            class_str = " ".join(css_classes)
            
            # Add data attributes for hover functionality
            return f'<td><a href="{url}" data-year="{self.year}" data-month="{self.month}" data-day="{day}" class="{class_str}">{day}</a></td>'

    def formatweek(self, theweek):
        week = ''.join(self.formatday(d, wd) for (d, wd) in theweek)
        return f'<tr>{week}</tr>'

    def formatmonth(self, theyear, themonth, withyear=True):
        self.year, self.month = theyear, themonth
        
        # This is the key change: adding the 'ledger-calendar' class to the table
        cal = f'<table class="ledger-calendar">\n'
        cal += f'{self.formatmonthname(theyear, themonth, withyear)}\n'
        cal += f'{self.formatweekheader()}\n'
        for week in self.monthdays2calendar(theyear, themonth):
            cal += f'{self.formatweek(week)}\n'
        cal += '</table>\n'
        return cal