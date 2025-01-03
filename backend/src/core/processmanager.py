from threading import Thread, Lock
from typing import Callable, List, Dict
from enum import Enum
import time
from queue import PriorityQueue


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Task:
    def __init__(
        self, func: Callable, task_id: str, priority: int = 0, *args, **kwargs
    ):
        self.func = func
        self.task_id = task_id
        self.priority = priority
        self.args = args
        self.kwargs = kwargs
        self.status = TaskStatus.PENDING
        self.error = None
        self.start_time = None
        self.end_time = None

    def __lt__(self, other):
        return self.priority < other.priority


class ProcessManager:
    """
    尚未實裝
    使用:
    pm = ProcessManager()
    pm.add_task(func, task_id, priority, *args, **kwargs)
    pm.get_task_status(task_id)
    pm.get_all_status()
    pm.stop()
    """
    def __init__(self, max_workers: int = 4):
        self.tasks: Dict[str, Task] = {}
        self.task_queue = PriorityQueue()
        self.active_threads: List[Thread] = []
        self.lock = Lock()
        self.max_workers = max_workers
        self.running = True
        self._start_worker()

    def _start_worker(self):
        self.worker_thread = Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()

    def clean_completed_tasks(self) -> None:
        with self.lock:
            completed_tasks = [
                task_id
                for task_id, task in self.tasks.items()
                if task.status == TaskStatus.COMPLETED
            ]
            for task_id in completed_tasks:
                del self.tasks[task_id]

            self.active_threads = [
                thread for thread in self.active_threads if thread.is_alive()
            ]

    def _process_queue(self):
        while self.running:
            if self.get_active_count() < self.max_workers:
                try:
                    task = self.task_queue.get_nowait()
                    if task.status == TaskStatus.PENDING:
                        thread = Thread(
                            target=self.execute_task,
                            args=(task,),
                            name=f"Task-{task.task_id}",
                        )
                        with self.lock:
                            self.active_threads.append(thread)
                        thread.start()
                except:
                    time.sleep(0.1)
                finally:
                    self.clean_completed_tasks()
            time.sleep(0.1)

    def add_task(
        self, func: Callable, task_id: str, priority: int = 0, *args, **kwargs
    ) -> None:
        with self.lock:
            task = Task(func, task_id, priority, *args, **kwargs)
            self.tasks[task_id] = task
            self.task_queue.put(task)

    def execute_task(self, task: Task) -> None:
        try:
            task.status = TaskStatus.RUNNING
            task.start_time = time.time()
            task.func(*task.args, **task.kwargs)
            task.status = TaskStatus.COMPLETED
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
        finally:
            task.end_time = time.time()
            self.clean_completed_tasks()

    def stop(self):
        self.running = False
        self.worker_thread.join()

    def get_active_count(self) -> int:
        return sum(1 for thread in self.active_threads if thread.is_alive())

    def get_task_status(self, task_id: str) -> TaskStatus:
        return self.tasks[task_id].status if task_id in self.tasks else None

    def get_all_status(self) -> Dict[str, Dict]:
        return {
            task_id: {
                "status": task.status.value,
                "error": task.error,
                "duration": task.end_time - task.start_time if task.end_time else None,
            }
            for task_id, task in self.tasks.items()
        }