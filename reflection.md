# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

The initial UML included four classes: `Task`, `Pet`, `Owner`, and `Scheduler`.

- `Task` holds the description, scheduled time, frequency, and completion flag.
- `Pet` owns a list of tasks and encapsulates everything specific to one animal.
- `Owner` aggregates pets and exposes `get_all_tasks()` as a convenience method so higher layers never need to iterate pets manually.
- `Scheduler` sits above all three and is the sole class responsible for sorting, filtering, conflict detection, and recurring-task scheduling.

The intent was a clear layered architecture: data models at the bottom, an orchestrating `Scheduler` on top, and the Streamlit UI as a thin wrapper that calls `Scheduler` methods and renders their outputs.

**b. Design changes**

One meaningful change: `Task` was given a `due_date` field (defaulting to `date.today()`) that was not in the initial sketch. The initial design assumed tasks were always "for today." Once recurring tasks were added, a concrete `due_date` became necessary so that `next_due()` could compute the follow-up date with `timedelta` without ambiguity. This change was surgical — it didn't alter the external interface of `Pet`, `Owner`, or `Scheduler`.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers:

- **Time** — tasks are sorted by their `HH:MM` string so the day reads chronologically.
- **Frequency** — `daily` and `weekly` tasks auto-reschedule after completion; `as needed` tasks do not.
- **Completion state** — `get_pending()` / `filter_by_status()` let the UI and tests separate done from todo work without rebuilding the full schedule.
- **Time-slot collisions** — `get_conflicts()` flags any two tasks that share the same start time, prompting the owner to resolve the overlap.

The most important constraint to get right was sorting, because a schedule that displays tasks out of order is actively misleading. Conflict detection was second: silent collisions could cause an owner to miss a task entirely.

**b. Tradeoffs**

The conflict detector uses **exact time-string matching** (`task_a.time == task_b.time`) rather than checking whether two tasks' time windows overlap based on their durations. This means two tasks at `"08:00"` are flagged as a conflict even if one takes 5 minutes and they would finish before the other starts, and it means a 30-minute task at `"07:45"` that runs into an `"08:00"` task is *not* caught.

This tradeoff is reasonable for this scenario because `Task` intentionally does not carry a duration field — adding one would increase the data burden on every task entry for a benefit (overlap detection) that matters mainly when tasks are long. For a pet care app where most tasks are short and owners think in terms of discrete time slots, flagging exact-time clashes covers the most common real mistake (scheduling two pets' feedings at literally the same moment) without requiring duration data that most users won't bother entering accurately.

---

## 3. AI Collaboration

**a. How you used AI**

AI was most valuable in three modes:

1. **Design brainstorming** — asking "what methods should a Scheduler class expose for a pet care app?" surfaced `filter_by_status` and `complete_task` as useful additions I hadn't planned initially.
2. **Algorithmic implementation** — asking how to use `timedelta` to advance a `date` by a given number of days gave a concise, correct pattern that I then verified and adapted.
3. **Test scaffolding** — asking for a list of edge cases for the conflict detector produced several I would have missed (e.g., three tasks at the same time producing three pairs, not one conflict).

The most effective prompt pattern was: "Given this interface, what are the five most important behaviors to test?" — because it forced the AI to reason about correctness from the outside in rather than from the implementation outward.

**b. Judgment and verification**

When asked to implement conflict detection, the AI initially suggested raising an exception when a conflict was found. That would have crashed the app on the first overlap — exactly the opposite of what a friendly UI needs. I rejected the suggestion and instead asked for a version that collects all conflicts into a list of warning messages, which the UI can then surface with `st.warning()`. I verified the change by writing a test that adds two tasks at the same time and asserts that `get_conflicts()` returns a non-empty list without raising.

---

## 4. Testing and Verification

**a. What you tested**

Key behaviors covered:

- A new `Task` defaults to `completed = False`.
- `mark_complete()` flips the flag to `True` and is idempotent.
- `Pet` starts empty; `add_task` increments the count correctly.
- `Owner.get_all_tasks()` aggregates across multiple pets.
- `Scheduler.get_schedule()` returns tasks in ascending time order regardless of insertion order.
- `Scheduler.get_pending()` excludes completed tasks.

These tests are important because they verify the correctness of every layer independently. A broken `mark_complete` would silently corrupt the UI's "done/pending" display; a broken sort would make the schedule unreadable.

**b. Confidence**

Confidence is high for the core happy path. Edge cases worth adding next:

- Tasks added with invalid time formats (e.g., `"8:00"` vs `"08:00"`) — currently sorted lexicographically, which breaks for single-digit hours.
- `get_conflicts()` with three tasks at the same slot — should produce three pairs.
- `complete_task()` for an `"as needed"` task — should return `None` and not add a follow-up.
- An owner with no pets calling `get_schedule()` — should return `[]` without raising.

---

## 5. Reflection

**a. What went well**

The separation between the data models (`Task`, `Pet`, `Owner`) and the `Scheduler` class worked cleanly. Because `Scheduler` only calls public methods on `Owner` and never reaches into a `Pet`'s task list directly (except through `Owner.get_all_tasks()`), all the algorithmic logic is co-located and easy to unit-test without standing up any UI.

**b. What you would improve**

The `time` field on `Task` is a plain string, which makes sorting fragile — `"9:00"` and `"09:00"` are lexicographically different but mean the same thing. In a next iteration I would store time as a `datetime.time` object and render it as a string only in the UI layer. That would also enable true duration-overlap conflict detection.

**c. Key takeaway**

The most important lesson was that **AI is a fast first-draft generator, not a final decision maker**. Every time I accepted a suggestion without reading it carefully, I introduced something that needed to be fixed later (like the exception-raising conflict detector). Every time I treated the AI as a consultant whose output I reviewed and adapted, I got to a better result faster than I would have alone. The human role in AI-assisted engineering is not to approve or reject outputs wholesale — it is to evaluate them against requirements the AI doesn't fully know.
