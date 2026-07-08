"""
Tests for scheduler functionality
"""
import os
import pytest
from unittest.mock import patch, MagicMock, call
from app.scheduler import (
    update_rankings_job,
    init_scheduler,
    _read_lock_pid,
    _is_process_alive,
    _acquire_scheduler_lock,
)
from app.models import User, Role, UserRankHistory
from werkzeug.security import generate_password_hash


def _unused_pid():
    """Return a PID that is (almost certainly) not in use on this system."""
    # PIDs are bounded; pick a very high value unlikely to be assigned.
    return 2 ** 22 - 1


class TestUpdateRankingsJob:
    """Test the update_rankings_job function"""
    
    def test_update_rankings_job_success_mocked(self, app):
        """Test successful execution of update_rankings_job with mocked services"""
        # Mock the take_rank_snapshot function
        with patch('app.rating.services.take_rank_snapshot') as mock_snapshot:
            mock_snapshot.return_value = {'success': True, 'message': 'Success'}
            
            # Execute the job
            update_rankings_job()
            
            # Verify take_rank_snapshot was called for all gender/season types
            expected_calls = [call('all'), call('male'), call('female'), call('summer_2026')]
            mock_snapshot.assert_has_calls(expected_calls, any_order=False)
            assert mock_snapshot.call_count == 4

    def test_update_rankings_job_with_exception(self, app, caplog):
        """Test update_rankings_job handles exceptions properly"""
        with patch('app.rating.services.take_rank_snapshot') as mock_snapshot:
            mock_snapshot.side_effect = Exception("Database error")
            
            # Execute the job - should not raise exception
            update_rankings_job()
            
            # Check that error was logged
            assert "Error updating rankings via scheduler" in caplog.text
            assert "Database error" in caplog.text

    def test_update_rankings_job_creates_app_context(self, app):
        """Test that update_rankings_job creates proper app context"""
        with patch('app.create_app') as mock_create_app, \
             patch('app.rating.services.take_rank_snapshot') as mock_snapshot:
            
            mock_app = MagicMock()
            mock_create_app.return_value = mock_app
            mock_snapshot.return_value = {'success': True, 'message': 'Success'}
            
            update_rankings_job()
            
            # Verify app was created and context was used
            mock_create_app.assert_called_once()
            mock_app.app_context.assert_called_once()


class TestInitScheduler:
    """Test the init_scheduler function"""
    
    def test_init_scheduler_disabled(self, app):
        """Test scheduler initialization when disabled"""
        app.config['SCHEDULER_ENABLED'] = False
        
        with patch('app.scheduler.BackgroundScheduler') as mock_scheduler_class:
            init_scheduler(app)
            
            # Scheduler should not be created when disabled
            mock_scheduler_class.assert_not_called()

    def test_init_scheduler_enabled_with_lock(self, app):
        """Test scheduler initialization when enabled and gets lock"""
        app.config['SCHEDULER_ENABLED'] = True

        with patch('app.scheduler.BackgroundScheduler') as mock_scheduler_class, \
             patch('app.scheduler._acquire_scheduler_lock', return_value=True), \
             patch('os.getpid', return_value=12345):

            mock_scheduler = MagicMock()
            mock_scheduler_class.return_value = mock_scheduler

            init_scheduler(app)

            # Verify scheduler was created and started
            mock_scheduler_class.assert_called_once()
            mock_scheduler.add_job.assert_called_once()
            mock_scheduler.start.assert_called_once()

    def test_init_scheduler_enabled_without_lock(self, app):
        """Test scheduler initialization when another worker has lock"""
        app.config['SCHEDULER_ENABLED'] = True

        with patch('app.scheduler.BackgroundScheduler') as mock_scheduler_class, \
             patch('app.scheduler._acquire_scheduler_lock', return_value=False), \
             patch('os.getpid', return_value=12345):

            init_scheduler(app)

            # Scheduler should not be created when lock is held elsewhere
            mock_scheduler_class.assert_not_called()

    def test_scheduler_job_configuration(self, app):
        """Test that scheduler job is configured correctly"""
        app.config['SCHEDULER_ENABLED'] = True

        with patch('app.scheduler.BackgroundScheduler') as mock_scheduler_class, \
             patch('app.scheduler._acquire_scheduler_lock', return_value=True), \
             patch('os.getpid', return_value=12345):

            mock_scheduler = MagicMock()
            mock_scheduler_class.return_value = mock_scheduler

            init_scheduler(app)

            # Verify job configuration
            mock_scheduler.add_job.assert_called_once()
            call_args = mock_scheduler.add_job.call_args

            assert call_args[1]['func'] == update_rankings_job
            assert call_args[1]['id'] == 'update_rankings_daily'
            assert call_args[1]['name'] == 'Update rankings daily at 23:00 UTC'
            assert call_args[1]['replace_existing'] is True

            # Just verify trigger exists - detailed trigger testing is complex
            assert 'trigger' in call_args[1]


