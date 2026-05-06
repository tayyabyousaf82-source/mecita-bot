"""FSM states for the /nueva_cita flow."""
from aiogram.fsm.state import State, StatesGroup


class NuevaCitaStates(StatesGroup):
    # Step 1: Province
    SELECT_PROVINCE = State()
    # Step 2: Trámite
    SELECT_TRAMITE = State()
    # Step 3: Oficina
    SELECT_OFICINA = State()
    # Step 4: Date range
    SELECT_DATE_FROM = State()
    SELECT_DATE_TO = State()
    # Step 5: Contact info
    ADD_PHONES = State()
    ADD_EMAILS = State()
    # Step 6: Certificate (optional)
    ADD_CERTIFICATES = State()
    # Step 7: Summary / confirm
    CONFIRM = State()
    # Editing
    EDIT_FIELD = State()
