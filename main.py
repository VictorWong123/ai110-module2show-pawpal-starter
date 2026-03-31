"""Demo script for PawPal+ — CLI testing ground.

Run with:  python main.py

Demonstrates Phase 4 features:
- Tasks added out of order (sorted correctly by Scheduler)
- Filtering by pet name and completion status
- Recurring task rescheduling via complete_task()
- Conflict detection for overlapping time slots
"""

from pawpal_system import Owner, Pet, Scheduler, Task


def main() -> None:
    """Run a full demo of sorting, filtering, recurring tasks, and conflict detection."""
    owner = Owner(name="Jordan")

    mochi = Pet(name="Mochi", species="dog")
    luna = Pet(name="Luna", species="cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)

    # Tasks added deliberately out of order to verify sorting
    mochi.add_task(Task(description="Evening walk",    time="18:00", frequency="daily"))
    mochi.add_task(Task(description="Flea medication", time="09:00", frequency="weekly"))
    mochi.add_task(Task(description="Morning walk",    time="07:30", frequency="daily"))
    mochi.add_task(Task(description="Breakfast",       time="08:00", frequency="daily"))

    luna.add_task(Task(description="Breakfast",  time="08:00", frequency="daily"))   # conflicts with Mochi's 08:00
    luna.add_task(Task(description="Brush fur",  time="17:00", frequency="weekly"))

    scheduler = Scheduler(owner=owner)

    # --- 1. Sorted schedule ---
    print("=== 1. Full schedule (sorted by time) ===")
    for task in scheduler.get_schedule():
        print(f"  {task.time}  {task.description}")

    # --- 2. Filter by pet ---
    print("\n=== 2. Filter: Mochi's tasks only ===")
    for task in scheduler.filter_by_pet("Mochi"):
        print(f"  {task.time}  {task.description}")

    # --- 3. Filter by status ---
    print("\n=== 3. Filter: pending tasks ===")
    for task in scheduler.get_pending():
        print(f"  {task.time}  {task.description}")

    # --- 4. Recurring task rescheduling ---
    print("\n=== 4. Complete 'Morning walk' and auto-schedule next occurrence ===")
    morning_walk = mochi.tasks[2]  # "Morning walk"
    follow_up = scheduler.complete_task(morning_walk, mochi)
    print(f"  Completed: {morning_walk}")
    print(f"  Follow-up: {follow_up}")

    # --- 5. Conflict detection ---
    print("\n=== 5. Conflict detection ===")
    conflicts = scheduler.get_conflicts()
    if conflicts:
        for _, _, msg in conflicts:
            print(f"  ! {msg}")
    else:
        print("  No conflicts detected.")

    # --- Full pretty-printed schedule ---
    scheduler.print_schedule()


if __name__ == "__main__":
    main()
