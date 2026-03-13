from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

from app.services.drive_watcher import DriveWatcher

logger = logging.getLogger(__name__)

class AppScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.drive_watcher = DriveWatcher()

    def start(self):
        """Inicia o agendador."""
        # Agenda sync do Drive para rodar diariamente as 08:00 e 14:00
        # Para testes debug, vamos rodar a cada 10 minutos se estiver em DEBUG
        # Mas para MVP producao:
        
        # Trigger: Seg-Sex as 08:00 e 14:00
        trigger = CronTrigger(day_of_week='mon-fri', hour='8,14', minute='0')
        
        self.scheduler.add_job(
            self.drive_watcher.check_for_updates,
            trigger=trigger,
            id='drive_sync_job',
            name='Sync Google Drive',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("Scheduler iniciado. Jobs agendados: Drive Sync (08:00, 14:00)")

    def shutdown(self):
        """Para o agendador."""
        self.scheduler.shutdown()
        logger.info("Scheduler finalizado.")

scheduler = AppScheduler()
