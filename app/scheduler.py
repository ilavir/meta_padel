from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import atexit
import logging
import os
import signal

logger = logging.getLogger(__name__)

# Exposed as a module-level constant (rather than inlined in init_scheduler)
# so tests can point it at a temp file instead of the real /tmp path.
SCHEDULER_LOCK_FILE = '/tmp/scheduler_lock'

# Lock-file based mutex ensuring only one Gunicorn worker runs the
# scheduler. A worker that is killed hard (e.g. `SIGKILL` after a
# `WORKER TIMEOUT`/OOM) never runs its `atexit` handlers, so the lock file
# can be left behind holding a PID that no longer exists. To recover from
# that, the lock file's PID is checked for liveness (`os.kill(pid, 0)`)
# before treating an existing lock as active: a dead/invalid PID means the
# lock is stale and is reclaimed via an atomic create-or-fail
# (`O_CREAT | O_EXCL`), which also arbitrates any concurrent reclaim race
# between workers cleanly (only one `os.open` call can win).


def _read_lock_pid(lock_file):
    """Read the PID stored in the scheduler lock file.

    Returns the PID as an int, or None if the file is missing, empty, or
    contains a non-numeric value.
    """
    try:
        with open(lock_file, 'r') as f:
            content = f.read().strip()
    except (FileNotFoundError, OSError):
        return None

    if not content:
        return None

    try:
        return int(content)
    except ValueError:
        return None


def _is_process_alive(pid):
    """Check whether a process with the given PID is currently alive."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        # Process exists but we lack permission to signal it - treat as alive.
        return True
    except OSError:
        return False
    return True


def _acquire_scheduler_lock(lock_file, max_retries=5):
    """Attempt to atomically acquire the scheduler lock.

    Uses `os.open` with `O_CREAT | O_EXCL` so the create-or-fail check is
    atomic even across processes. If the lock file already exists, the
    PID stored in it is checked for liveness:
      - alive: another worker legitimately holds the lock -> give up.
      - dead/invalid: the previous holder crashed without cleaning up
        (SIGKILL bypasses `atexit`) -> remove the stale file and retry,
        bounded by `max_retries` in case another worker wins the reclaim
        race first.

    Returns True if the lock was acquired by the current process.
    """
    current_pid = os.getpid()

    for _ in range(max_retries):
        try:
            fd = os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            try:
                os.write(fd, str(current_pid).encode())
            finally:
                os.close(fd)
            return True
        except FileExistsError:
            holder_pid = _read_lock_pid(lock_file)
            if holder_pid is not None and _is_process_alive(holder_pid):
                return False

            # Stale or invalid lock - reclaim it and retry the atomic create.
            try:
                os.remove(lock_file)
            except FileNotFoundError:
                pass
            except OSError:
                return False

    return False


def update_rankings_job():
    """Job function to update rankings by calling the service function directly"""
    try:
        # Import the factory and the service
        from app import create_app  # <-- Import the factory
        from app.rating.services import take_rank_snapshot

        # Create a new app instance just for this job
        app = create_app()

        with app.app_context():
            # Update rankings for all gender types and current season
            take_rank_snapshot('all')
            take_rank_snapshot('male')
            take_rank_snapshot('female')
            take_rank_snapshot('summer_2026')

            logger.info("Rankings updated successfully via scheduler for all player types")

    except Exception as e:
        logger.error(f"Error updating rankings via scheduler: {str(e)}")


def init_scheduler(app):
    """Initialize the scheduler with the Flask app"""
    if not app.config.get('SCHEDULER_ENABLED', False):
        return

    # Only run scheduler on one worker to avoid duplicate jobs
    current_pid = os.getpid()

    # Lock file to ensure only one worker initializes the scheduler. See the
    # module-level comment above for why this needs to survive stale locks.
    lock_file = SCHEDULER_LOCK_FILE
    if _acquire_scheduler_lock(lock_file):
        logger.info(f"Worker PID {current_pid} acquired scheduler lock")
    else:
        logger.info(f"Worker PID {current_pid} - scheduler already running on another worker")
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

    # Shutdown scheduler and cleanup lock when the process exits normally.
    # `atexit` alone is not sufficient: it does not run on SIGKILL (the
    # signal a Gunicorn worker receives on a hard timeout/OOM kill), which
    # is exactly the scenario that leaks the lock file. The liveness check
    # in `_acquire_scheduler_lock` is the backstop for that case. A guarded
    # SIGTERM handler is added here to cover the graceful-shutdown path too,
    # chaining to whatever handler (e.g. Gunicorn's own) was already
    # installed so existing shutdown behavior is preserved.
    cleanup_done = {'value': False}

    def cleanup():
        if cleanup_done['value']:
            return
        cleanup_done['value'] = True
        scheduler.shutdown()
        try:
            os.remove(lock_file)
            logger.info(f"Scheduler lock file removed by PID {current_pid}")
        except FileNotFoundError:
            pass

    atexit.register(cleanup)

    previous_sigterm_handler = signal.getsignal(signal.SIGTERM)

    def _handle_sigterm(signum, frame):
        cleanup()
        if callable(previous_sigterm_handler):
            previous_sigterm_handler(signum, frame)
        elif previous_sigterm_handler == signal.SIG_DFL:
            signal.signal(signal.SIGTERM, signal.SIG_DFL)
            os.kill(os.getpid(), signal.SIGTERM)

    try:
        signal.signal(signal.SIGTERM, _handle_sigterm)
    except (ValueError, OSError):
        # signal.signal only works in the main thread of the main
        # interpreter; skip registration in any other context.
        pass
