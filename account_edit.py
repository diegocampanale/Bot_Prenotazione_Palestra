import os
import logging
import json

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

# Definiamo gli stati per la modifica dell'account (scegli numeri non in conflitto con quelli già usati)
MODIFY_MENU, MODIFY_USERNAME, MODIFY_PASSWORD, CONFIRM_DELETE = range(3, 7)

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
        json.dump(credentials, f)

async def show_modification_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [InlineKeyboardButton("Cancella Credenziali", callback_data="delete_account")],
        [InlineKeyboardButton("Modifica Username", callback_data="modify_username")],
        [InlineKeyboardButton("Modifica Password", callback_data="modify_password")],
        [InlineKeyboardButton("Torna Indietro", callback_data="back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.edit_message_text("Seleziona l'opzione di modifica account:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Seleziona l'opzione di modifica account:", reply_markup=reply_markup)
    return MODIFY_MENU

async def account_modification_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    selection = query.data.strip().lower()  # Normalizza per evitare differenze di maiuscole/spazi

    if selection == "delete_account":
        await query.edit_message_text("Sei sicuro di voler cancellare le tue credenziali?\nInvia /confirm per confermare.")
        return CONFIRM_DELETE
    elif selection == "modify_username":
        await query.edit_message_text("Inserisci il nuovo username:")
        return MODIFY_USERNAME
    elif selection == "modify_password":
        await query.edit_message_text("Inserisci la nuova password:")
        return MODIFY_PASSWORD
    elif selection == "back":
        print("selection: ", selection)
        # Torna al menu principale
        from bot import show_menu
        return await show_menu(update, context)
    else:
        await query.edit_message_text("Opzione non riconosciuta. Riprova.")
        return MODIFY_MENU

async def process_modify_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Aggiorna solo lo username dell'utente."""
    new_username = update.message.text
    user_id = str(update.message.from_user.id)
    creds = load_credentials()
    if user_id in creds:
        creds[user_id]["username"] = new_username
        save_credentials(creds)
        await update.message.reply_text(f"Username aggiornato a: {new_username}")
    else:
        await update.message.reply_text("Nessuna registrazione trovata per il tuo account.")
    return await show_modification_menu(update, context)

async def process_modify_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Aggiorna solo la password dell'utente."""
    new_password = update.message.text
    user_id = str(update.message.from_user.id)
    creds = load_credentials()
    if user_id in creds:
        creds[user_id]["password"] = new_password
        save_credentials(creds)
        await update.message.reply_text("Password aggiornata.")
    else:
        await update.message.reply_text("Nessuna registrazione trovata per il tuo account.")
    return await show_modification_menu(update, context)

async def confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancella le credenziali dell'utente dopo la conferma."""
    user_id = str(update.message.from_user.id)
    creds = load_credentials()
    if user_id in creds:
        del creds[user_id]
        save_credentials(creds)
        await update.message.reply_text("Le tue credenziali sono state cancellate.")
    else:
        await update.message.reply_text("Nessuna registrazione trovata per il tuo account.")
    await update.message.reply_text("Premi /start per tornare al menu principale.")
    return ConversationHandler.END

async def cancel_modification(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Annulla il processo di modifica account."""
    await update.message.reply_text("Operazione annullata.")
    return ConversationHandler.END