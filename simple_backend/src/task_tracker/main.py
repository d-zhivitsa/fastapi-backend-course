from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import json

app = FastAPI()


class Task(BaseModel):
    id: int  # Уникальный идентификатор
    name: str  # Название
    status: str  # Статус

# Класс для работы с задачами, сохранёнными в файле
class TaskManager:
    def __init__(self, file_path: str):
        self.file_path = file_path  # Путь к файлу для хранения задач
        self.tasks = self.load_tasks()  # Загружаем задачи при старте программы

    def load_tasks(self) -> Dict[int, Task]:
        """Загружает задачи из файла и возвращает их как словарь {id: Task}."""
        try:
            with open(self.file_path, "r") as file:
                tasks_data = json.load(file)
                return {task["id"]: Task(**task) for task in tasks_data}
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_tasks(self):
        """Сохраняет задачи в файл."""
        with open(self.file_path, "w") as file:
            json.dump([{"id": task.id, "name": task.name, "status": task.status} for task in self.tasks.values()], file, sort_keys=True)

    def get_tasks(self) -> List[Task]:
        """Возвращает список всех задач."""
        return sorted(list(self.tasks.values()), key=lambda task: task.id)

    def add_task(self, task: Task):
        """Добавляет новую задачу, если её ID уникален."""
        if task.id in self.tasks:
            raise HTTPException(status_code=400, detail="Задача с таким ID уже существует")
        self.tasks[task.id] = task
        self.save_tasks()

    def update_task_status(self, task_id: int):
        """Обновляет статус задачи на 'updated' по её ID."""
        if task_id in self.tasks:
            self.tasks[task_id].status = "updated"
            self.save_tasks()
        else:
            raise HTTPException(status_code=404, detail="Задача не найдена")

    def delete_task(self, task_id: int):
        """Удаляет задачу по её ID."""
        if task_id in self.tasks:
            del self.tasks[task_id]
            self.save_tasks()
        else:
            raise HTTPException(status_code=404, detail="Задача не найдена")

# Создаём объект TaskManager, который будет работать с файлом "tasks.json"
task_manager = TaskManager("tasks.json")

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
