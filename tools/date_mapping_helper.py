import json
import sqlite3
import pprint
import re
from itertools import cycle

pp = pprint.PrettyPrinter(indent=4)
weekday_map = {
    0: 'Mon',
    1: 'Tue',
    2: 'Wed',
    3: 'Thurs',
    4: 'Fri',
    5: 'Sat',
    6: 'Sun',
    }
map_week = {v: k for k, v in weekday_map.items()}
weekday_cycle = cycle(weekday_map.values())

def get_hour(hour_int, am_or_pm):
  if hour_int == 12:
    return 0 if am_or_pm == 'am' else 12
  else:
    return hour_int + 12 if am_or_pm == 'pm' else hour_int

def try_to_parse_date(dates):
  results = {}
  for date_range in dates:
    # Splittin'
    date_parts = re.split(' \: |\: | \:', date_range)
    if len(date_parts) != 2:
      print("Couldn't split date range from time range (" + date_range + ").")
      return None
    weekday_range = re.split(' - |- | -', date_parts[0])
    # Make sure we split the weekday range apart.
    if len(weekday_range) != 2:
      weekday_range = re.split(u' \u2013 | \u2013|\u2013 ', date_parts[0], re.UNICODE)
      if len(weekday_range) != 2:
        weekday_pair = re.split(' \& |\& | \&|', date_parts[0])
        if len(weekday_pair) != 2:
          if date_parts[0] in weekday_map.values():
            weekday_range = [date_parts[0], date_parts[0]]
          else:
            print("Couldn't split weekday range (" + date_parts[0] + ").")
            return None
        else:
          weekday_range = [weekday_pair[0], weekday_pair[1]]

    for idx, value in enumerate(weekday_range):
      if value == 'Tues':
        weekday_range[idx] = 'Tue'

    # Make sure these are understood dates.
    for weekday in weekday_range:
      if weekday not in weekday_map.values():
        print(weekday + " not in weekday values.")
        return None

    # Cycle to the right date.
    current_weekday = next(weekday_cycle)
    while current_weekday != weekday_range[0]:
      current_weekday = next(weekday_cycle)

    # Get the time range.
    time_range = re.split(' - | -|- ', date_parts[1])
    if len(time_range) != 2:
      time_range = re.split(u' \u2013 | \u2013|\u2013 ', date_parts[1], re.UNICODE)
      if len(time_range) != 2:
        print("Could not split time range (" + date_parts[1] + ").")
        return None
    start_am_or_pm = time_range[0][-2:]
    if start_am_or_pm not in ['am', 'pm']:
      print ("Could not get AM or PM from start time (" + time_range[0][-2:] + ").")
      return None
    end_am_or_pm = time_range[1][-2:]
    if end_am_or_pm not in ['am', 'pm']:
      print ("Could not get AM or PM from end time (" + time_range[1][-2:] + ").")
      return None

    try:
      start_time = time_range[0][:-2].split(':')
      end_time = time_range[1][:-2].split(':')
      while current_weekday != weekday_range[1]:
        results[map_week[current_weekday]] = [
          {
            'start_time': {
              'h': get_hour(int(start_time[0]), start_am_or_pm),
              'm': int(start_time[1] if 1 in start_time else 0),
            },
            'end_time': {
              'h': get_hour(int(end_time[0]), end_am_or_pm),
              'm': int(end_time[1] if 1 in end_time else 0),
            },
          }
        ]
        current_weekday = next(weekday_cycle)
      results[map_week[current_weekday]] = [
        {
          'start_time': {
            'h': get_hour(int(start_time[0]), start_am_or_pm),
            'm': int(start_time[1] if 1 in start_time else 0),
          },
          'end_time': {
            'h': get_hour(int(end_time[0]), end_am_or_pm),
            'm': int(end_time[1] if 1 in end_time else 0),
          },
        }
      ]
    except (UnicodeEncodeError, ValueError):
      print ("Some weird time formatting going on ...")
      return None

  return results

db = sqlite3.connect('/Users/DTM-2/gits/qadan.github.io/pytools/garnish/garnish.db')
cur = db.cursor()
cur.execute('select id, hours_of_operation from restaurants')
print('Times are in format "9:30 am" or "2:00 pm"')
results = {}
try:
  for row in cur:
    result = try_to_parse_date(json.loads(row[1]))
    if not result:
      print("Manual entry for row " + str(row[0]))
      pp.pprint(json.loads(row[1]))
      result = {}
      time_ranges = []
      for dateint, weekday in weekday_map.iteritems():
        is_closed = raw_input('Closed on ' + weekday + '(y/N)? ')
        if is_closed:
          result[dateint] = None
        else:
          if time_ranges:
            different = raw_input('Different from previous day with time ranges (y/N)? ')
            if not different:
              result[dateint] = time_ranges
              continue
            else:
              time_ranges = []

          num_ranges = raw_input('Number of time ranges for this day (default: 1): ') or 1
          got_num = False
          while not got_num:
            try:
              num_ranges = int(num_ranges)
              got_num = True
            except ValueError:
              num_ranges = raw_input('Invalid number of time ranges. Please enter a numer of time ranges for this day (default: 1): ') or 1

          for n in range(0, int(num_ranges)):
            start_bits = raw_input('Time of opening: ').split(' ')
            end_bits = raw_input('Time of closing: ').split(' ')
            start_time = start_bits[0].split(':')
            end_time = end_bits[0].split(':')
            time_range = {
              'start_time': {
                'h': get_hour(int(start_time[0]), start_bits[1]),
                'm': int(start_time[1] if 1 in start_time else 0),
                },
              'end_time': {
                'h': get_hour(int(end_time[0]), end_bits[1]),
                'm': int(end_time[1] if 1 in end_time else 0),
                },
              }
            time_ranges.append(time_range)
          result[dateint] = time_ranges

    results[row[0]] = result

  with open('backup.json', 'w') as backup:
    backup.write(json.dumps(results))

  for restaurant_id, result in results.iteritems():
    cur.execute('update restaurants set hours_table = ? where id = ?', [json.dumps(result), restaurant_id])

  db.commit()
  cur.close()
except KeyboardInterrupt:
  pp.pprint(results)
