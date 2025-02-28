# MIREA Schedule Analyzer

## 📌 Описание проекта
Этот сервис анализирует расписание студентов и преподавателей МИРЭА и выявляет неудобные места ("узкие места"), такие как:
- Длинные окна между парами
- Недостаточное время на переход между корпусами
- Конфликты по времени занятий

Данные об ошибках хранятся в **PostgreSQL**, обработка выполняется в **Celery**, а **Redis** используется для управления очередью запросов.

## 🚀 Функциональность
### **1️⃣ Поиск неудобств в расписании**
🔹 Анализируются данные из API МИРЭА `https://schedule-of.mirea.ru/schedule/api/search`  
🔹 Доступны фильтры по **группе** и **преподавателю**
`GET /api/issueslist/?group=ИВБО-01-23&teacher=Иванов%20И.И.`

### **2️⃣ API для работы с данными**
🔹 `GET /api/issueslist/` - получить список проблем в расписании  
🔹 `POST /api/schedule/process/` - запустить фоновую обработку  
🔹 `GET /api/schedule/process/{task_id}/` - проверить статус обработки  

### **3️⃣ Очередь задач**
🔹 Сервис **не выполняет дублирующиеся запросы**  
🔹 Одновременно обрабатывается **только одна задача**, остальные ставятся в очередь  
🔹 Разные запросы (с разными фильтрами) ставятся в очередь отдельно

---

## 📡 API Ответы
### **1️⃣ Получение списка проблем в расписании**
`GET /api/issueslist/`

Пример ответа:
```json
{
    "issues": [
        {
            "id": 1,
            "issue_type": "Окно между парами",
            "description": "Перерыв между занятиями превышает 3 часа",
            "related_event": {
                "summary": "Математика",
                "start_time": "2025-02-28T10:00:00Z",
                "end_time": "2025-02-28T11:30:00Z",
                "location": "Корпус 1, Ауд. 105",
                "teacher": "Иванов И.И.",
                "group": "ИВБО-01-23"
            },
            "related_event_2": {
                "summary": "Физика",
                "start_time": "2025-02-28T15:00:00Z",
                "end_time": "2025-02-28T16:30:00Z",
                "location": "Корпус 2, Ауд. 201",
                "teacher": "Петров П.П.",
                "group": "ИВБО-01-23"
            },
            "last_updated": "2025-02-28T08:00:00Z"
        }
    ]
}
```

### **2️⃣ Запуск фоновой обработки**
`POST /api/schedule/process/`

Пример ответа:
```json
{
    "task_id": "a123b456-c789-d012-e345-f67890abcdef",
    "status": "STARTED",
    "result": []
}
```

### **3️⃣ Проверка статуса задачи**
`GET /api/schedule/process/{task_id}/`

Примеры ответа:
```json
{
    "task_id": "a123b456-c789-d012-e345-f67890abcdef",
    "status": "PENDING",
    "result": []
}
```

```json
{
    "task_id": "a123b456-c789-d012-e345-f67890abcdef",
    "status": "IN QUEUE",
    "result": []
}
```

Пример ответа, если задача завершена:
```json
{
    "task_id": "a123b456-c789-d012-e345-f67890abcdef",
    "status": "SUCCESS",
    "result": [
        {
            "id": 1,
            "issue_type": "Окно между парами",
            "description": "Перерыв между занятиями превышает 3 часа",
            "related_event": {
                "summary": "Математика",
                "start_time": "2025-02-28T10:00:00Z",
                "end_time": "2025-02-28T11:30:00Z",
                "location": "Корпус 1, Ауд. 105",
                "teacher": "Иванов И.И.",
                "group": "ИВБО-01-23"
            },
            "related_event_2": {
                "summary": "Физика",
                "start_time": "2025-02-28T15:00:00Z",
                "end_time": "2025-02-28T16:30:00Z",
                "location": "Корпус 2, Ауд. 201",
                "teacher": "Петров П.П.",
                "group": "ИВБО-01-23"
            }
        }
    ]
}
```

---

## 🛠️ Установка и запуск
### **1️⃣ Клонируйте репозиторий**
```sh
git clone https://github.com/your-repo/mirea-schedule-analyzer.git
cd mirea-schedule-analyzer
```

### **2️⃣ Создайте `.env` файл**
```sh
SECRET_KEY="your-secret-key"
DEBUG=False
DB_NAME=issues_db
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_HOST=db
DB_PORT=5432
CELERY_BROKER_URL=redis://redis:6379/0
```

### **3️⃣ Запустите Docker-контейнеры**
```sh
docker-compose up --build
```

Это поднимет:
- `web` - Django-приложение на `localhost:8000`
- `db` - PostgreSQL для хранения данных
- `redis` - брокер сообщений для Celery
- `celery` - обработчик фоновых задач
- `celery-beat` - планировщик задач

### **4️⃣ Запуск фоновой обработки вручную**
Запустите обработку через API:
```sh
curl -X POST "http://127.0.0.1:8000/api/schedule/process/"
```

Проверка статуса:
```sh
curl -X GET "http://127.0.0.1:8000/api/schedule/process/{task_id}/"
```

---

## 🔧 Основные технологии
- **Django REST Framework** - API-сервер
- **Celery + Redis** - обработка задач в фоне
- **PostgreSQL** - база данных
- **Docker + Docker Compose** - контейнеризация

---


