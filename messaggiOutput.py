
start_text = "Benvenuto nel Bot di Prenotazione Palestra del CUS TORINO di Via Braccini.\n Iinserisci le credenziali del tuo profilo CUS TORINO"
menu_text = ""

def mess_prenotazione_eseguita(formatted_date, orario):
    
    """
    Messaggio di prenotazione eseguita
    """
    return (
        "*Prenotazione Effettuata\!*\n\n"
        f"*Data:* `{formatted_date}`\n"
        f"*Orario:* `{orario.replace('-', '\-')}`\n\n"
        "✅ *La prenotazione è stata completata con successo\!*\n\n"
        "_Ci vediamo in palestra\!_"
    )
    
def mess_prenotazione_fallita(formatted_date, orario):
    
    """
    Messaggio di prenotazione fallita
    """
    return (
        "*Prenotazione Fallita\!*\n\n"
        f"*Data:* `{formatted_date}`\n"
        f"*Orario:* `{orario.replace('-', '\-')}`\n\n"
        "❌ *La prenotazione non è stata completata*\n\n"
        "_Controlla che il tuo profilo CUS TORINO sia attivo\!_"
    )

