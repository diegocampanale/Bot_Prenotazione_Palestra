# booking_status_scheduler.py
import logging
import json
import os
from datetime import datetime, timedelta
from scheduler_instance import scheduler
from booking_records import completed_bookings
from watchdogScheduler import get_next_occurrence  # Assumi che SLOT_ORARI e get_next_occurrence siano definiti in booking_settings.py

SLOT_ORARI = ["14:00\-15:30", "15:30\-17:00", "17:00\-18:30", "18:30\-20:00"]

def escape_markdown_v2(text: str) -> str:
    """
    Scappa i caratteri speciali per MarkdownV2.
    I caratteri riservati sono: _ * [ ] ( ) ~ ` > # + - = | { } . !
    """
    escape_chars = r"_*[]()~`>#+-=|{}.!\\"
    for char in escape_chars:
        text = text.replace(char, f"\\{char}")
    return text

# Nome del file JSON contenente le impostazioni
CREDENTIALS_FILE = "credentials.json"

def load_credentials() -> dict:
    """Carica le informazioni dal file JSON."""
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "r") as f:
            return json.load(f)
    return {}

def get_scheduler_status(user_id: str) -> str:
    """
    Costruisce una stringa di stato che include:
      - Le prenotazioni programmate, lette dal campo "scheduled_jobs" nel file JSON
      - Le prenotazioni già effettuate (registrate in completed_bookings)
    """
    all_users = load_credentials()
    if user_id not in all_users:
        return "Nessun job schedulato\."

    info = all_users[user_id]
    username = info.get("username", "N/D")
    lines = []
    
    # Header per l'utente
    lines.append(f"📋 *Stato Prenotazioni:*")

    # Sezione Prenotazioni Programmate
    lines.append("⏰ *Prenotazioni Programmate:*")
    scheduled_jobs = info.get("scheduled_jobs", [])
    if scheduled_jobs:
        for job in scheduled_jobs:
            day = job.get("day", "N/D").capitalize()
            slot = job.get("slot", 0)
            formatted_date = job.get("formatted_date", "N/D")
            scheduled_time = job.get("scheduled_time", "N/A")
            # Aggiungo escape manuale per i caratteri statici: parentesi e trattino
            lines.append(f"• *{day}* {formatted_date} \(slot {slot}: _{SLOT_ORARI[slot]}_\) \n `{scheduled_time}`")
    else:
        lines.append("• *Nessun job schedulato*")

    lines.append("")

    lines.append("✅ *Prenotazioni Effettuate \(ultima settimana\):*")
    completed = info.get("completed_bookings", [])
    if completed:
        for rec in completed:
            day = rec.get("day", "N/D").capitalize()
            slot = rec.get("slot", 0)
            try:
                slot_desc = SLOT_ORARI[int(slot)]
            except Exception:
                slot_desc = "Slot sconosciuto"
            formatted_date = rec.get("formatted_date", "N/D")
            execution_time = rec.get("execution_time", "N/A")
            result = rec.get("result", 0)
            outcome = "Successo" if result == 1 else "Fallita"
            # Inserisco escape manuali per le parentesi e il trattino fisso
            lines.append(f"   \- *{day}* \({formatted_date}\), slot {slot} \({slot_desc}\) eseguita alle `{execution_time}`")
    else:
        lines.append("   • *Nessuna prenotazione effettuata*")

    return "\n\n".join(lines)