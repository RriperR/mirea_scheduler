from collections import defaultdict
from datetime import timedelta

class ScheduleAnalyzer:
    """Анализирует расписание на окна и сложные переходы"""

    MIN_TIME_TO_TRAVEL = timedelta(minutes=10)

    @staticmethod
    def find_issues(events):
        """Ищет неудобства в расписании с учётом групп и дней"""
        issues = []

        # Группируем по группе и дню
        events_by_group_day = defaultdict(lambda: defaultdict(list))
        for event in events:
            group = event["group"]
            day = event["start"].date()
            events_by_group_day[group][day].append(event)

        # Перебираем группы и их расписание
        for group, days in events_by_group_day.items():
            for day, day_events in days.items():
                # Сортируем занятия внутри дня по времени начала
                day_events.sort(key=lambda e: e["start"])

                for i in range(len(day_events) - 1):
                    event_1 = day_events[i]
                    event_2 = day_events[i + 1]

                    end_prev = event_1["end"]
                    start_next = event_2["start"]

                    location_prev, location_next = event_1["location"], event_2["location"]
                    gap = start_next - end_prev

                    # Проверяем длинные окна (больше 2 часов)
                    if gap > timedelta(hours=2):
                        issues.append({
                            "category": "Длинное окно",
                            "summary": event_1["summary"],
                            "start": event_1["start"],
                            "end": event_1["end"],
                            "location": event_1["location"],
                            "teacher": event_1["teacher"],
                            "group": event_1["group"],
                            "discipline": event_1["discipline"],

                            # 🔹 Теперь добавляем информацию про второе событие
                            "related_summary_2": event_2["summary"],
                            "related_start_2": event_2["start"],
                            "related_end_2": event_2["end"],
                            "related_location_2": event_2["location"],
                            "related_teacher_2": event_2["teacher"],
                            "related_group_2": event_2["group"],
                            "related_discipline_2": event_2["discipline"],

                            "description": f"Окно между занятиями: {gap}"
                        })

                    # Проверяем невозможные переходы между корпусами
                    if location_prev != location_next and gap < ScheduleAnalyzer.MIN_TIME_TO_TRAVEL:
                        issues.append({
                            "category": "Невозможный переход",
                            "summary": event_1["summary"],
                            "start": event_1["start"],
                            "end": event_1["end"],
                            "location": event_1["location"],
                            "teacher": event_1["teacher"],
                            "group": event_1["group"],
                            "discipline": event_1["discipline"],

                            # 🔹 Теперь добавляем второе событие, куда нужно успеть
                            "related_summary_2": event_2["summary"],
                            "related_start_2": event_2["start"],
                            "related_end_2": event_2["end"],
                            "related_location_2": event_2["location"],
                            "related_teacher_2": event_2["teacher"],
                            "related_group_2": event_2["group"],
                            "related_discipline_2": event_2["discipline"],

                            "description": f"Невозможно успеть из {location_prev} в {location_next} за {gap}."
                        })

        return issues
