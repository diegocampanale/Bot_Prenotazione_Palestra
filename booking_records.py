# booking_records.py

# Inizializza un dizionario per memorizzare le prenotazioni completate per ogni utente.
# La chiave sarà l'ID dell'utente, il valore una lista di record.
completed_bookings = {}

def add_booking(user_id: str, day: str, slot: int, formatted_date: str, execution_time: str, result: int):
    """
    Aggiunge un record di prenotazione completata per l'utente specificato.
    """
    record = {
        "day": day,
        "slot": slot,
        "formatted_date": formatted_date,
        "execution_time": execution_time,
        "result": result  # 1 per successo, 0 per fallimento
    }
    if user_id in completed_bookings:
        completed_bookings[user_id].append(record)
    else:
        completed_bookings[user_id] = [record]