from datetime import datetime, date
from pydantic import BaseModel
from enum import Enum
import uuid
from taskw import TaskWarrior

from docker_names import get_random_name
from .settings import Settings
settings = Settings()

class Task(BaseModel):
    """a typed taskwarrior object"""
    description: str
    entry: datetime
    modified: datetime | None = None
    status: Enum('pending', 'completed', 'deleted', 'waiting', 'recurring', 'recurring-paused', 'deferred',)
    tags: list[str] = []
    uuid: str
    points: int
    partial_group: uuid.UUID | None = None
    block_id: "uuid.UUID" | None = None
    block: str | None = None

    @classmethod
    def get_tasks(cls, oversize_strategy:Enum("break_up","ignore",)="break_up") -> list["Task"]:
        """get all the tasks from taskwarrior"""
        tw = TaskWarrior()
        tasks = tw.load_tasks(command="pending")
        if oversize_strategy == "break_up":
            cls.break_up_oversized_tasks()
        ordered = sorted(tasks, key=lambda x: (x["partial_group"], x["urgency"], x["points"],), reverse=True)
        return [cls(**t) for t in ordered if t["points"] <= settings.big_max_points]

    @classmethod
    def break_up_oversized_tasks(cls) -> None:
        tw = TaskWarrior()
        tasks = tw.load_tasks(command="pending")
        oversized = [t for t in tasks if t["points"] > settings.big_max_points]
        for task in oversized:
            count = task["points"] // settings.big_max_points
            partial_group = str(uuid.uuid4())
            tw = TaskWarrior()
            for _ in range(count):
                tw.add_task(description=task["description"],
                            entry=task["entry"],
                            status="pending",
                            tags=task["tags"],
                            partial_group=partial_group,
                            points=settings.big_max_points)
            tw.execute_command(f"task {task['uuid']} modify points:{settings.big_max_points} partial_group:{partial_group}")


class Block(BaseModel):
    """Represents a Work Block, or solid set of time to work one or more tasks.
    """
    id: uuid.UUID = uuid.uuid4()
    index: int
    name: str | None = None
    start: datetime
    end: datetime
    duration: int
    size: Enum('big', 'medium','small',)
    max_points: int
    break_size: int
    tasks: list[Task]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = f"{self.index}-{get_random_name()}"

    @property
    def available_points(self) -> int:
        """the number of points available in this block"""
        return self.max_points - sum([t.points for t in self.tasks])

    def add_task(self, task:Task)-> None:
        """add a task to this block"""
        task.block = self.name
        task.block_id = self.id
        self.tasks.append(task)

class BigBlock(Block):
    """A Big Block is a Work Block that is 80 minutes long with a 17 minute break"""
    size = 'big'
    duration = settings.big_block_size
    max_points = settings.big_max_points
    break_size = settings.big_break_size

class MediumBlock(Block):
    """A Medium Block is a Work Block that is 50 minutes long with a 17 minute break"""
    size = 'medium'
    duration = settings.medium_block_size
    max_points = settings.medium_max_points
    break_size = settings.medium_break_size

class SmallBlock(Block):
    """A Small Block is a Work Block that is 25 minutes long with a 10 minute break"""
    size = 'small'
    duration = settings.small_block_size
    max_points = settings.small_max_points
    break_size = settings.small_break_size

class Day(BaseModel):
    """A Day is a collection of Work Blocks"""
    date: date
    blocks: list[Block]
    start_time: datetime
    end_time: datetime

    def __init__(self, day: date|str = date.today()):
        super().__init__()
        try:
            self.date = date.fromisoformat(day)
        except ValueError:
            self.date = day
        settings = Settings()
        self.start_time = datetime.combine(self.date, settings.start_time)
        self.end_time = datetime.combine(self.date, settings.end_time)
        self.blocks = sorted(self.blocks, key=lambda x: x.start)

        def next_block(self, block: Block) -> Block | None:
            """get the next block or none if it is the last block"""
            try:
                return self.blocks[block.index+1]
            except IndexError:
                return None

        def most_space_available_block(self)-> Block | None:
            """Returns the block with the most space that is not full or None if all are full"""
            most_space = self.blocks[0]
            for block in self.blocks:
                if block.available_points > most_space.available_points:
                    most_space = block
            if most_space.available_points:
                return most_space
            return None
