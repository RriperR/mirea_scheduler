import requests
from icalendar import Calendar, vText


class ScheduleService:
    """Класс для работы с API расписания МИРЭА"""

    API_URL = "https://schedule-of.mirea.ru/schedule/api/search"

    @classmethod
    def fetch_schedule(cls):
        """Получает список групп и ссылки на расписание (постранично)"""
        all_data = []
        next_page_token = None

        while True:
            # Формируем URL с токеном страницы (если есть)
            params = {"pageToken": next_page_token} if next_page_token else {}
            response = requests.get(cls.API_URL, params=params)
            response.raise_for_status()

            data = response.json()
            all_data.extend(data["data"])  # Добавляем данные

            # Проверяем, есть ли следующая страница
            next_page_token = data.get("nextPageToken")
            if not next_page_token:
                break  # Если страниц больше нет, выходим

        return all_data

    @classmethod
    def fetch_ical(cls, ical_url):
        """Загружает и парсит iCalendar файл"""
        response = requests.get(ical_url + "?includeMeta=true")
        response.raise_for_status()
        return cls.parse_ical(response.text)

    @staticmethod
    def parse_ical(ical_data):
        """Разбирает iCalendar (.ics) и возвращает список только с парами"""
        calendar = Calendar.from_ical(ical_data)
        events = []

        for component in calendar.walk():
            if component.name == "VEVENT":  # Берём только события (пары и мета-инфу)
                event = {
                    "summary": str(component.get("SUMMARY", "")),  # Название предмета
                    "start": component.get("DTSTART").dt,  # Время начала
                    "end": component.get("DTEND").dt,  # Время окончания
                    "location": str(component.get("LOCATION", "")),  # Аудитория
                    "teacher": str(component.get("X-META-TEACHER", "")),  # Преподаватель
                    "group": str(component.get("X-META-GROUP", "")),  # Группа
                    "discipline": str(component.get("X-META-DISCIPLINE", "")),  # Дисциплина
                }

                # Декодируем vText
                for key in event:
                    if isinstance(event[key], vText):
                        event[key] = event[key].to_ical().decode("utf-8")

                # Фильтруем события: оставляем только занятия с X-META-DISCIPLINE
                if event["discipline"]:
                    events.append(event)

        return events
