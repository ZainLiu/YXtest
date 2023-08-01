import datetime


def check_data(month_seq: int, now: datetime.date, start_date: datetime.date) -> bool:
    """
    检测是否触发维保计划
    :param month_seq: 月份间隔，3个月表示季度， 6个月表示半年，12个月便是年度
    :param now: 当前日期
    :param start_date: 开始日期
    :return:
    """

    if now < start_date:
        if ((now.month + 1) % 12) == start_date.month and (start_date.year - now.year) <= 1:
            return True
        else:
            return False
    else:
        if (((now.year - start_date.year) * 12 + now.month + 1) - start_date.month) % month_seq == 0:
            return True
        else:
            return False


if __name__ == '__main__':
    now = datetime.date(month=9, year=2022, day=25)
    start_date = datetime.date(month=11, year=2022, day=1)
    month_seq = 1
    print(check_data(month_seq, now, start_date))
