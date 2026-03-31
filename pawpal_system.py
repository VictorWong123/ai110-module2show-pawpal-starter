"""Core logic layer for PawPal+.

Defines four classes that model the pet care domain:
- Task: a single care activity with scheduling metadata and completion state.
- Pet: a pet that owns a list of Tasks.
- Owner: a person who owns one or more Pets.
- Scheduler: the "brain" that retrieves, organises, filters, and validates tasks.

Phase 4 additions:
- Task.next_due(): calculates the next due date using timedelta.
- Scheduler.filter_by_pet(): filters tasks to a single pet by name.
- Scheduler.filter_by_status(): filters tasks by completion state.
- Scheduler.complete_task(): marks a task done and auto-schedules the next
  occurrence for daily/weekly tasks.
- Scheduler.get_conflicts(): detects tasks scheduled at the same time.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import List, Optional, Tuple


class Task:
    """A single pet care activity with scheduling metadata and a completion flag."""

    RECURRENCE_DAYS = {"daily": 1, "weekly": 7}

    def __init__(
        self,
        description: str,
        time: str,
        frequency: str = "daily",
        completed: bool = False,
        due_date: Optional[date] = None,
    ) -> None:
        """Initialise a Task.

        Args:
            description: Short label for the activity (e.g. 'Morning walk').
            time: Scheduled time as a string in HH:MM format (e.g. '08:00').
            frequency: How often the task recurs ('daily', 'weekly', 'as needed').
            completed: Whether the task has already been completed today.
            due_date: The calendar date this task is due. Defaults to today.
        """
        self.description = description
        self.time = time
        self.frequency = frequency
        self.completed = completed
        self.due_date: date = due_date if due_date is not None else date.today()

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def next_due(self) -> Optional[date]:
        """Return the next due date based on frequency, or None if non-recurring.

        Uses timedelta so that 'daily' advances by 1 day and 'weekly' by 7 days.
        Returns None for frequencies not in RECURRENCE_DAYS (e.g. 'as needed').
        """
        days = self.RECURRENCE_DAYS.get(self.frequency)
        if days is None:
            return None
        return self.due_date + timedelta(days=days)

    def __repr__(self) -> str:
        """Return a concise developer-readable representation."""
        status = "done" if self.completed else "pending"
        return (
            f"Task({self.description!r}, time={self.time}, "
            f"freq={self.frequency}, due={self.due_date}, {status})"
        )


class Pet:
    """A pet that owns a list of care tasks."""

    def __init__(self, name: str, species: str) -> None:
        """Initialise a Pet with no tasks.

        Args:
            name: The pet's name.
            species: The type of animal (e.g. 'dog', 'cat').
        """
        self.name = name
        self.species = species
        self.tasks: List[Task] = []

    def add_task(self, task: Task) -> None:
        """Append a Task to this pet's task list."""
        self.tasks.append(task)

    def __repr__(self) -> str:
        """Return a concise developer-readable representation."""
        return f"Pet(name={self.name!r}, species={self.species!r}, tasks={len(self.tasks)})"


