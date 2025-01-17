from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import requests

app = FastAPI()

class Task(BaseModel):
    id: int  # Уникальный идентификатор
    name: str  # Название
    status: str  # Статус

class TaskManager:
    def __init__(self, base_url: str, api_key: str, bin_id: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.bin_id = bin_id
        self.headers = {"X-Master-Key": self.api_key, "Content-Type": "application/json"}

    def load_tasks(self) -> List[Task]:
        """Загружает задачи из jsonbin.io."""
        url = f"{self.base_url}/b/{self.bin_id}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            try:
                data = response.json()
                return [Task(**task) for task in data.get("record", {}).get("tasks", [])]
            except Exception:
                raise HTTPException(status_code=500, detail="Ошибка обработки данных из хранилища.")
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)

    def save_tasks(self, tasks: List[Task]):
        """Сохраняет задачи в jsonbin.io."""
        url = f"{self.base_url}/b/{self.bin_id}"
        data = {"tasks": [task.dict() for task in tasks]}
        response = requests.put(url, headers=self.headers, json=data)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

    def get_tasks(self) -> List[Task]:
        """Возвращает список всех задач."""
        return self.load_tasks()

    def add_task(self, task: Task):
        """Добавляет новую задачу, если её ID уникален."""
        tasks = self.load_tasks()
        if any(t.id == task.id for t in tasks):
            raise HTTPException(status_code=400, detail="Задача с таким ID уже существует")
        tasks.append(task)
        self.save_tasks(tasks)

    def update_task_status(self, task_id: int):
        """Обновляет статус задачи на 'updated' по её ID."""
        tasks = self.load_tasks()
        for task in tasks:
            if task.id == task_id:
                task.status = "updated"
                self.save_tasks(tasks)
                return
        raise HTTPException(status_code=404, detail="Задача не найдена")

    def delete_task(self, task_id: int):
        """Удаляет задачу по её ID."""
        tasks = self.load_tasks()
        tasks = [task for task in tasks if task.id != task_id]
        if len(tasks) == len(self.load_tasks()):
            raise HTTPException(status_code=404, detail="Задача не найдена")
        self.save_tasks(tasks)

# Настраиваем параметры jsonbin.io
BASE_URL = "https://api.jsonbin.io/v3"
API_KEY = "$2a$10$JKwnSYVa3.z22z6TR74SF.iXgFgPbaL2Fkn3d2wA167LfmGGAw.s6"  # ключ API
BIN_ID = "678a5e7ae41b4d34e478e10d"  # bin ID

# Создаём объект TaskManager для работы с jsonbin.io
task_manager = TaskManager(BASE_URL, API_KEY, BIN_ID)

# Маршрут для получения всех задач
@app.get("/tasks")
def get_tasks():
    """Возвращает список всех задач."""
    return task_manager.get_tasks()

# Маршрут для создания новой задачи
@app.post("/tasks")
def create_task(task: Task):
    """Создаёт новую задачу."""
    task_manager.add_task(task)
    return task

# Маршрут для обновления статуса задачи
@app.put("/tasks/{task_id}")
def update_task(task_id: int):
    """Обновляет статус задачи на 'updated'."""
    task_manager.update_task_status(task_id)
    return {"message": "Статус задачи обновлён на 'updated'"}

# Маршрут для удаления задачи
@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    """Удаляет задачу по её ID."""
    task_manager.delete_task(task_id)
    return {"message": "Задача успешно удалена"}
