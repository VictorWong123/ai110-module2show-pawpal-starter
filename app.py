"""PawPal+ Streamlit application.

Entry point for PawPal+. All scheduling logic is delegated to the classes
defined in pawpal_system.py. This module handles only UI rendering and
wires user actions to the appropriate backend methods.

Session state keys:
    owner (Owner): the single Owner instance persisted for the session.
"""

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("PawPal+")
st.caption("Your daily pet care planner.")

# ------------------------------------------------------------------
# Session state initialisation
# Streamlit re-runs this file top-to-bottom on every interaction, so the
# Owner object is stored in st.session_state to survive across rerenders.
# ------------------------------------------------------------------

if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan")

owner: Owner = st.session_state.owner

# ------------------------------------------------------------------
# Owner setup
# ------------------------------------------------------------------

st.subheader("Owner")

with st.form("owner_form"):
    owner_name_input = st.text_input("Your name", value=owner.name)
    if st.form_submit_button("Update name"):
        owner.name = owner_name_input.strip() or owner.name
        st.rerun()

st.write(f"Logged in as: **{owner.name}**")

# ------------------------------------------------------------------
# Pets
# ------------------------------------------------------------------

st.subheader("Pets")

with st.form("add_pet_form", clear_on_submit=True):
    c1, c2 = st.columns(2)
    with c1:
        new_pet_name = st.text_input("Pet name", value="Mochi")
    with c2:
        new_species = st.selectbox("Species", ["dog", "cat", "other"])
    if st.form_submit_button("Add pet"):
        if new_pet_name.strip():
            owner.add_pet(Pet(name=new_pet_name.strip(), species=new_species))
            st.rerun()

if owner.pets:
    for pet in owner.pets:
        st.write(f"- **{pet.name}** ({pet.species}) — {len(pet.tasks)} task(s)")
else:
    st.info("No pets yet. Add one above.")

# ------------------------------------------------------------------
# Tasks
# ------------------------------------------------------------------

st.subheader("Tasks")

if not owner.pets:
    st.warning("Add a pet before adding tasks.")
else:
    with st.form("add_task_form", clear_on_submit=True):
        pet_names = [p.name for p in owner.pets]
        selected_pet_name = st.selectbox("Add task to", pet_names)

        c1, c2, c3 = st.columns(3)
        with c1:
            task_desc = st.text_input("Description", value="Morning walk")
        with c2:
            task_time = st.text_input("Time (HH:MM)", value="08:00")
        with c3:
            task_freq = st.selectbox("Frequency", ["daily", "weekly", "as needed"])

        if st.form_submit_button("Add task"):
            if task_desc.strip():
                target_pet = next(p for p in owner.pets if p.name == selected_pet_name)
                target_pet.add_task(
                    Task(
                        description=task_desc.strip(),
                        time=task_time.strip(),
                        frequency=task_freq,
                    )
                )
                st.rerun()

    # Show all current tasks grouped by pet
    all_tasks = owner.get_all_tasks()
    if all_tasks:
        for pet in owner.pets:
            if pet.tasks:
                st.write(f"**{pet.name}**")
                for task in pet.tasks:
                    status = "~~done~~" if task.completed else task.description
                    st.write(f"  - {status} at {task.time} ({task.frequency})")
    else:
        st.info("No tasks yet. Add one above.")

# ------------------------------------------------------------------
# Schedule generation
# ------------------------------------------------------------------

st.subheader("Today's Schedule")

if st.button("Generate schedule", type="primary"):
    all_tasks = owner.get_all_tasks()
    if not all_tasks:
        st.warning("Add at least one task before generating a schedule.")
    else:
        scheduler = Scheduler(owner=owner)
        schedule = scheduler.get_schedule()
        pending = scheduler.get_pending()
        conflicts = scheduler.get_conflicts()

        completed_count = len(schedule) - len(pending)
        st.success(
            f"{completed_count}/{len(schedule)} tasks completed today "
            f"for {owner.name}'s pet(s)."
        )

        if conflicts:
            for _, _, msg in conflicts:
                st.warning(msg)

        for pet in owner.pets:
            pet_tasks_in_schedule = [t for t in schedule if t in pet.tasks]
            if not pet_tasks_in_schedule:
                continue
            st.markdown(f"#### {pet.name} ({pet.species})")
            table_rows = []
            for task in pet_tasks_in_schedule:
                status = "Done" if task.completed else "Pending"
                table_rows.append(
                    {"Time": task.time, "Task": task.description, "Frequency": task.frequency, "Status": status}
                )
            st.table(table_rows)
            for task in pet_tasks_in_schedule:
                if not task.completed:
                    if st.button(f"Mark done: {task.description} @ {task.time}", key=f"done_{id(task)}"):
                        task.mark_complete()
                        st.rerun()

# ------------------------------------------------------------------
# Reset
# ------------------------------------------------------------------

st.divider()
if st.button("Reset session"):
    del st.session_state.owner
    st.rerun()
