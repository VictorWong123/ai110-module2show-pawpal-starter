"""Tests for the PawPal+ scheduling logic."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from models import Owner, Pet, Task
from scheduler import DAY_START_MINUTES, Scheduler


@pytest.fixture
def owner():
    """Default owner with 60 minutes available."""
    return Owner(name="Jordan", available_minutes=60)


@pytest.fixture
def pet():
    """Default pet."""
    return Pet(name="Mochi", species="dog")


@pytest.fixture
def scheduler(owner, pet):
    """Scheduler initialised with default owner and pet."""
    return Scheduler(owner=owner, pet=pet)


# ------------------------------------------------------------------
# Empty / edge cases
# ------------------------------------------------------------------


def test_empty_task_list_returns_empty_schedule(scheduler):
    """An empty task list should produce a schedule with nothing scheduled."""
    schedule = scheduler.build_schedule([])
    assert schedule.scheduled == []
    assert schedule.skipped == []


def test_single_task_fits(scheduler):
    """A single task that fits within the budget should be scheduled."""
    task = Task(title="Walk", duration_minutes=20, priority="high")
    schedule = scheduler.build_schedule([task])
    assert len(schedule.scheduled) == 1
    assert schedule.scheduled[0].task == task


def test_single_task_too_long_is_skipped(scheduler):
    """A task longer than the available budget should be skipped, not scheduled."""
    task = Task(title="Long hike", duration_minutes=90, priority="high")
    schedule = scheduler.build_schedule([task])
    assert schedule.scheduled == []
    assert len(schedule.skipped) == 1


# ------------------------------------------------------------------
# Priority ordering
# ------------------------------------------------------------------


def test_high_priority_scheduled_before_low(scheduler):
    """High-priority tasks must appear before low-priority tasks in the schedule."""
    tasks = [
        Task(title="Low task", duration_minutes=10, priority="low"),
        Task(title="High task", duration_minutes=10, priority="high"),
    ]
    schedule = scheduler.build_schedule(tasks)
    titles = [st.task.title for st in schedule.scheduled]
    assert titles.index("High task") < titles.index("Low task")


def test_all_three_priorities_ordered_correctly(scheduler):
    """Tasks with all three priority levels must be ordered high > medium > low."""
    owner = Owner(name="Alex", available_minutes=120)
    pet = Pet(name="Rex", species="dog")
    sched = Scheduler(owner=owner, pet=pet)
    tasks = [
        Task(title="Low", duration_minutes=10, priority="low"),
        Task(title="Medium", duration_minutes=10, priority="medium"),
        Task(title="High", duration_minutes=10, priority="high"),
    ]
    schedule = sched.build_schedule(tasks)
    titles = [st.task.title for st in schedule.scheduled]
    assert titles == ["High", "Medium", "Low"]


def test_same_priority_shorter_task_first(scheduler):
    """Among tasks with equal priority, shorter tasks should be scheduled first."""
    tasks = [
        Task(title="Long high", duration_minutes=30, priority="high"),
        Task(title="Short high", duration_minutes=10, priority="high"),
    ]
    schedule = scheduler.build_schedule(tasks)
    titles = [st.task.title for st in schedule.scheduled]
    assert titles.index("Short high") < titles.index("Long high")


# ------------------------------------------------------------------
# Time budget
# ------------------------------------------------------------------


def test_tasks_exceeding_budget_are_skipped(scheduler):
    """Tasks that push total duration past the owner's budget must be skipped."""
    tasks = [
        Task(title="Task A", duration_minutes=40, priority="high"),
        Task(title="Task B", duration_minutes=30, priority="medium"),  # 40+30 > 60
    ]
    schedule = scheduler.build_schedule(tasks)
    scheduled_titles = [st.task.title for st in schedule.scheduled]
    skipped_titles = [t.title for t, _ in schedule.skipped]
    assert "Task A" in scheduled_titles
    assert "Task B" in skipped_titles


def test_total_minutes_does_not_exceed_budget(scheduler):
    """Total scheduled minutes must never exceed the owner's available budget."""
    tasks = [
        Task(title="A", duration_minutes=25, priority="high"),
        Task(title="B", duration_minutes=25, priority="high"),
        Task(title="C", duration_minutes=25, priority="medium"),
    ]
    schedule = scheduler.build_schedule(tasks)
    assert schedule.total_minutes_scheduled <= scheduler.owner.available_minutes


def test_minutes_remaining_is_correct(scheduler):
    """minutes_remaining must equal budget minus total scheduled minutes."""
    tasks = [Task(title="Walk", duration_minutes=20, priority="high")]
    schedule = scheduler.build_schedule(tasks)
    assert schedule.minutes_remaining == scheduler.owner.available_minutes - 20


# ------------------------------------------------------------------
# Start times
# ------------------------------------------------------------------


def test_first_task_starts_at_day_start(scheduler):
    """The first scheduled task must start exactly at DAY_START_MINUTES."""
    task = Task(title="Walk", duration_minutes=15, priority="high")
    schedule = scheduler.build_schedule([task])
    assert schedule.scheduled[0].start_minutes == DAY_START_MINUTES


def test_consecutive_tasks_are_back_to_back(scheduler):
    """Each task must start exactly when the previous task ends."""
    owner = Owner(name="Jordan", available_minutes=120)
    pet = Pet(name="Mochi", species="dog")
    sched = Scheduler(owner=owner, pet=pet)
    tasks = [
        Task(title="A", duration_minutes=15, priority="high"),
        Task(title="B", duration_minutes=20, priority="high"),
    ]
    schedule = sched.build_schedule(tasks)
    assert schedule.scheduled[1].start_minutes == schedule.scheduled[0].end_minutes


# ------------------------------------------------------------------
# Reason strings
# ------------------------------------------------------------------


def test_scheduled_task_has_non_empty_reason(scheduler):
    """Every scheduled task must have a non-empty reason string."""
    task = Task(title="Feed", duration_minutes=5, priority="medium")
    schedule = scheduler.build_schedule([task])
    assert schedule.scheduled[0].reason.strip() != ""


def test_skipped_task_has_non_empty_reason(scheduler):
    """Every skipped task must have a non-empty reason string."""
    task = Task(title="Long walk", duration_minutes=999, priority="low")
    schedule = scheduler.build_schedule([task])
    _, reason = schedule.skipped[0]
    assert reason.strip() != ""