class Owner:
    """A pet owner who manages one or more pets."""

    def __init__(self, name: str) -> None:
        """Initialise an Owner with no pets.

        Args:
            name: The owner's name.
        """
        self.name = name
        self.pets: List[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a Pet to this owner's roster."""
        self.pets.append(pet)

    def get_all_tasks(self) -> List[Task]:
        """Return every task across all of this owner's pets."""
        all_tasks = []
        for pet in self.pets:
            all_tasks.extend(pet.tasks)
        return all_tasks

    def __repr__(self) -> str:
        """Return a concise developer-readable representation."""
        return f"Owner(name={self.name!r}, pets={len(self.pets)})"


class Scheduler:
    """Retrieves, organises, filters, and validates tasks from an Owner's pets."""

    def __init__(self, owner: Owner) -> None:
        """Initialise the Scheduler for a specific owner.

        Args:
            owner: The Owner whose pets' tasks will be scheduled.
        """
        self.owner = owner

    # ------------------------------------------------------------------
    # Sorting
    # ------------------------------------------------------------------

    def get_schedule(self) -> List[Task]:
        """Return all tasks sorted by scheduled time (HH:MM), earliest first."""
        tasks = self.owner.get_all_tasks()
        return sorted(tasks, key=lambda t: t.time)

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    def get_pending(self) -> List[Task]:
        """Return only incomplete tasks, sorted by time."""
        return self.filter_by_status(completed=False)

    def filter_by_status(self, completed: bool) -> List[Task]:
        """Return tasks matching the given completion status, sorted by time.

        Args:
            completed: Pass True to get completed tasks, False for pending ones.
        """
        return [t for t in self.get_schedule() if t.completed == completed]

    def filter_by_pet(self, pet_name: str) -> List[Task]:
        """Return tasks belonging to the named pet, sorted by time.

        Args:
            pet_name: The name of the pet to filter by (case-sensitive).

        Returns:
            Sorted task list for that pet, or an empty list if the pet is not found.
        """
        for pet in self.owner.pets:
            if pet.name == pet_name:
                return sorted(pet.tasks, key=lambda t: t.time)
        return []

    # ------------------------------------------------------------------
    # Recurring tasks
    # ------------------------------------------------------------------

    def complete_task(self, task: Task, pet: Pet) -> Optional[Task]:
        """Mark a task complete and auto-schedule the next occurrence.

        For 'daily' and 'weekly' tasks, a new Task with the same description,
        time, and frequency is created and added to the pet, with its due_date
        set using timedelta via Task.next_due().

        Args:
            task: The task to mark as complete.
            pet: The pet that owns the task (needed to attach the follow-up).

        Returns:
            The newly created follow-up Task, or None if the task is non-recurring.
        """
        task.mark_complete()
        next_date = task.next_due()
        if next_date is None:
            return None
        follow_up = Task(
            description=task.description,
            time=task.time,
            frequency=task.frequency,
            due_date=next_date,
        )
        pet.add_task(follow_up)
        return follow_up

    # ------------------------------------------------------------------
    # Conflict detection
    # ------------------------------------------------------------------

    def get_conflicts(self) -> List[Tuple[Task, Task, str]]:
        """Detect tasks scheduled at the same time across all pets.

        Two tasks conflict when they share the same HH:MM time string. The
        check uses exact string matching rather than duration overlap — a
        deliberate simplification that avoids needing duration data on Task
        while still catching the most common scheduling mistakes.

        Returns:
            A list of (task_a, task_b, warning_message) tuples. Returns an
            empty list when no conflicts exist.
        """
        schedule = self.get_schedule()
        # Build a map of time -> list of (task, pet_name)
        time_map: dict = {}
        for pet in self.owner.pets:
            for task in pet.tasks:
                time_map.setdefault(task.time, []).append((task, pet.name))

        conflicts: List[Tuple[Task, Task, str]] = []
        for time_slot, entries in time_map.items():
            if len(entries) < 2:
                continue
            # Report every unique pair at this time slot
            for i in range(len(entries)):
                for j in range(i + 1, len(entries)):
                    task_a, pet_a = entries[i]
                    task_b, pet_b = entries[j]
                    msg = (
                        f"Conflict at {time_slot}: "
                        f"'{task_a.description}' ({pet_a}) and "
                        f"'{task_b.description}' ({pet_b}) are both scheduled at the same time."
                    )
                    conflicts.append((task_a, task_b, msg))
        return conflicts

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def print_schedule(self) -> None:
        """Print today's full schedule to the terminal in a readable format."""
        schedule = self.get_schedule()
        print(f"\n=== Today's Schedule for {self.owner.name} ===")

        if not schedule:
            print("  (no tasks scheduled)")
            return

        for pet in self.owner.pets:
            pet_tasks = [t for t in schedule if t in pet.tasks]
            if not pet_tasks:
                continue
            print(f"\n  {pet.name} ({pet.species})")
            for task in pet_tasks:
                status = "[x]" if task.completed else "[ ]"
                print(f"    {status} {task.time}  {task.description}  ({task.frequency})  due {task.due_date}")

        conflicts = self.get_conflicts()
        if conflicts:
            print("\n  *** Scheduling Conflicts ***")
            for _, _, msg in conflicts:
                print(f"  ! {msg}")

        pending = len(self.get_pending())
        total = len(schedule)
        print(f"\n  {total - pending}/{total} tasks completed today.\n")
