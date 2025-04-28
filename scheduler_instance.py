# scheduler_instance.py
from apscheduler.schedulers.background import BackgroundScheduler
import logging

scheduler = BackgroundScheduler()
scheduler.start()
logging.basicConfig(level=logging.INFO)
logging.info("Scheduler avviato in scheduler_instance.py")