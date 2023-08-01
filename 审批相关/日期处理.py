import datetime
import time

a = datetime.datetime.now()

b = datetime.datetime.now() + datetime.timedelta(hours=1, seconds=9)
print((b - a).seconds)
print((b - a).days)


def get_time_duration_str(datatime_timedelta):
    days = datatime_timedelta.days
    total_second = time.seconds
    hours = total_second // 3600
    total_second -= hours * 3600
    mins = total_second // 60
    seconds = total_second - mins * 60

    return f"{days}天{hours}小时{mins}分钟{seconds}秒"


print(get_time_duration_str(b - a))
