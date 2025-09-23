from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging
import os

logger = logging.getLogger(__name__)


def update_rankings_job():
    """Job function to update rankings by calling the service function directly"""
    try:
        # Import the factory and the service
        from app import create_app  # <-- Import the factory
        from app.rating.services import take_rank_snapshot

        # Create a new app instance just for this job
        app = create_app()

        with app.app_context():
            # Update rankings for all gender types
            take_rank_snapshot('all')
            take_rank_snapshot('male')
            take_rank_snapshot('female')
            take_rank_snapshot('autumn_2025')

            logger.info("Rankings updated successfully via scheduler for all player types")

    except Exception as e:
        logger.error(f"Error updating rankings via scheduler: {str(e)}")


def init_scheduler(app):
    """Initialize the scheduler with the Flask app"""
    if not app.config.get('SCHEDULER_ENABLED', False):
        return

    # Only run scheduler on one worker to avoid duplicate jobs
    # Use a simple approach: only run on the worker with the lowest PID
    current_pid = os.getpid()

    # Create a lock file to ensure only one worker initializes the scheduler
    lock_file = '/tmp/scheduler_lock'
    try:
        # Try to create lock file exclusively
        with open(lock_file, 'x') as f:
            f.write(str(current_pid))
        should_run_scheduler = True
        logger.info(f"Worker PID {current_pid} acquired scheduler lock")
    except FileExistsError:
        # Another worker already has the lock
        should_run_scheduler = False
        logger.info(f"Worker PID {current_pid} - scheduler already running on another worker")

    if not should_run_scheduler:
        return

    scheduler = BackgroundScheduler()

    # Schedule daily at 23:00 UTC
    scheduler.add_job(
        func=update_rankings_job,
        trigger=CronTrigger(hour=23, minute=0, timezone='UTC'),
        id='update_rankings_daily',
        name='Update rankings daily at 23:00 UTC',
        replace_existing=True
    )

    scheduler.start()
    logger.info(f"Scheduler initialized on worker PID {current_pid} - Rankings will update daily at 23:00 UTC")

    # Shutdown scheduler and cleanup lock when app context is destroyed
    def cleanup():
        scheduler.shutdown()
        try:
            os.remove(lock_file)
            logger.info(f"Scheduler lock file removed by PID {current_pid}")
        except FileNotFoundError:
            pass

    import atexit
    atexit.register(cleanup)
