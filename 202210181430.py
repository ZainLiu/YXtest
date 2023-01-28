import datetime
from dateutil.relativedelta import relativedelta

now = datetime.date(month=1, year=2022, day=31)
next_month = now + relativedelta(months=+1)
print(next_month, type(next_month))
