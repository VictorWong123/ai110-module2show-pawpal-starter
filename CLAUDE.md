# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PawPal+ is a Python/Streamlit pet care scheduling app built as an educational assignment (AI110, Module 2). The starter code provides only the UI scaffold — the scheduling logic, data models, and tests are intentionally left to be implemented.

## Commands

**Setup:**
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**Run the app:**
```bash
streamlit run app.py
```

**Run all tests:**
```bash
pytest
```

**Run a single test file:**
```bash
pytest tests/test_scheduler.py
```

## Architecture

`app.py` is the sole entry point — a thin Streamlit UI with no scheduling logic. It demonstrates the expected UI shape (owner info, pet info, task list, schedule generation button) but the "Generate schedule" button is a stub.

The intended design is a separation between:
- **Backend modules** (to be created): Python classes for `Pet`, `Owner`, `Task`, and a `Scheduler`/planner. These should live in separate `.py` files (e.g., `scheduler.py`, `models.py`), not inside `app.py`.
- **UI layer** (`app.py`): Imports and calls the backend, displays results.

The scheduler must accept task constraints (duration, priority, available time, preferences) and return an ordered daily plan with reasoning for each task's placement.

**Streamlit session state** (`st.session_state.tasks`) is used to persist the task list across rerenders. Any additional shared UI state should follow this same pattern.

## Key Requirements

From `README.md`:
- Tasks have at minimum: title, duration (minutes), priority
- Owner and pet have basic info and preferences
- The scheduler produces an ordered daily plan and explains its reasoning
- Tests must cover the most important scheduling behaviors
