---
name: date-with-lunar
description: Provides current date information including both Gregorian and Chinese lunar calendar. Use when user asks about today's date, current date, or what day it is.
license: MIT
metadata:
  author: custom
  version: "1.0"
---

# Date with Lunar Calendar Skill

This skill provides comprehensive date information including both the Gregorian calendar and Chinese lunar calendar (农历).

## When to Use

Activate this skill when the user asks questions like:
- "今天几号？" / "What's today's date?"
- "今天是什么日期？" / "What is the date today?"
- "现在是几月几号？" / "What's the current date?"
- Any question about the current date

## Instructions

1. Get the current Gregorian date (you already have this from system context)
2. Run the lunar calendar calculation script to get the corresponding lunar date
3. Format the response to include both calendars in a clear, readable format

## Usage

Run the Python script to calculate the lunar calendar:

```bash
python .claude/skills/date-with-lunar/scripts/lunar_calendar.py YYYY-MM-DD
```

The script will output the lunar calendar information in JSON format.

## Response Format

When responding to date queries, include:

1. **Gregorian Date**: Full date with day of week
2. **Lunar Date**: Chinese lunar calendar with year (天干地支), month, and day
3. **Optional**: Any relevant traditional festivals or solar terms if applicable

### Example Response

```
今天是 2026年2月5日 星期四

农历：乙巳年（蛇年）腊月十八
```

## Notes

- The lunar calendar calculation uses the Chinese lunisolar calendar system
- Lunar months can be 29 or 30 days
- Leap months (闰月) occur approximately every 2-3 years
- The script handles all edge cases including leap months and year transitions
