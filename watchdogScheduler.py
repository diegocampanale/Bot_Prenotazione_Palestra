import os
import json
import logging
import time
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from prenotazione import prenotazione, ORA, MINUTI  # Funzione prenotazione(data, orario, username, password)
from telegram import Bot
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
#from bot import TOKEN
import threading
import asyncio
from booking_records import add_booking
from datetime import datetime

# Definisci lo scheduler come variabile globale
# scheduler = BackgroundScheduler()
# scheduler.start()
from scheduler_instance import scheduler

from config import TOKEN
BOT_TOKEN = TOKEN

logging.basicConfig(level=logging.INFO)

# Crea un event loop di background che rimane attivo per l'intera esecuzione
background_loop = asyncio.new_event_loop()

def start_background_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

# Avvia il background loop in un thread dedicato (solo una volta)
threading.Thread(target=start_background_loop, args=(background_loop,), daemon=True).start()

def send_message_sync(bot: Bot, chat_id: int, text: str):
    """Invia un messaggio usando il background_loop, in modo sincrono."""
    future = asyncio.run_coroutine_threadsafe(bot.send_message(chat_id=chat_id, text=text, parse_mode="MarkdownV2"), background_loop)
    return future.result()

# Costanti per la prenotazione
# ORA = 11
# MINUTI = 8

# Costanti per la schedulazione
HOURS_SCHED = 24
MINUTES_SCHED = 1

# Nome del file JSON contenente le impostazioni
CREDENTIALS_FILE = "credentials.json"

def load_credentials() -> dict:
    """Carica le informazioni dal file JSON."""
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_credentials(credentials: dict) -> None:
    with open(CREDENTIALS_FILE, "w", encoding="utf-8") as f:
        json.dump(credentials, f, indent=4, ensure_ascii=False)
        
# ... (Definizioni di get_next_occurrence, day_mapping, italian_months, SLOT_ORARI, booking_job, ecc.) ...

