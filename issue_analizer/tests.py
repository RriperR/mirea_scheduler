import requests

url = "https://schedule-of.mirea.ru/schedule/api/search"
response = requests.get(url)
response.raise_for_status()
schedules = response.json()["data"]

events = []
for schedule in schedules:
    ical_url = schedule["iCalLink"] + "?includeMeta=true"
    ical_data = requests.get(ical_url).text
    print(ical_data)

    #parsed_events = parse_ical(ical_data, schedule["iCalLink"])
    #events.extend(parsed_events)
    break

#
# def parse_ical(self, ical_data, schedule_url):
#     """ Парсит iCalendar (ICS) и извлекает события """
#     from icalendar import Calendar
#
#     calendar = Calendar.from_ical(ical_data)
#     events = []
#
#     for component in calendar.walk():
#         if component.name == "VEVENT":
#             start = parse_datetime(str(component.get("DTSTART").dt))
#             end = parse_datetime(str(component.get("DTEND").dt))
#             location = component.get("LOCATION", "Неизвестно")
#
#             events.append({
#                 "start": start,
#                 "end": end,
#                 "location": location,
#                 "url": schedule_url
#             })
#
#     return events