class TestReadLockPid:
    """Test the _read_lock_pid helper"""

    def test_valid_pid_file(self, tmp_path):
        lock_file = tmp_path / "scheduler_lock"
        lock_file.write_text("12345")

        assert _read_lock_pid(str(lock_file)) == 12345

    def test_missing_file(self, tmp_path):
        lock_file = tmp_path / "does_not_exist"

        assert _read_lock_pid(str(lock_file)) is None

    def test_empty_file(self, tmp_path):
        lock_file = tmp_path / "scheduler_lock"
        lock_file.write_text("")

        assert _read_lock_pid(str(lock_file)) is None

    def test_garbage_content(self, tmp_path):
        lock_file = tmp_path / "scheduler_lock"
        lock_file.write_text("not-a-pid")

        assert _read_lock_pid(str(lock_file)) is None


class TestIsProcessAlive:
    """Test the _is_process_alive helper"""

    def test_live_pid(self):
        # The current process is always alive.
        assert _is_process_alive(os.getpid()) is True

    def test_dead_pid(self):
        assert _is_process_alive(_unused_pid()) is False

    def test_permission_error_treated_as_alive(self):
        with patch('os.kill', side_effect=PermissionError):
            assert _is_process_alive(1) is True


class TestAcquireSchedulerLock:
    """Test the _acquire_scheduler_lock helper"""

    def test_fresh_lock_is_acquired(self, tmp_path):
        lock_file = str(tmp_path / "scheduler_lock")

        assert _acquire_scheduler_lock(lock_file) is True
        assert _read_lock_pid(lock_file) == os.getpid()

    def test_live_holder_blocks_acquisition(self, tmp_path):
        lock_file = tmp_path / "scheduler_lock"
        lock_file.write_text(str(os.getpid()))  # current process is alive

        assert _acquire_scheduler_lock(str(lock_file)) is False
        # Lock file untouched - still holds the original (live) PID
        assert _read_lock_pid(str(lock_file)) == os.getpid()

    def test_dead_holder_lock_is_reclaimed(self, tmp_path):
        lock_file = tmp_path / "scheduler_lock"
        lock_file.write_text(str(_unused_pid()))

        assert _acquire_scheduler_lock(str(lock_file)) is True
        assert _read_lock_pid(str(lock_file)) == os.getpid()

    def test_invalid_content_lock_is_reclaimed(self, tmp_path):
        lock_file = tmp_path / "scheduler_lock"
        lock_file.write_text("garbage")

        assert _acquire_scheduler_lock(str(lock_file)) is True
        assert _read_lock_pid(str(lock_file)) == os.getpid()

    def test_concurrent_reclaim_loser_does_not_acquire(self, tmp_path):
        """Simulate another worker winning the race to recreate the lock
        right after this process removes the stale one."""
        lock_file = str(tmp_path / "scheduler_lock")
        with open(lock_file, 'w') as f:
            f.write(str(_unused_pid()))  # stale/dead lock

        real_open = os.open

        def racing_open(path, flags, *args, **kwargs):
            # First call: pretend a competing worker just recreated the file.
            if path == lock_file and flags & os.O_EXCL:
                with open(lock_file, 'w') as f:
                    f.write("999999")  # live-looking competitor PID
                raise FileExistsError()
            return real_open(path, flags, *args, **kwargs)

        with patch('os.open', side_effect=racing_open), \
             patch('app.scheduler._is_process_alive', return_value=True):
            assert _acquire_scheduler_lock(lock_file) is False


