"""Tests for the PawPal+ core logic in pawpal_system.py."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from pawpal_system import Owner, Pet, Scheduler, Task


# ------------------------------------------------------------------
# Task
# ------------------------------------------------------------------


def test_task_defaults_to_not_completed():
    """A newly created Task should have completed == False."""
    task = Task(description="Walk", time="08:00")
    assert task.completed is False


def test_mark_complete_changes_status():
    """Calling mark_complete() must flip the task's completed flag to True."""
    task = Task(description="Walk", time="08:00")
    task.mark_complete()
    assert task.completed is True


def test_mark_complete_is_idempotent():
    """Calling mark_complete() twice must not raise and status stays True."""
    task = Task(description="Walk", time="08:00")
    task.mark_complete()
    task.mark_complete()
    assert task.completed is True


# ------------------------------------------------------------------
# Pet
# ------------------------------------------------------------------


def test_pet_starts_with_no_tasks():
    """A newly created Pet must have an empty task list."""
    pet = Pet(name="Mochi", species="dog")
    assert len(pet.tasks) == 0


def test_add_task_increases_pet_task_count():
    """Adding a Task to a Pet must increment its task count by one."""
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task(description="Walk", time="08:00"))
    assert len(pet.tasks) == 1


def test_add_multiple_tasks_increases_count_correctly():
    """Adding N tasks to a Pet must result in exactly N tasks stored."""
    pet = Pet(name="Luna", species="cat")
    for i in range(3):
        pet.add_task(Task(description=f"Task {i}", time="09:00"))
    assert len(pet.tasks) == 3


# ------------------------------------------------------------------
# Owner
# ------------------------------------------------------------------


def test_owner_starts_with_no_pets():
    """A newly created Owner must have an empty pets list."""
    owner = Owner(name="Jordan")
    assert len(owner.pets) == 0


def test_add_pet_increases_owner_pet_count():
    """Adding a Pet to an Owner must increment the pet count by one."""
    owner = Owner(name="Jordan")
    owner.add_pet(Pet(name="Mochi", species="dog"))
    assert len(owner.pets) == 1


def test_get_all_tasks_aggregates_across_pets():
    """get_all_tasks() must return the combined tasks of all pets."""
    owner = Owner(name="Jordan")

    dog = Pet(name="Mochi", species="dog")
    dog.add_task(Task(description="Walk", time="07:30"))
    dog.add_task(Task(description="Feed", time="08:00"))

    cat = Pet(name="Luna", species="cat")
    cat.add_task(Task(description="Feed", time="08:15"))

    owner.add_pet(dog)
    owner.add_pet(cat)

    assert len(owner.get_all_tasks()) == 3


def test_get_all_tasks_empty_owner():
    """An Owner with no pets must return an empty list from get_all_tasks()."""
    owner = Owner(name="Alex")
    assert owner.get_all_tasks() == []


# ------------------------------------------------------------------
# Scheduler
# ------------------------------------------------------------------


def test_get_schedule_sorts_by_time():
    """get_schedule() must return tasks ordered earliest time first."""
    owner = Owner(name="Jordan")
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task(description="Evening walk", time="18:00"))
    pet.add_task(Task(description="Morning walk", time="07:30"))
    pet.add_task(Task(description="Midday meds", time="12:00"))
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner)
    times = [t.time for t in scheduler.get_schedule()]
    assert times == sorted(times)


def test_get_pending_excludes_completed_tasks():
    """get_pending() must omit tasks that have been marked complete."""
    owner = Owner(name="Jordan")
    pet = Pet(name="Mochi", species="dog")

    done = Task(description="Morning walk", time="07:30")
    done.mark_complete()
    todo = Task(description="Evening walk", time="18:00")

    pet.add_task(done)
    pet.add_task(todo)
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner)
    pending = scheduler.get_pending()
    assert len(pending) == 1
    assert pending[0].description == "Evening walk"
