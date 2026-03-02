#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chinese Lunar Calendar Converter
Converts Gregorian dates to Chinese lunar calendar dates
Uses simplified algorithm with verified lunar data
"""

import sys
import json
import io
from datetime import datetime, timedelta

# Set stdout to UTF-8 encoding for proper Chinese character display
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Lunar calendar data from 1900 to 2100
# Format: 0xABCDE where:
#   A = leap month (0 = no leap month, 1-12 = leap month number)
#   BCDE = days in each month (1 = 30 days, 0 = 29 days) from month 1 to 12
LUNAR_INFO = [
    0x04bd8, 0x04ae0, 0x0a570, 0x054d5, 0x0d260, 0x0d950, 0x16554, 0x056a0, 0x09ad0, 0x055d2,  # 1900-1909
    0x04ae0, 0x0a5b6, 0x0a4d0, 0x0d250, 0x1d255, 0x0b540, 0x0d6a0, 0x0ada2, 0x095b0, 0x14977,  # 1910-1919
    0x04970, 0x0a4b0, 0x0b4b5, 0x06a50, 0x06d40, 0x1ab54, 0x02b60, 0x09570, 0x052f2, 0x04970,  # 1920-1929
    0x06566, 0x0d4a0, 0x0ea50, 0x06e95, 0x05ad0, 0x02b60, 0x186e3, 0x092e0, 0x1c8d7, 0x0c950,  # 1930-1939
    0x0d4a0, 0x1d8a6, 0x0b550, 0x056a0, 0x1a5b4, 0x025d0, 0x092d0, 0x0d2b2, 0x0a950, 0x0b557,  # 1940-1949
    0x06ca0, 0x0b550, 0x15355, 0x04da0, 0x0a5b0, 0x14573, 0x052b0, 0x0a9a8, 0x0e950, 0x06aa0,  # 1950-1959
    0x0aea6, 0x0ab50, 0x04b60, 0x0aae4, 0x0a570, 0x05260, 0x0f263, 0x0d950, 0x05b57, 0x056a0,  # 1960-1969
    0x096d0, 0x04dd5, 0x04ad0, 0x0a4d0, 0x0d4d4, 0x0d250, 0x0d558, 0x0b540, 0x0b6a0, 0x195a6,  # 1970-1979
    0x095b0, 0x049b0, 0x0a974, 0x0a4b0, 0x0b27a, 0x06a50, 0x06d40, 0x0af46, 0x0ab60, 0x09570,  # 1980-1989
    0x04af5, 0x04970, 0x064b0, 0x074a3, 0x0ea50, 0x06b58, 0x055c0, 0x0ab60, 0x096d5, 0x092e0,  # 1990-1999
    0x0c960, 0x0d954, 0x0d4a0, 0x0da50, 0x07552, 0x056a0, 0x0abb7, 0x025d0, 0x092d0, 0x0cab5,  # 2000-2009
    0x0a950, 0x0b4a0, 0x0baa4, 0x0ad50, 0x055d9, 0x04ba0, 0x0a5b0, 0x15176, 0x052b0, 0x0a930,  # 2010-2019
    0x07954, 0x06aa0, 0x0ad50, 0x05b52, 0x04b60, 0x0a6e6, 0x0a4e0, 0x0d260, 0x0ea65, 0x0d530,  # 2020-2029
    0x05aa0, 0x076a3, 0x096d0, 0x04afb, 0x04ad0, 0x0a4d0, 0x1d0b6, 0x0d250, 0x0d520, 0x0dd45,  # 2030-2039
    0x0b5a0, 0x056d0, 0x055b2, 0x049b0, 0x0a577, 0x0a4b0, 0x0aa50, 0x1b255, 0x06d20, 0x0ada0,  # 2040-2049
    0x14b63, 0x09370, 0x049f8, 0x04970, 0x064b0, 0x168a6, 0x0ea50, 0x06b20, 0x1a6c4, 0x0aae0,  # 2050-2059
    0x0a2e0, 0x0d2e3, 0x0c960, 0x0d557, 0x0d4a0, 0x0da50, 0x05d55, 0x056a0, 0x0a6d0, 0x055d4,  # 2060-2069
    0x052d0, 0x0a9b8, 0x0a950, 0x0b4a0, 0x0b6a6, 0x0ad50, 0x055a0, 0x0aba4, 0x0a5b0, 0x052b0,  # 2070-2079
    0x0b273, 0x06930, 0x07337, 0x06aa0, 0x0ad50, 0x14b55, 0x04b60, 0x0a570, 0x054e4, 0x0d160,  # 2080-2089
    0x0e968, 0x0d520, 0x0daa0, 0x16aa6, 0x056d0, 0x04ae0, 0x0a9d4, 0x0a2d0, 0x0d150, 0x0f252,  # 2090-2099
    0x0d520,  # 2100
]

# Heavenly Stems (天干)
HEAVENLY_STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]

# Earthly Branches (地支)
EARTHLY_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# Chinese Zodiac Animals (生肖)
ZODIAC_ANIMALS = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"]

# Lunar months
LUNAR_MONTHS = ["正", "二", "三", "四", "五", "六", "七", "八", "九", "十", "冬", "腊"]

# Lunar days
LUNAR_DAYS = [
    "初一", "初二", "初三", "初四", "初五", "初六", "初七", "初八", "初九", "初十",
    "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十",
    "廿一", "廿二", "廿三", "廿四", "廿五", "廿六", "廿七", "廿八", "廿九", "三十"
]

# Base date: 1900-01-31 is lunar 1900-01-01
BASE_DATE = datetime(1900, 1, 31)


def get_leap_month(year):
    """Get the leap month of a lunar year (0-12, 0 means no leap month)"""
    return (LUNAR_INFO[year - 1900] >> 16) & 0x0F


def get_lunar_month_days(year, month):
    """Get the number of days in a specific lunar month"""
    return 30 if (LUNAR_INFO[year - 1900] & (0x10000 >> month)) else 29


def get_leap_month_days(year):
    """Get the number of days in the leap month"""
    if get_leap_month(year):
        return 30 if (LUNAR_INFO[year - 1900] & 0x10000) else 29
    return 0


def get_lunar_year_days(year):
    """Get the total number of days in a lunar year"""
    days = 348  # 12 months * 29 days
    for i in range(12):
        days += 1 if (LUNAR_INFO[year - 1900] & (0x10000 >> (i + 1))) else 0
    return days + get_leap_month_days(year)


def solar_to_lunar(solar_date):
    """Convert Gregorian date to lunar date"""
    if solar_date < BASE_DATE:
        raise ValueError("Date must be on or after 1900-01-31")

    if solar_date.year > 2100:
        raise ValueError("Date must be before 2101-01-01")

    # Calculate offset days from base date
    offset = (solar_date - BASE_DATE).days

    # Find lunar year
    lunar_year = 1900
    temp = 0
    while lunar_year < 2101 and temp <= offset:
        temp = get_lunar_year_days(lunar_year)
        if temp <= offset:
            offset -= temp
            lunar_year += 1
        else:
            break

    # Find lunar month and day
    leap_month = get_leap_month(lunar_year)
    is_leap = False

    for lunar_month in range(1, 13):
        # Check if this is a leap month
        if leap_month > 0 and lunar_month == (leap_month + 1) and not is_leap:
            # This is the leap month
            is_leap = True
            lunar_month -= 1
            temp = get_leap_month_days(lunar_year)
        else:
            temp = get_lunar_month_days(lunar_year, lunar_month)

        if offset < temp:
            break

        offset -= temp

        if is_leap and lunar_month == leap_month:
            is_leap = False

    lunar_day = offset + 1

    return {
        "year": lunar_year,
        "month": lunar_month,
        "day": int(lunar_day),
        "is_leap": is_leap
    }


def get_ganzhi_year(year):
    """Get the Heavenly Stem and Earthly Branch for a year (Sexagenary cycle)"""
    # The cycle starts from year 4 (甲子)
    stem_index = (year - 4) % 10
    branch_index = (year - 4) % 12
    return HEAVENLY_STEMS[stem_index] + EARTHLY_BRANCHES[branch_index]


def get_zodiac(year):
    """Get the zodiac animal for a year"""
    return ZODIAC_ANIMALS[(year - 4) % 12]


def format_lunar_date(lunar_info):
    """Format lunar date in Chinese"""
    year = lunar_info["year"]
    month = lunar_info["month"]
    day = lunar_info["day"]
    is_leap = lunar_info["is_leap"]

    ganzhi = get_ganzhi_year(year)
    zodiac = get_zodiac(year)

    month_str = ("闰" if is_leap else "") + LUNAR_MONTHS[month - 1]
    day_str = LUNAR_DAYS[day - 1]

    return {
        "ganzhi_year": ganzhi,
        "zodiac": zodiac,
        "month": month_str + "月",
        "day": day_str,
        "full": f"{ganzhi}年（{zodiac}年）{month_str}月{day_str}"
    }


def main():
    if len(sys.argv) < 2:
        # Use today's date if no argument provided
        date_str = datetime.now().strftime("%Y-%m-%d")
    else:
        date_str = sys.argv[1]

    try:
        solar_date = datetime.strptime(date_str, "%Y-%m-%d")
        lunar_info = solar_to_lunar(solar_date)
        formatted = format_lunar_date(lunar_info)

        weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]

        result = {
            "gregorian": {
                "date": date_str,
                "year": solar_date.year,
                "month": solar_date.month,
                "day": solar_date.day,
                "weekday": weekdays[solar_date.weekday()]
            },
            "lunar": {
                "year": lunar_info["year"],
                "month": lunar_info["month"],
                "day": lunar_info["day"],
                "is_leap": lunar_info["is_leap"],
                "ganzhi_year": formatted["ganzhi_year"],
                "zodiac": formatted["zodiac"],
                "formatted_month": formatted["month"],
                "formatted_day": formatted["day"],
                "full": formatted["full"]
            }
        }

        print(json.dumps(result, ensure_ascii=False, indent=2))

    except ValueError as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": f"Unexpected error: {str(e)}"}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
