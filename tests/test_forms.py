"""
Tests for form validation, including avatar file size validation
"""
import pytest
from io import BytesIO
from flask import current_app
from app.user.forms import EditProfileForm, FileSizeValidator


class TestFileSizeValidator:
    """Test the custom FileSizeValidator"""
    
    def test_small_file_passes(self, app):
        """Test that small files pass validation"""
        with app.app_context():
            # Create small file
            small_file = BytesIO(b"small content")
            small_file.filename = "test.jpg"
            
            validator = FileSizeValidator()
            
            # Mock form and field
            class MockField:
                def __init__(self, data):
                    self.data = data
            
            class MockForm:
                pass
            
            # Should not raise exception
            validator(MockForm(), MockField(small_file))
    
    def test_large_file_fails(self, app):
        """Test that large files fail validation"""
        with app.app_context():
            # Get max size from config (TestingConfig has 1MB limit)
            max_size = current_app.config.get('AVATARS_MAX_CONTENT_LENGTH', 1024 * 1024)
            
            # Create file that's 1 byte over limit
            large_content = b"x" * (max_size + 1)
            large_file = BytesIO(large_content)
            large_file.filename = "large.jpg"
            
            validator = FileSizeValidator()
            
            # Mock form and field
            class MockField:
                def __init__(self, data):
                    self.data = data
            
            class MockForm:
                pass
            
            # Should raise ValidationError
            from wtforms.validators import ValidationError
            with pytest.raises(ValidationError) as exc_info:
                validator(MockForm(), MockField(large_file))
            
            assert "Размер файла не должен превышать" in str(exc_info.value)
    
    def test_no_file_passes(self, app):
        """Test that no file (None) passes validation"""
        with app.app_context():
            validator = FileSizeValidator()
            
            # Mock form and field with no data
            class MockField:
                def __init__(self, data):
                    self.data = data
            
            class MockForm:
                pass
            
            # Should not raise exception
            validator(MockForm(), MockField(None))
    
    def test_format_size_helper(self, app):
        """Test the size formatting helper method"""
        with app.app_context():
            validator = FileSizeValidator()
            
            # Test bytes
            assert "100 байт" in validator._format_size(100)
            
            # Test KB
            assert "1.0 КБ" in validator._format_size(1024)
            
            # Test MB
            assert "1.0 МБ" in validator._format_size(1024 * 1024)


class TestAvatarConfig:
    """Test avatar-related configuration"""
    
    def test_avatar_config_exists(self, app):
        """Test that avatar configuration is properly set"""
        with app.app_context():
            # Check that avatar config exists
            assert current_app.config.get('AVATARS_MAX_CONTENT_LENGTH') is not None
            assert current_app.config.get('AVATARS_ALLOWED_EXTENSIONS') is not None
            assert current_app.config.get('AVATARS_FOLDER') is not None
            assert current_app.config.get('AVATARS_SIZES') is not None
    
    def test_avatar_max_size_reasonable(self, app):
        """Test that avatar max size is reasonable"""
        with app.app_context():
            max_size = current_app.config.get('AVATARS_MAX_CONTENT_LENGTH')
            
            # Should be at least 100KB and at most 50MB
            assert max_size >= 100 * 1024  # 100KB
            assert max_size <= 50 * 1024 * 1024  # 50MB
    
    def test_testing_config_has_smaller_limit(self, app):
        """Test that TestingConfig has a smaller avatar size limit"""
        with app.app_context():
            max_size = current_app.config.get('AVATARS_MAX_CONTENT_LENGTH')
            
            # TestingConfig should have 1MB limit
            assert max_size == 1 * 1024 * 1024  # 1MB for testing
