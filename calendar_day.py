import calendar

date_input = input("Enter date (MM DD YYYY): ")

month, day, year = map(int, date_input.split())

day_number = calendar.weekday(year, month, day)

day_name = calendar.day_name[day_number].upper()

print(day_name)
