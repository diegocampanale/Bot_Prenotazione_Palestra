import os
import json
import logging
import time
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from prenotazione import prenotazione  # La funzione prenotazione(data, orario, username, password)
from telegram import Bot
from config import TOKEN

# Nome del file JSON contenente le impostazioni
CREDENTIALS_FILE = "credentials.json"

def load_credentials() -> dict:
    """Carica le informazioni dal file JSON."""
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "r") as f:
            return json.load(f)
    return {}

# Mappa dei nomi dei giorni (in italiano, senza accenti) ai numeri della settimana (lunedì=0,..., domenica=6)
day_mapping = {
    "lunedi": 0,
    "martedi": 1,
    "mercedi": 2,
    "giovedi": 3,
    "venerdi": 4,
    "sabato": 5,
    "domenica": 6
}

# Mappa dei mesi in italiano, per formattare la data
italian_months = {
    1: "gennaio", 2: "febbraio", 3: "marzo", 4: "aprile", 5: "maggio",
    6: "giugno", 7: "luglio", 8: "agosto", 9: "settembre", 10: "ottobre",
    11: "novembre", 12: "dicembre"
}

def get_next_occurrence(day_name: str) -> tuple[datetime, str]:
    """
    Calcola la prossima occorrenza del giorno della settimana specificato (es. "martedi").
    Restituisce:
      - un oggetto datetime (impostato a mezzanotte)
      - una stringa formattata, ad es. "4 aprile"
    """
    day_key = day_name.lower()
    if day_key not in day_mapping:
        raise ValueError(f"Giorno non valido: {day_name}")
    target_weekday = day_mapping[day_key]
    today = datetime.now()
    days_ahead = target_weekday - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    next_date = today + timedelta(days=days_ahead)
    next_date = next_date.replace(hour=0, minute=0, second=0, microsecond=0)
    formatted_date = f"{next_date.day} {italian_months[next_date.month]}"
    return next_date, formatted_date

# Assumiamo di avere una lista di orari corrispondenti agli slot (ad es. 0,1,2,3)
SLOT_ORARI = ["14:00-15:30", "15:30-17:00", "17:00-18:30", "18:30-20:00"]
    
def booking_job(day_name: str, slot: int, chat_id: int, bot: Bot, username: str, password: str):
    """
    Funzione schedulata:
      - Calcola la prossima occorrenza del giorno 'day_name'
      - Richiama la funzione prenotazione() passando:
            * la data formattata (es. "4 aprile"),
            * l'orario (derivato da SLOT_ORARI in base allo slot),
            * username e password.
      - Invia un messaggio all'utente tramite Telegram in base al risultato.
    """
    
    try:
        next_date, formatted_date = get_next_occurrence(day_name)
    except ValueError as e:
        logging.error(e)
        return

    # Ottieni l'orario corrispondente al slot
    orario = SLOT_ORARI[slot]
    # Chiama la funzione prenotazione, che accetta (data, orario, username, password)
    result = prenotazione(formatted_date, orario, username, password)
    if result == 1:
        message = f"Prenotazione per {formatted_date} (orario {orario}) eseguita con successo."
    else:
        message = f"Prenotazione per {formatted_date} (orario {orario}) fallita."
    # Invia il messaggio tramite il bot
    bot.send_message(chat_id=chat_id, text=message)
    logging.info(message)

def add_booking_jobs(scheduler, bot_token: str):
   # Carica le informazioni di tutti gli utenti
    all_users = load_credentials()
    for user_id, info in all_users.items():
        username = info.get("username")
        password = info.get("password")
        # Poiché il file JSON non contiene un campo "chat_id", usiamo la chiave come chat_id
        try:
            chat_id = int(user_id)
            print(f"Chat ID: {chat_id}")
        except ValueError:
            logging.error(f"User ID {user_id} non valido come chat_id.")
            continue

        booking_days = info.get("booking_days", {})
        if not booking_days or not username or not password:
            logging.error(f"Informazioni di prenotazione incomplete per l'utente {user_id}.")
            continue
        
        bot = Bot(token=BOT_TOKEN)

        for day, slot in booking_days.items():
            try:
                next_date, formatted_date = get_next_occurrence(day)
            except ValueError as e:
                logging.error(e)
                continue

            # Calcola l'orario di esecuzione: 47 ore e 59 minuti prima della data di prenotazione
            scheduled_time = next_date - timedelta(hours=48, minutes=1)
            # Se l'orario di esecuzione è passato, pianifica per la prossima occorrenza (aggiungi 7 giorni)
            if scheduled_time < datetime.now():
                next_date = next_date + timedelta(days=7)
                scheduled_time = next_date - timedelta(hours=48, minutes=1)

            message = f"Scheduling booking for {day} ({formatted_date}), slot {slot} for user {user_id} at {scheduled_time}"
            logging.info(message)
            scheduler.add_job(booking_job, 'date', run_date=scheduled_time, args=[day, slot, chat_id, bot, username, password])
            # Invia un messaggio di conferma all'utente
            confirmation_message = f"Prenotazione programmata per {formatted_date} (orario {SLOT_ORARI[slot]})"
            bot.send_message(chat_id=chat_id, text=confirmation_message)
            

def schedule_bookings(bot_token: str):
    """
    Crea e avvia lo scheduler, aggiungendo i job in base alle informazioni del file JSON.
    """
    scheduler = BackgroundScheduler()
    scheduler.start()
    add_booking_jobs(scheduler, bot_token)
    return scheduler

def poll_json(scheduler, bot_token: str, poll_interval: int = 30):
    """
    Esegue un polling continuo sul file JSON per verificare modifiche.
    Se il file viene modificato, rimuove tutti i job dallo scheduler e li riprogramma.
    """
    last_mod_time = os.path.getmtime(CREDENTIALS_FILE) if os.path.exists(CREDENTIALS_FILE) else None
    while True:
        time.sleep(poll_interval)
        if not os.path.exists(CREDENTIALS_FILE):
            continue
        current_mod_time = os.path.getmtime(CREDENTIALS_FILE)
        if last_mod_time is None or current_mod_time != last_mod_time:
            logging.info("Il file JSON è stato modificato, aggiornamento dei job...")
            last_mod_time = current_mod_time
            scheduler.remove_all_jobs()
            add_booking_jobs(scheduler, bot_token)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    BOT_TOKEN = TOKEN  # Sostituisci con il token del tuo bot
    scheduler = schedule_bookings(BOT_TOKEN)
    try:
        poll_json(scheduler, BOT_TOKEN, poll_interval=10)
    except KeyboardInterrupt:
        scheduler.shutdown()
        logging.info("Scheduler arrestato.")