import os
import json
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from account_edit import (
    show_modification_menu,
    account_modification_handler,
    MODIFY_MENU,
    MODIFY_USERNAME,
    MODIFY_PASSWORD,
    CONFIRM_DELETE,
    process_modify_username,
    process_modify_password,
    confirm_delete,)

from booking_settings import (
    show_booking_settings_menu,
    booking_day_handler,
    slot_selection_handler,
    change_slot_handler,
    delete_day_handler,
    replace_day_handler,
    BOOKING_MENU,
    BOOKING_MODIFY,
    BOOKING_REPLACE,
    BOOKING_SLOT
)

from booking_status import get_scheduler_status
from config import TOKEN

# Definisci gli stati della conversazione
ASK_USERNAME, ASK_PASSWORD, MENU = range(3)

# File in cui salvare le credenziali (in formato JSON)
CREDENTIALS_FILE = "credentials.json"

def load_credentials() -> dict:
    """Carica le credenziali dal file JSON se esiste, altrimenti restituisce un dizionario vuoto."""
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_credentials(credentials: dict) -> None:
    """Salva il dizionario delle credenziali nel file JSON."""
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(credentials, f, indent=4, ensure_ascii=False)

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Mostra il menu principale con le opzioni disponibili."""
    keyboard = [
        [InlineKeyboardButton("Imposta giorni/orario", callback_data="set_default")],
        [InlineKeyboardButton("Verifica stato prenotazioni", callback_data="check_status")],
        [InlineKeyboardButton("Cancella prenotazione", callback_data="cancel_reservation")],
        [InlineKeyboardButton("Modifica informazioni account", callback_data="modify_account")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Se il comando viene inviato come messaggio:
    if update.message:
        await update.message.reply_text("Seleziona un'opzione:", reply_markup=reply_markup)
    # Se invece proviene da una callback:
    elif update.callback_query:
        await update.callback_query.edit_message_text("Seleziona un'opzione:", reply_markup=reply_markup)
    return MENU

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Resetta eventuali dati della conversazione (cancella lo stato)
    context.user_data.clear()
    # Ora prosegui con il flusso di /start
    """
    Gestisce il comando /start.
    Se le credenziali dell'utente sono già salvate, saluta l'utente;
    altrimenti, chiede di inserire le credenziali.
    """
    user_id = str(update.message.from_user.id)
    creds = load_credentials()
    
    if user_id in creds:
        username = creds[user_id]['username']
        await update.message.reply_text(f"Benvenuto, *{update.message.from_user.first_name}*\!",parse_mode=ParseMode.MARKDOWN_V2)
        # Qui puoi mostrare il menu principale o proseguire in altro modo
        return await show_menu(update, context)
    else:
        msg = (
            "*Bot Prenotazione Palestra CUS*\n\n"
            "Benvenuto nel Bot di Prenotazione Palestra del CUS TORINO di Via Braccini\n\n"
            "Inserisci le credenziali del tuo profilo CUS TORINO"
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN_V2)
        await update.message.reply_text("Username:")
        return ASK_USERNAME

async def ask_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Riceve lo username, lo salva in user_data e chiede la password."""
    username = update.message.text
    context.user_data["username"] = username
    await update.message.reply_text("Inserisci la tua password:")
    return ASK_PASSWORD

async def ask_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Riceve la password, salva le credenziali in un file JSON e conferma all'utente."""
    password = update.message.text
    context.user_data["password"] = password
    user_id = str(update.message.from_user.id)
    
    # Carica le credenziali esistenti
    creds = load_credentials()
    # Aggiorna o aggiunge le credenziali dell'utente, inizializzando anche "booking_days" come dizionario vuoto
    creds[user_id] = {
        "name": update.message.from_user.name,
        "username": context.user_data["username"],
        "password": context.user_data["password"],
        "booking_days": {},
        "scheduled_jobs": [],
        "completed_bookings": []
    }
    save_credentials(creds)
    await update.message.reply_text("Le tue credenziali sono state salvate!")
    return await show_menu(update, context)

async def menu_option(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Gestisce il callback dei pulsanti del menu, inclusa l'opzione 'Torna indietro'."""
    query = update.callback_query
    await query.answer()
    selection = query.data
    logging.info(f"Callback data ricevuto: {selection}")

    if selection == "set_default":
        return await show_booking_settings_menu(update, context)
        #text = "Hai selezionato 'Imposta giorni/orario'. (Funzionalità in costruzione)"
    elif selection == "check_status":
        print("Verifica stato prenotazioni selezionata")
        # text = "Hai selezionato 'Verifica stato prenotazioni'. (Funzionalità in costruzione)"
        user_id = str(update.effective_user.id)
        status_message = get_scheduler_status(user_id)
        if not status_message:
            status_message = "[Errore] Nessun job schedulato\."
            
        # Crea una tastiera inline con il pulsante "Torna indietro"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Torna indietro", callback_data="back")]])

        # Invia il messaggio di stato; assicurati che eventuali caratteri speciali siano scappati se usi MarkdownV2
        await query.edit_message_text(status_message, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=keyboard)
        return MENU
    
    elif selection == "cancel_reservation":
        text = "Hai selezionato 'Cancella prenotazione'. \n(Funzionalità in costruzione)\n\n Vai sul sito CUS TORINO per cancellare la prenotazione."
    elif selection == "modify_account":
        print("Modifica account selezionata")
        #text = "Hai selezionato 'Modifica Informazioni Account'. (Funzionalità in costruzione)"
        return await show_modification_menu(update, context)
    elif selection == "back":
        return await show_menu(update, context)
    else:
        text = "MENU: Opzione non riconosciuta."

    # Aggiunge un pulsante "Torna indietro" per tornare al menu principale
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Torna indietro", callback_data="back")]])
    await query.edit_message_text(text, reply_markup=keyboard)
    return MENU

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Annulla la conversazione."""
    await update.message.reply_text("Operazione annullata.")
    return ConversationHandler.END

def main():
    
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
    )
    TOKEN = "7105192398:AAFh62xMU6CScmDZvLT_u1DpTXHt5neOaho"
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_command)],
        states={
            ASK_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_username)],
            ASK_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_password)],
            MENU: [CallbackQueryHandler(menu_option)],
            #Nuovi stati per il flusso di modifica account
            MODIFY_MENU: [CallbackQueryHandler(account_modification_handler)],
            MODIFY_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_modify_username)],
            MODIFY_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_modify_password)],
            CONFIRM_DELETE: [CommandHandler("confirm", confirm_delete)],
            # Stati per il flusso "Imposta giorni/orario"
            BOOKING_MENU: [CallbackQueryHandler(booking_day_handler)],
            BOOKING_MODIFY: [CallbackQueryHandler(booking_day_handler)],
            BOOKING_REPLACE: [CallbackQueryHandler(replace_day_handler)],
            BOOKING_SLOT: [CallbackQueryHandler(slot_selection_handler),
                            MessageHandler(filters.TEXT & ~filters.COMMAND, slot_selection_handler)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    application.add_handler(conv_handler)
    print("bot in ascolto...")
    application.run_polling()

if __name__ == '__main__':
    main()