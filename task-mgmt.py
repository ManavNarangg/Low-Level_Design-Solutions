import uuid
from enum import Enum
from abc import ABC, abstractmethod
from threading import Lock
from typing import Dict, List, Set

class Priority(ENUM):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class User:
    def __init__(self, name: str):
        self._id = uuid.uuid4()
        self.name = name

class ActivityLog:
    def __init__(self, task_id: int, actor_id: int, description: str, created_at: date):
        self.task_id = task_id
        self.author_id = author_id
        self.description = description
        self.created_at = created_at

class Task:
    def __init__(self, title: str, description: str, user_id: int, priority: Priority, asignee_id: Optional[int]):
        self.task_id = uuid.uuid4()
        self.title = title
        self.description = description
        self.user_id = user_id
        self.priority = priority
        self.asignee_id = asignee_id
        self.state: TaskState = field(default_factory=TodoState) 
        self.comments: list[Comment] = []

    @property
    def status(self) -> str:
        self.status.name

    def start(self):
        self.state.start(self)

    def complete(self):
        self.state.complete(self)


class TaskState(ABC):
    @abstractmethod
    def start_task(self, task: Task):
        pass

    @abstractmethod
    def complete_task(self, task: Task):
        pass

class TodoState(TaskState):
    def start_task(self, task: Task):
        task.set_state(InProgressState())

    def complete_task(self, task: Task):
        print("Can't mark it as completed")

class InProgressState(TaskState):
    def start_task(self, task: Task):
        print("Can't mark it as started")
    
    def compete_task(self, task: Task):
        task.set_state(CompletedState())

class CompletedState(TaskState):
    def start_task(self, task: Task):
        print("Task is already completed")

    def complete_task(self, task: Task):
        print("Task is already completed")

class TaskList:
    def __init__(self, name: str):
        self.list_id = uuid.uuid4()
        self.name = name
        self.member_ids: set[int] = field(default_factory = set)
        self.task_ids: set[int] = field(default_factory = set)

    def add_members(self, user_id: int) -> None:
        if user_id in self.member_ids:
            raise ValueError("Member already exists")
        self.member_ids.add(user_id)

    def add_tasks(self, task_id: int) -> None:
        if task_id in self.task_ids:
            raise ValueError("Taks already exists")
        self.task_ids.add(task_id)

    def remove_task(self, task_id: int) -> None:
        if task_id not in self.task_ids:
            raise ValueError("Taks doesnt exist")
        self.task_ids.remove(task_id)
        

class TaskService:
    def __init__(self):
        self.tasks: dict[int, Task] = {}
        self.users: dict[int, User] = {}
        self.activities: list[Activity] = []
        # self.observers: List[] = [] 
