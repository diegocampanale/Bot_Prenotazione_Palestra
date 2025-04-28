TOKEN = "7925539011:AAHvmEmEeZo4SFy47m7lNttEfxuB_HhZA6M"

import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from prenotazione import prenotazione  # Funzione definita in prenotazione.py
from telegram import Bot

# Parametri impostati manualmente
USERNAME = "s325040@studenti.polito.it"
PASSWORD = "XZdVoop0yW8zwuX"              # Sostituisci con la tua password
BOOKING_DAY = "8 aprile"             # La data da passare alla funzione prenotazione (formattata come il sito si aspetta)
SLOT = 1                             # Slot orario (ad esempio: 0 per il primo slot)
CHAT_ID = 602793492                  # ID della chat a cui inviare il messaggio
BOT_TOKEN = "7925539011:AAHvmEmEeZo4SFy47m7lNttEfxuB_HhZA6M"         # Sostituisci con il token del tuo bot

# Parametri per configurare l'orario di prenotazione (modificabili per test)
BOOKING_HOUR = 0    # Ora in cui eseguire la prenotazione (default mezzanotte)
BOOKING_MINUTE = 0  # Minuti (default 00)


def compute_next_booking_time(booking_hour: int = BOOKING_HOUR, booking_minute: int = BOOKING_MINUTE) -> datetime:
    """
    Calcola il prossimo orario in cui esattamente si raggiunge l'ora configurata.
    Se la data/ora configurata per oggi è già passata, ritorna quella del giorno successivo.
    """
    now = datetime.now()
    print(f"Current time: {now}")
    # Crea un candidato per oggi con l'orario specificato
    candidate = datetime.combine(now.date(), datetime.min.time()).replace(hour=booking_hour, minute=booking_minute)
    if candidate <= now:
        candidate += timedelta(days=1)
    return candidate

def job():
    """
    Funzione schedulata:
      - Chiama la funzione prenotazione() passando BOOKING_DAY, SLOT, USERNAME e PASSWORD.
      - In base al risultato (1 per successo, 0 per fallimento), costruisce un messaggio che include la data e lo slot orario,
        e lo invia tramite Telegram.
    """
    result = prenotazione(BOOKING_DAY, SLOT, USERNAME, PASSWORD)
    if result == 1:
        message = f"Prenotazione per il giorno {BOOKING_DAY} (slot orario {SLOT}) eseguita con successo."
    else:
        message = f"Prenotazione per il giorno {BOOKING_DAY} (slot orario {SLOT}) fallita."
    
    bot = Bot(token=BOT_TOKEN)
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(bot.send_message(chat_id=CHAT_ID, text=message))
    loop.close()
    
    logging.info(message)

def main():
    logging.basicConfig(level=logging.INFO)
    
    # Calcola il prossimo orario di prenotazione in modo dinamico,
    # utilizzando le variabili BOOKING_HOUR e BOOKING_MINUTE (modificabili per test)
    next_booking_time = compute_next_booking_time()
    logging.info(f"Scheduling booking job at {next_booking_time}")
    
    scheduler = BackgroundScheduler()
    scheduler.add_job(job, 'date', run_date=next_booking_time)
    scheduler.start()
    logging.info("Booking scheduler avviato. Attesa del job programmato...")
    
    # Invia un messaggio per confermare la programmazione del job
    bot = Bot(token=BOT_TOKEN)
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    scheduling_message = f"Job di prenotazione programmato per {next_booking_time}\n\nPrenotazione per il giorno {BOOKING_DAY} (slot orario {SLOT})"
    loop.run_until_complete(bot.send_message(chat_id=CHAT_ID, text=scheduling_message))
    loop.close()
    
    try:
        while True:
            pass  # Mantiene il processo in esecuzione
    except KeyboardInterrupt:
        scheduler.shutdown()
        logging.info("Scheduler arrestato.")

if __name__ == "__main__":
    main()