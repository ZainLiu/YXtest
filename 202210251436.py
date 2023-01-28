import datetime
date_one = datetime.datetime.now()
date_two = date_one + datetime.timedelta(minutes=5)
print((date_two-date_one).seconds/60)