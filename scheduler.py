"""Scheduling logic for PawPal+.

The algorithm uses a greedy priority-first strategy:
1. Sort tasks by priority descending (high > medium > low).
2. Within the same priority tier, prefer shorter tasks (maximises the number
   of tasks completed within the available time window).
3. Walk the sorted list and greedily assign tasks to sequential time slots
   starting at DAY_START_MINUTES, stopping when the owner's time budget is
   exhausted.
4. Attach a plain-English reason to every scheduled and skipped task so the
   user understands why each decision was made.
"""

from __future__ import annotations

from typing import List

from models import Owner, Pet, Schedule, ScheduledTask, Task

DAY_START_HOUR = 8  # schedule begins at 08:00
DAY_START_MINUTES = DAY_START_HOUR * 60


class Scheduler:
    """Generates a greedy priority-first daily schedule for a pet owner."""

    def __init__(self, owner: Owner, pet: Pet) -> None:
        """Initialise the scheduler with an owner (time budget) and pet."""
        self.owner = owner
        self.pet = pet

    def build_schedule(self, tasks: List[Task]) -> Schedule:
        """Build and return a Schedule from the provided list of tasks.

        Tasks are sorted by priority (descending) then duration (ascending) and
        greedily assigned until the owner's available time is exhausted.
        """
        schedule = Schedule(owner=self.owner, pet=self.pet)

        if not tasks:
            return schedule

        sorted_tasks = self._sort_tasks(tasks)
        time_cursor = DAY_START_MINUTES
        budget_remaining = self.owner.available_minutes

        for task in sorted_tasks:
            if task.duration_minutes > budget_remaining:
                reason = (
                    f"Skipped — needs {task.duration_minutes} min but only "
                    f"{budget_remaining} min remain in your daily budget."
                )
                schedule.skipped.append((task, reason))
                continue

            reason = self._build_reason(task, time_cursor, budget_remaining)
            scheduled_task = ScheduledTask(
                task=task,
                start_minutes=time_cursor,
                reason=reason,
            )
            schedule.scheduled.append(scheduled_task)
            time_cursor += task.duration_minutes
            budget_remaining -= task.duration_minutes

        return schedule

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _sort_tasks(self, tasks: List[Task]) -> List[Task]:
        """Return tasks sorted by priority desc, then duration asc."""
        return sorted(tasks, key=lambda t: (-t.priority_rank(), t.duration_minutes))

    def _build_reason(
        self, task: Task, start_minutes: int, budget_remaining: int
    ) -> str:
        """Compose a human-readable explanation for scheduling a task."""
        h, m = divmod(start_minutes, 60)
        time_str = f"{h:02d}:{m:02d}"

        priority_phrases = {
            "high": "This is a high-priority task and was scheduled first.",
            "medium": "This is a medium-priority task scheduled after all high-priority tasks.",
            "low": "This is a low-priority task scheduled after higher-priority tasks.",
        }
        base = priority_phrases[task.priority]
        return (
            f"{base} Placed at {time_str} ({task.duration_minutes} min). "
            f"{budget_remaining - task.duration_minutes} min remaining after this task."
        )
