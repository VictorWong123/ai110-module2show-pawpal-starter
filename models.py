"""Data model classes for PawPal+."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Literal, Tuple

Priority = Literal["low", "medium", "high"]
PRIORITY_RANK = {"low": 1, "medium": 2, "high": 3}


@dataclass
class Task:
    """A single pet care task with time and priority constraints."""

    title: str
    duration_minutes: int
    priority: Priority

    def priority_rank(self) -> int:
        """Return a numeric rank for the priority level (higher is more urgent)."""
        return PRIORITY_RANK[self.priority]

    def __repr__(self) -> str:
        return f"Task(title={self.title!r}, duration={self.duration_minutes}m, priority={self.priority})"


@dataclass
class Pet:
    """Represents a pet with basic identifying information."""

    name: str
    species: str

    def __repr__(self) -> str:
        return f"Pet(name={self.name!r}, species={self.species!r})"


@dataclass
class Owner:
    """Represents a pet owner with a daily time budget for pet care."""

    name: str
    available_minutes: int = 120

    def __repr__(self) -> str:
        return f"Owner(name={self.name!r}, available_minutes={self.available_minutes})"


@dataclass
class ScheduledTask:
    """A task placed into a concrete time slot within a daily schedule."""

    task: Task
    start_minutes: int  # minutes from midnight
    reason: str

    @property
    def end_minutes(self) -> int:
        """Return the minute-from-midnight at which this task ends."""
        return self.start_minutes + self.task.duration_minutes

    def start_label(self) -> str:
        """Return the start time formatted as HH:MM."""
        h, m = divmod(self.start_minutes, 60)
        return f"{h:02d}:{m:02d}"

    def end_label(self) -> str:
        """Return the end time formatted as HH:MM."""
        h, m = divmod(self.end_minutes, 60)
        return f"{h:02d}:{m:02d}"


@dataclass
class Schedule:
    """A complete daily schedule for a pet owner."""

    owner: Owner
    pet: Pet
    scheduled: List[ScheduledTask] = field(default_factory=list)
    skipped: List[Tuple[Task, str]] = field(default_factory=list)

    @property
    def total_minutes_scheduled(self) -> int:
        """Return the total minutes of care scheduled."""
        return sum(st.task.duration_minutes for st in self.scheduled)

    @property
    def minutes_remaining(self) -> int:
        """Return how many minutes of the owner's budget are still unallocated."""
        return self.owner.available_minutes - self.total_minutes_scheduled