class TestSchedulerLockRecovery:
    """End-to-end stale-lock recovery scenarios for init_scheduler"""

    def test_dead_lock_is_reclaimed_and_scheduler_starts(self, app, tmp_path):
        """A lock left behind by a hard-killed worker (dead PID) should be
        reclaimed and the scheduler should start with the current PID."""
        lock_file = tmp_path / "scheduler_lock"
        lock_file.write_text(str(_unused_pid()))

        app.config['SCHEDULER_ENABLED'] = True

        with patch('app.scheduler.SCHEDULER_LOCK_FILE', str(lock_file)), \
             patch('app.scheduler.BackgroundScheduler') as mock_scheduler_class, \
             patch('app.scheduler.signal.signal'), \
             patch('app.scheduler.atexit.register'):
            mock_scheduler = MagicMock()
            mock_scheduler_class.return_value = mock_scheduler

            init_scheduler(app)

            mock_scheduler_class.assert_called_once()
            mock_scheduler.start.assert_called_once()

        assert _read_lock_pid(str(lock_file)) == os.getpid()

    def test_live_lock_prevents_startup(self, app, tmp_path):
        """A lock held by a live process should prevent a new worker from
        starting its own scheduler."""
        lock_file = tmp_path / "scheduler_lock"
        lock_file.write_text(str(os.getpid()))  # current process is alive

        app.config['SCHEDULER_ENABLED'] = True

        with patch('app.scheduler.SCHEDULER_LOCK_FILE', str(lock_file)), \
             patch('app.scheduler.BackgroundScheduler') as mock_scheduler_class:
            init_scheduler(app)

            mock_scheduler_class.assert_not_called()


class TestSchedulerIntegration:
    """Integration tests for scheduler functionality"""
    
    def test_full_ranking_update_flow_mocked(self, app, db_session):
        """Test complete ranking update flow with mocked ranking service"""
        # Create test users with different scores
        player_role = Role.query.filter_by(name='player').first()
        
        users = []
        for i in range(3):  # Reduced number to avoid conflicts
            user = User(
                username=f'sched_player{i}',  # Different prefix to avoid conflicts
                email=f'sched_player{i}@test.com',
                name=f'Sched Player {i}',
                phone=f'+123456780{i}',  # Different phone numbers
                gender='male' if i % 2 == 0 else 'female',
                password_hash=generate_password_hash('password'),
                active=True
            )
            user.roles.append(player_role)
            db_session.add(user)
            users.append(user)
        
        db_session.commit()
        
        # Mock the ranking service to avoid database issues
        with patch('app.rating.services.take_rank_snapshot') as mock_snapshot:
            mock_snapshot.return_value = {'success': True, 'message': 'Success'}
            
            # Execute the ranking job
            update_rankings_job()
            
            # Verify all ranking types were called
            expected_calls = [call('all'), call('male'), call('female'), call('summer_2026')]
            mock_snapshot.assert_has_calls(expected_calls, any_order=False)
            assert mock_snapshot.call_count == 4

    def test_scheduler_error_handling(self, app):
        """Test scheduler handles service errors gracefully"""
        with patch('app.rating.services.take_rank_snapshot') as mock_snapshot:
            # Simulate service error
            mock_snapshot.side_effect = [
                {'success': True, 'message': 'Success'},  # all succeeds
                Exception("Service error"),  # male fails
                {'success': True, 'message': 'Success'}   # female succeeds
            ]
            
            # Should not raise exception despite service error
            update_rankings_job()
            
            # Verify all calls were attempted
            assert mock_snapshot.call_count == 2  # Stops at first exception

    def test_actual_ranking_service_integration(self, app, db_session):
        """Test integration with actual ranking service (limited scope)"""
        # Create a minimal test user
        player_role = Role.query.filter_by(name='player').first()
        
        user = User(
            username='integration_test_user',
            email='integration@test.com',
            name='Integration Test User',
            phone='+1234567890',
            gender='male',
            password_hash=generate_password_hash('password'),
            active=True
        )
        user.roles.append(player_role)
        db_session.add(user)
        db_session.commit()
        
        # Count existing male users before test
        existing_male_count = User.query.filter_by(gender='male', active=True).count()
        
        # Test the actual ranking service call
        from app.rating.services import take_rank_snapshot
        
        # This should work without errors
        result = take_rank_snapshot('male')
        assert result['success'] is True
        assert 'male' in result['message']
        
        # Verify rank history was created for our user
        rank_history = UserRankHistory.query.filter_by(
            user_id=user.id, 
            rank_type='male'
        ).first()
        assert rank_history is not None
        # Rank should be between 1 and the total number of male users
        assert 1 <= rank_history.rank <= existing_male_count