# Mappa dei nomi dei giorni (in italiano, senza accenti) ai numeri della settimana (lunedì=0,..., domenica=6)
day_mapping = {
    "lunedi": 0,
    "martedi": 1,
    "mercoledi": 2,
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

def get_next_occurrence(day_name: str) -> (datetime, str):
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
    next_date = next_date.replace(hour=ORA, minute=MINUTI, second=0, microsecond=0)
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
    result = prenotazione(formatted_date, slot, username, password)
    execution_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # Salva il record includendo l'ID utente (qui user_id corrisponde a chat_id se usato come ID)
    
    # add_booking(str(chat_id), day_name, slot, formatted_date, execution_time, result)
    # Aggiorna il file JSON aggiungendo il record della prenotazione completata per l'utente.
    # Carichiamo tutte le credenziali
    if result == 1:
        all_users = load_credentials()    
        user_key = str(chat_id)
        if user_key in all_users:
            user_info = all_users[user_key]
            if "completed_bookings" not in user_info:
                user_info["completed_bookings"] = []
            new_record = {
                "day": day_name,
                "slot": slot,
                "formatted_date": formatted_date,
                "execution_time": execution_time,
                "result": result
            }
            user_info["completed_bookings"].append(new_record)
            # Pulizia dei record (eliminando quelli più vecchi di 7 giorni)
            now = datetime.now()
            cleaned_records = []
            for record in user_info["completed_bookings"]:
                try:
                    record_time = datetime.strptime(record["execution_time"], '%Y-%m-%d %H:%M:%S')
                    if (now - record_time).days < 7:
                        cleaned_records.append(record)
                except Exception as ex:
                    logging.error(f"Errore nel parsing del record {record}: {ex}")
            user_info["completed_bookings"] = cleaned_records
            save_credentials(all_users)
        else:
            logging.error(f"Utente con chat_id {chat_id} non trovato nelle credenziali.")
    
    if result == 1:
        # message = f"Prenotazione per {formatted_date} (orario {orario}) eseguita con successo."
        logging.info("Prenotazione effettuata con SUCCESSO, invio messaggio di conferma.")
        message = (
            f"*Prenotazione Effettuata\!*\n\n"
            f"*Data:* `{formatted_date}`\n"
            f"*Orario:* `{orario.replace('-', '\-')}`\n\n"
            f"✅ *La prenotazione è stata completata con successo\!*\n\n"
            f"_Ci vediamo in palestra\!_")
    else:
        logging.info("Prenotazione non effettuata, invio messaggio di insuccesso.")
        message = (
            f"*Prenotazione Fallita\!*\n\n"
            f"*Data:* `{formatted_date}`\n"
            f"*Orario:* `{orario.replace('-', '\-')}`\n\n"
            f"❌ *La prenotazione non è stata completata*\n\n"
        )
        
    # Invia il messaggio tramite il bot
    try:
        send_message_sync(bot, chat_id, message)
        logging.info("Messaggio inviato tramite Telegram: " + message)
    except Exception as e:
        logging.error("Errore durante l'invio del messaggio: " + str(e))

def add_booking_jobs(scheduler, bot_token: str):
    """Legge il file JSON e aggiunge i job allo scheduler per ogni utente."""
    all_users = load_credentials()
    for user_id, info in all_users.items():
        username = info.get("username")
        password = info.get("password")
        try:
            chat_id = int(user_id)
        except ValueError:
            logging.error(f"User ID {user_id} non valido come chat_id.")
            continue

        booking_days = info.get("booking_days", {})
        if not booking_days or not username or not password:
            logging.error(f"Informazioni di prenotazione incomplete per l'utente {user_id}.")
            continue

        bot = Bot(token=bot_token)
        
        # Azzeriamo la lista dei job programmati per questo utente,
        # in modo da evitare duplicazioni durante le successive chiamate
        info["scheduled_jobs"].clear()

        for day, slot in booking_days.items():
            try:
                next_date, formatted_date = get_next_occurrence(day)
            except ValueError as e:
                logging.error(e)
                continue
            # Calcola l'orario di esecuzione: 47 ore e 59 minuti prima della data di prenotazione
            scheduled_time = next_date - timedelta(hours=HOURS_SCHED, minutes=MINUTES_SCHED)
            if scheduled_time < datetime.now():
                next_date += timedelta(days=7)
                formatted_date = f"{next_date.day} {italian_months[next_date.month]}"
                scheduled_time = next_date - timedelta(hours=HOURS_SCHED, minutes=MINUTES_SCHED)

            # Log del job pianificato
            job_info = {
                "day": day,
                "formatted_date": formatted_date,
                "slot": slot,
                "scheduled_time": scheduled_time.strftime('%Y-%m-%d %H:%M:%S')
            }

            # Aggiungi il job allo scheduler
            message = f"Scheduling booking for {day.capitalize()} ({formatted_date}), slot {slot} for user {user_id} at {job_info['scheduled_time']}"
            # message = (f"Scheduling booking for {day.capitalize()} ({formatted_date}), slot {slot} "
            #            f"for user {user_id} at {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}")
            logging.info(message)
            
            scheduler.add_job(booking_job, 'date', run_date=scheduled_time, args=[day, slot, chat_id, bot, username, password])
            # Aggiungi il record del job alla sezione scheduled_jobs per questo utente
            info["scheduled_jobs"].append(job_info)
            modified = True
            
            if modified:
                # Salva le modifiche al file JSON
                save_credentials(all_users)
                logging.info(f"Credenziali aggiornate per l'utente {user_id}.")
                
            # Invia il messaggio di conferma usando asyncio.run()
            # message = (f"*Scheduling booking* for _{day.capitalize()}_ \({formatted_date}\), slot {slot} "
            #            f"for user *{user_id}* at {scheduled_time.strftime('%Y\-%m\-%d %H:%M:%S')}")
            # send_message_sync(bot, chat_id, message)
            #print("Messaggio inviato tramite Telegram")




class CredentialsChangeHandler(FileSystemEventHandler):
    """Gestisce gli eventi di modifica del file JSON."""
    def __init__(self, scheduler, bot_token, debounce_interval=5):
        """
        debounce_interval: tempo (in secondi) da attendere tra una modifica e l'altra.
        """
        super().__init__()
        self.scheduler = scheduler
        self.bot_token = bot_token
        self.debounce_interval = debounce_interval
        self.last_event_time = 0
    

    def on_modified(self, event):
        if not event.src_path.endswith(CREDENTIALS_FILE):
            return

        current_time = time.time()
        # Se l'intervallo è inferiore al debounce_interval, ignora l'evento
        if current_time - self.last_event_time < self.debounce_interval:
            return
        self.last_event_time = current_time

        logging.info("Il file JSON è stato modificato, aggiornamento dei job...")
        self.scheduler.remove_all_jobs()
        add_booking_jobs(self.scheduler, self.bot_token)

def schedule_bookings(bot_token: str):
    """Crea e avvia lo scheduler, aggiungendo i job e avviando il file watcher."""
    add_booking_jobs(scheduler, bot_token)
    return scheduler

def start_file_watcher(scheduler, bot_token: str, path="."):
    """Avvia un file watcher per monitorare il file JSON e aggiornare i job quando viene modificato."""
    event_handler = CredentialsChangeHandler(scheduler, bot_token, debounce_interval=5)
    observer = Observer()
    observer.schedule(event_handler, path=path, recursive=False)
    observer.start()
    logging.info("File watcher avviato per credentials.json")
    return observer

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    #BOT_TOKEN = TOKEN  # Sostituisci con il token del tuo bot
    scheduler = schedule_bookings(BOT_TOKEN)
    observer = start_file_watcher(scheduler, BOT_TOKEN, path=".")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.shutdown()
        observer.stop()
        observer.join()
        logging.info("Scheduler e file watcher arrestati.")