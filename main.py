import time
import threading
from apscheduler.schedulers.background import BackgroundScheduler
from watchdog.observers import Observer
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ConversationHandler, 
    ContextTypes, MessageHandler, filters
)
import logging

# Importa le funzioni del modulo di scheduling (watchdogScheduler)
from watchdogScheduler import schedule_bookings, start_file_watcher
# Importa i tuoi handler per il bot
from bot import (
    start_command, menu_option, cancel, ask_username, ask_password, TOKEN,
    ASK_USERNAME, ASK_PASSWORD, MENU, MODIFY_MENU, MODIFY_USERNAME, MODIFY_PASSWORD,
    CONFIRM_DELETE, BOOKING_MENU, BOOKING_MODIFY, BOOKING_REPLACE, BOOKING_SLOT,
    show_modification_menu, account_modification_handler, process_modify_username,
    process_modify_password, confirm_delete, show_booking_settings_menu,
    booking_day_handler, slot_selection_handler, change_slot_handler, delete_day_handler,
    replace_day_handler
)
BOT_TOKEN = TOKEN  # Il token del bot

def run_scheduler():
    # Avvia lo scheduler e il file watcher nel thread separato
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

def main():
    logging.basicConfig(level=logging.INFO)
    
    # Avvia lo scheduler in un thread separato
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    # Configura il bot: crea l'applicazione e aggiungi gli handler
    application = Application.builder().token(TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_command)],
        states={
            ASK_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_username)],
            ASK_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_password)],
            MENU: [CallbackQueryHandler(menu_option)],
            # Nuovi stati per il flusso di modifica account
            MODIFY_MENU: [CallbackQueryHandler(account_modification_handler)],
            MODIFY_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_modify_username)],
            MODIFY_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_modify_password)],
            CONFIRM_DELETE: [CommandHandler("confirm", confirm_delete)],
            # Stati per il flusso "Imposta giorni/orario"
            BOOKING_MENU: [CallbackQueryHandler(booking_day_handler)],
            BOOKING_MODIFY: [CallbackQueryHandler(booking_day_handler)],
            BOOKING_REPLACE: [CallbackQueryHandler(replace_day_handler)],
            BOOKING_SLOT: [
                CallbackQueryHandler(slot_selection_handler),
                MessageHandler(filters.TEXT & ~filters.COMMAND, slot_selection_handler)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )
    application.add_handler(conv_handler)
    # Altri handler, se necessari
    application.add_handler(CallbackQueryHandler(menu_option))
    
    logging.info("Bot e Scheduler avviati. In attesa di interazioni...")
    
    # Avvia il bot nel thread principale
    application.run_polling()

if __name__ == "__main__":
    main()