# ledger/utils.py
from calendar import HTMLCalendar
from django.urls import reverse

class LedgerHTMLCalendar(HTMLCalendar):
    def formatday(self, day, weekday):
        if day == 0:
            return '<td class="noday">&nbsp;</td>'  # day outside month
        else:
            url = reverse('daily_view_date', args=(self.year, self.month, day))
            # Add data attributes for hover functionality
            return f'<td><a href="{url}" data-year="{self.year}" data-month="{self.month}" data-day="{day}" class="calendar-day-link">{day}</a></td>'

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