import os
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

CREDENTIALS_FILE = "credentials.json"
MAX_BOOKING_DAYS = 2
DAYS_OF_WEEK = ["lunedi", "martedi", "mercoledi", "giovedi", "venerdi", "sabato",]
SLOT_ORARI = ["14:00 - 15:30", "15:30 - 17:00", "17:00 - 18:30", "18:30 - 20:00"]

# Stati del flusso di impostazione giorni/orario (usati nel ConversationHandler)
BOOKING_MENU = 100
BOOKING_MODIFY = 101
BOOKING_REPLACE = 102
BOOKING_SLOT = 103

def load_credentials() -> dict:
    """Carica il file JSON con le credenziali e le impostazioni di prenotazione."""
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_credentials(credentials: dict) -> None:
    """Salva il dizionario aggiornato nel file JSON."""
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(credentials, f,indent=4, ensure_ascii=False)

async def show_booking_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Visualizza un menu con i giorni della settimana.
    Se un giorno è già impostato, viene evidenziato (con un'emoji e lo slot impostato).
    Include anche un pulsante "Torna indietro".
    """
    user_id = str(update.effective_user.id)
    creds = load_credentials()
    user_data = creds.get(user_id, {})
    booking_days = user_data.get("booking_days", {})

    keyboard = []
    for day in DAYS_OF_WEEK:
        if day in booking_days:
            # Evidenzia il giorno impostato, mostrando anche lo slot
            button_text = f"✅ {day.capitalize()} ({SLOT_ORARI[booking_days[day]]})"
            callback_data = f"modify_day:{day}"
        else:
            button_text = day.capitalize()
            callback_data = f"set_day:{day}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    # Aggiunge un pulsante per tornare al menu principale
    keyboard.append([InlineKeyboardButton("Torna indietro", callback_data="back")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text("Imposta i giorni di prenotazione:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Imposta i giorni di prenotazione:", reply_markup=reply_markup)
    return BOOKING_MENU

async def booking_day_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Gestisce il callback quando l'utente clicca su un giorno.
    - Se il giorno è già impostato, mostra un sottomenu per modificare lo slot o cancellare la prenotazione.
    - Se non è impostato, controlla se il limite massimo è raggiunto; in tal caso chiede di sostituire un giorno,
      altrimenti mostra il menu per impostare lo slot.
    """
    query = update.callback_query
    await query.answer()
    # Normalizza il callback data: rimuove spazi e lo porta in minuscolo
    data = query.data.strip().lower()  # es. "set_day:martedi" o "modify_day:lunedi" o "booking_back"
    logging.info(f"booking_day_handler: callback_data = {data}")

    if data == "back":
        from bot import show_menu  # Import locale per evitare cicli di importazione
        return await show_menu(update, context)
    if data == "booking_back":
        return await show_booking_settings_menu(update, context)
    
    try:
        action, day = data.split(":", 1)
    except ValueError:
        logging.error("Callback data non formattata correttamente: " + data)
        await query.edit_message_text("Errore: formato del callback non corretto.")
        return BOOKING_MENU

    context.user_data["selected_day"] = day
    user_id = str(update.effective_user.id)
    creds = load_credentials()
    user_data = creds.get(user_id, {})
    booking_days = user_data.get("booking_days", {})

    if action == "modify_day":
        # Giorno già impostato: mostra sottomenu per modificare lo slot o cancellare la prenotazione
        keyboard = [
            [InlineKeyboardButton("Modifica slot", callback_data=f"change_slot:{day}")],
            [InlineKeyboardButton("Elimina prenotazione", callback_data=f"delete_day:{day}")],
            [InlineKeyboardButton("Torna indietro", callback_data="booking_back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(f"{day.capitalize()} è già impostato (slot {booking_days[day]}). Cosa vuoi fare?", reply_markup=reply_markup)
        return BOOKING_MODIFY
    elif action == "change_slot":
        # Instrada alla funzione change_slot_handler per modificare lo slot del giorno
        return await change_slot_handler(update, context)
    elif action == "delete_day":
        # Instrada alla funzione delete_day_handler per cancellare la prenotazione del giorno
        return await delete_day_handler(update, context)
    elif action == "set_day":
        if len(booking_days) >= MAX_BOOKING_DAYS:
            # Se il limite è raggiunto, chiedi all'utente quale giorno sostituire
            keyboard = []
            for d in booking_days.keys():
                keyboard.append([InlineKeyboardButton(f"Sostituisci {d.capitalize()} (slot {booking_days[d]}: {SLOT_ORARI[booking_days[d]]})", callback_data=f"replace_day:{d}")])
            keyboard.append([InlineKeyboardButton("Annulla", callback_data="booking_back")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("Hai raggiunto il limite di giorni prenotabili. Seleziona il giorno da sostituire:", reply_markup=reply_markup)
            print("Hai raggiunto il limite di giorni prenotabili.")
            return BOOKING_REPLACE
        else:
            # Se il giorno non è impostato e il limite non è raggiunto, mostra il menu per scegliere lo slot
            keyboard = [
                [InlineKeyboardButton("Slot 0: "+SLOT_ORARI[0], callback_data="set_slot:0")],
                [InlineKeyboardButton("Slot 1: "+SLOT_ORARI[1], callback_data="set_slot:1")],
                [InlineKeyboardButton("Slot 2: "+SLOT_ORARI[2], callback_data="set_slot:2")],
                [InlineKeyboardButton("Slot 3: "+SLOT_ORARI[3], callback_data="set_slot:3")],
                [InlineKeyboardButton("Torna indietro", callback_data="booking_back")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(f"Seleziona lo slot orario per {day.capitalize()}:", reply_markup=reply_markup)
            print(f"Seleziona lo slot orario per {day.capitalize()}:")
            return BOOKING_SLOT
    else:
        await query.edit_message_text("Azione non riconosciuta.")
        return BOOKING_MENU
    
async def slot_selection_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Gestisce la scelta dello slot orario per un giorno.
    Se il flusso prevede la sostituzione (caso in cui è stato raggiunto il limite), sostituisce il giorno selezionato.
    Altrimenti, aggiunge o modifica la prenotazione per il giorno selezionato.
    """
    query = update.callback_query
    await query.answer()
    data = query.data  # es. "set_slot:1"
    if data == "booking_back":
        return await show_booking_settings_menu(update, context)
    _, slot_str = data.split(":")
    slot = int(slot_str)
    user_id = str(update.effective_user.id)
    creds = load_credentials()
    if user_id not in creds:
        creds[user_id] = {"booking_days": {}}
    if "booking_days" not in creds[user_id]:
        creds[user_id]["booking_days"] = {}
    
    if "replace_day" in context.user_data:
        # Sostituzione: il nuovo giorno da impostare è quello salvato in "selected_day"
        old_day = context.user_data.pop("replace_day")
        new_day = context.user_data.get("selected_day")
        if new_day is None:
            await query.edit_message_text("Errore: giorno non selezionato.")
            return BOOKING_MENU
        # Rimuovi il vecchio giorno e imposta il nuovo
        if old_day in creds[user_id]["booking_days"]:
            del creds[user_id]["booking_days"][old_day]
        creds[user_id]["booking_days"][new_day] = slot
        await query.edit_message_text(f"{new_day.capitalize()} impostato con slot {slot}, sostituendo {old_day.capitalize()}.")
    else:
        # Aggiungi o modifica la prenotazione per il giorno selezionato
        day = context.user_data.get("selected_day")
        if day is None:
            await query.edit_message_text("Errore: giorno non selezionato.")
            return BOOKING_MENU
        creds[user_id]["booking_days"][day] = slot
        await query.edit_message_text(f"{day.capitalize()} impostato con slot {slot} {SLOT_ORARI[slot]}.")
    save_credentials(creds)
    return await show_booking_settings_menu(update, context)

async def change_slot_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Gestisce la modifica dello slot per un giorno già impostato.
    Mostra un menu per scegliere il nuovo slot.
    """
    query = update.callback_query
    await query.answer()
    data = query.data  # es. "change_slot:lunedi"
    _, day = data.split(":")
    context.user_data["selected_day"] = day
    keyboard = [
        [InlineKeyboardButton("Slot 0: "+SLOT_ORARI[0], callback_data="set_slot:0")],
        [InlineKeyboardButton("Slot 1: "+SLOT_ORARI[1], callback_data="set_slot:1")],
        [InlineKeyboardButton("Slot 2: "+SLOT_ORARI[2], callback_data="set_slot:2")],
        [InlineKeyboardButton("Slot 3: "+SLOT_ORARI[3], callback_data="set_slot:3")],
        [InlineKeyboardButton("Torna indietro", callback_data="booking_back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"Seleziona il nuovo slot per {day.capitalize()}:", reply_markup=reply_markup)
    return BOOKING_SLOT

async def delete_day_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Gestisce la cancellazione della prenotazione per un giorno.
    """
    query = update.callback_query
    await query.answer()
    data = query.data  # es. "delete_day:lunedi"
    _, day = data.split(":")
    user_id = str(update.effective_user.id)
    creds = load_credentials()
    user_data = creds.get(user_id, {})
    booking_days = user_data.get("booking_days", {})
    if day in booking_days:
        del booking_days[day]
        creds[user_id]["booking_days"] = booking_days
        save_credentials(creds)
        await query.edit_message_text(f"Prenotazione per {day.capitalize()} cancellata.")
    else:
        await query.edit_message_text("Giorno non trovato.")
    return await show_booking_settings_menu(update, context)

async def replace_day_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Gestisce la sostituzione di un giorno già impostato con uno nuovo.
    L'utente ha già raggiunto il limite massimo e deve scegliere quale sostituire.
    """
    query = update.callback_query
    await query.answer()
    data = query.data  # es. "replace_day:lunedi"
    if data == "booking_back":
        return await show_booking_settings_menu(update, context)
    _, old_day = data.split(":")
    context.user_data["replace_day"] = old_day
    new_day = context.user_data.get("selected_day", None)
    if new_day is None:
        await query.edit_message_text("Errore: nuovo giorno non selezionato.")
        return BOOKING_MENU
    keyboard = [
        [InlineKeyboardButton("Slot 0: "+SLOT_ORARI[0], callback_data="set_slot:0")],
        [InlineKeyboardButton("Slot 1: "+SLOT_ORARI[1], callback_data="set_slot:1")],
        [InlineKeyboardButton("Slot 2: "+SLOT_ORARI[2], callback_data="set_slot:2")],
        [InlineKeyboardButton("Slot 3: "+SLOT_ORARI[3], callback_data="set_slot:3")],
        [InlineKeyboardButton("Torna indietro", callback_data="booking_back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"Seleziona lo slot per {new_day.capitalize()}:", reply_markup=reply_markup)
    return BOOKING_SLOT

# Esporta le funzioni e gli stati per l'integrazione in bot.py
__all__ = [
    "show_booking_settings_menu",
    "booking_day_handler",
    "slot_selection_handler",
    "change_slot_handler",
    "delete_day_handler",
    "replace_day_handler",
    "BOOKING_MENU",
    "BOOKING_MODIFY",
    "BOOKING_REPLACE",
    "BOOKING_SLOT"
]