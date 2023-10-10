from datetime import datetime, date
from logging import getLogger

from models import Block, SmallBlock, MediumBlock, BigBlock, Block, Task, Day
from ingester import GoogleCalendarIngester
from settings import Settings

logger = getLogger(__name__)

class Gap:
    start: datetime
    end: datetime
    duration: int

class Builder:
    """create a set of blocks for a given day and
    communicate that back to external services.
    """
    date: date
    blocks: list[Block] = []
    start_time: datetime
    end_time: datetime


    def __init__(self, day: date|str = date.today()):
        try:
            self.date = date.fromisoformat(day)
        except ValueError:
            self.date = day
        settings = Settings()
        self.start_time = datetime.combine(self.date, settings.start_time)
        self.end_time = datetime.combine(self.date, settings.end_time)

    def get_existing_events(self) -> list:
        """get existing events from calendar"""
        gci = GoogleCalendarIngester()
        existing = gci.get_busy_for_date(self.date,
                                         after=self.start_time,
                                         before=self.end_time)


    def bin_packer(self) -> list:
        """use bin packing to create blocks

        Note: Work Blocks have rules:
            - blocks contain points.
            - only tasks bigger than big block can overlap
            - task overlap is only allowed if:
                - task was the full previous block (no siblings)
                - task is the first in this block (siblings follow)
        """
        gaps = self._get_spaces_between_existing_events(
            self.start_time,
            self.end_time,
            self.get_existing_events())
        for gap in gaps:
            blocks = self._next_biggest_block(gap, [BigBlock, MediumBlock, SmallBlock], [])
            self.blocks.extend(blocks)
        self._set_lunch_block()
        available_tasks = Task.get_tasks()


    @classmethod
    def _get_spaces_between_existing_events(cls, day_start: datetime, day_end: datetime, existing_events: list) -> list:
        """find all the spaces between existing events"""
        ordered_events = sorted(existing_events, key=lambda x: x.start)
        pointer = day_start
        gaps = []

        for event in ordered_events:
            if event.start > pointer:
                gap = Gap(start=pointer,
                    end=event.start,
                    duration=(event.start-pointer).minutes)
                gaps.append(gap)
                pointer = event.end
        if pointer < day_end:
            gap = Gap(start=pointer,
                end=day_end,
                duration=(day_end-pointer).minutes)
            gaps.append(gap)
        return gaps

    def _next_biggest_block(cls,
                          gap: Gap,
                          block_list: list[Block],
                          blocks:list) -> list[Block]:
        """recursively stack the bins"""
        if not block_list:
            return blocks
        next_block = block_list.pop(0)
        count = next_block.total_duration // gap.duration
        remainder = next_block.total_duration % gap.duration
        for i in range(count):
            start = gap.start + (i * next_block.total_duration)
            end = start + next_block.total_duration
            blocks.append(next_block(start=start,
                                     index=len(blocks),
                                     end=end))
        if remainder:
            gap = Gap(start=end,
                      end=gap.end,
                      duration=remainder)
            return cls._next_biggest_block(gap, block_list, blocks)

    def _set_lunch_block(self):
        """set the lunch block"""
        ideal_lunch_start = datetime.combine(self.date, self.settings.lunch_aprox_start)
        lunch_sized_blocks = [b for b in self.blocks if b.size == self.settings.lunch_size]
        if not lunch_sized_blocks:
            logger.error("No lunch sized blocks available. That sucks.")
            return
        lunch_block = lunch_sized_blocks[0]
        for block in lunch_sized_blocks:
            current_delta = abs(lunch_block.start - ideal_lunch_start)
            distance_from_ideal = abs(block.start - ideal_lunch_start)
            if distance_from_ideal < current_delta:
                lunch_block = block
        lunch_block.add_task(
            Task(description="Lunch",
                 entry=lunch_block.start,
                 status="pending",
                 points=block.max_points,
                 tags=["lunch"]))

    @classmethod
    def _assign_tasks_to_blocks(cls,
                                tasks: list[Task],
                                day: Day):
        """do the actual bin packing"""
        # break tasks into stacks of 10 by priority
        task_groups = [
            task[n*10:][:10] for n in
                range((len(tasks)//10) + 1)
        ]
        highest_priority = task_groups.pop(0)

        for partial in highest_priority.sort(key=lambda x: x.partial_group):


                day.most_space_available_block()
                # deal with oversized tasks

                for block in sorted_blocks:
                    if block.can_fit(task):
                        block.add_task(task)
                        tasks.remove(task)
            for ock in sorted_blocks:
                for task in tasks:
                    if block.can_fit(task):
                        block.add_task(task)
                        tasks.remove(task)