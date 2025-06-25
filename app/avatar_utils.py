from flask import current_app, url_for
import os
from PIL import Image, ImageDraw


class AvatarManager:
    """Utility class for avatar management"""

    SIZES = {
        'thumbnail': (30, 30),
        'small': (50, 50),
        'medium': (100, 80),
        'large': (300, 300)
    }

    @staticmethod
    def get_avatar_path(filename, size='medium'):
        """Get the file system path for an avatar"""
        if filename == 'default.jpg':
            # Handle default avatar
            size_suffix = f"_{size}" if size != 'medium' else '_medium'
            filename = f"default{size_suffix}.jpg"
        else:
            # Handle user avatar
            name, ext = os.path.splitext(filename)
            size_suffix = f"_{size}" if size != 'medium' else '_medium'
            filename = f"{name}{size_suffix}{ext}"

        avatars_path = os.path.relpath(current_app.config['AVATARS_FOLDER'], current_app.static_folder)
        return url_for('static', filename=f'{avatars_path}/{filename}')

    @staticmethod
    def avatar_exists(filename, size='medium'):
        """Check if an avatar file exists"""
        return os.path.exists(AvatarManager.get_avatar_path(filename, size))

    @staticmethod
    def cleanup_orphaned_avatars(active_filenames):
        """Remove avatar files that are no longer referenced by any user"""
        pics_dir = current_app.config['AVATARS_FOLDER']
        if not os.path.exists(pics_dir):
            return

        # Get all files in the directory
        all_files = os.listdir(pics_dir)

        # Keep track of files that should be kept
        keep_files = set()

        # Add default avatar files
        for size in AvatarManager.SIZES.keys():
            suffix = f"_{size}" if size != 'medium' else '_medium'
            keep_files.add(f"default{suffix}.jpg")

        # Add active user avatar files
        for filename in active_filenames:
            if filename and filename != 'default.jpg':
                name, ext = os.path.splitext(filename)
                for size in AvatarManager.SIZES.keys():
                    suffix = f"_{size}" if size != 'medium' else '_medium'
                    keep_files.add(f"{name}{suffix}{ext}")

        # Remove orphaned files
        removed_count = 0
        for file in all_files:
            if file not in keep_files and not file.startswith('.'):
                try:
                    os.remove(os.path.join(pics_dir, file))
                    removed_count += 1
                except OSError:
                    pass  # File might be in use

        return removed_count

    @staticmethod
    def regenerate_sizes(filename):
        """Regenerate all sizes for an existing avatar"""
        if filename == 'default.jpg':
            return False  # Don't regenerate default

        pics_dir = current_app.config['AVATARS_FOLDER']

        # Try to find the largest existing version
        name, ext = os.path.splitext(filename)
        source_path = None

        # Check for large version first, then medium, then original
        for size in ['large', 'medium', '']:
            suffix = f"_{size}" if size else ''
            potential_path = os.path.join(pics_dir, f"{name}{suffix}{ext}")
            if os.path.exists(potential_path):
                source_path = potential_path
                break

        if not source_path:
            return False

        try:
            # Open the source image
            img = Image.open(source_path)

            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background

            # Regenerate all sizes
            from app.models import User  # Adjust import

            for size_name, dimensions in AvatarManager.SIZES.items():
                img_copy = img.copy()

                if size_name == 'medium':  # 100x80 - crop to fit
                    img_copy = User._crop_to_fit(img_copy, dimensions)
                else:  # Square images
                    img_copy.thumbnail(dimensions, Image.Resampling.LANCZOS)
                    if img_copy.size != dimensions:
                        img_copy = User._crop_center(img_copy, dimensions)

                # Save the sized image
                suffix = f"_{size_name}" if size_name != 'medium' else '_medium'
                sized_filename = f"{name}{suffix}{ext}"
                sized_path = os.path.join(pics_dir, sized_filename)

                img_copy.save(sized_path, quality=95, optimize=True)

            return True

        except Exception as e:
            print(f"Error regenerating avatar sizes: {e}")
            return False

    @staticmethod
    def init_default():
        """Create necessary directories for file uploads with tennis-themed default avatars"""
        profile_pics_dir = current_app.config['AVATARS_FOLDER']
        os.makedirs(profile_pics_dir, exist_ok=True)

        # Create default avatar files in all sizes if they don't exist
        default_paths = {
            'default_thumbnail.jpg': (30, 30),
            'default_small.jpg': (50, 50),
            'default_medium.jpg': (100, 80),
            'default_large.jpg': (300, 300)
        }

        for filename, size in default_paths.items():
            default_path = os.path.join(profile_pics_dir, filename)
            if not os.path.exists(default_path):
                # Create a simple monochrome avatar with a tennis motif
                img = Image.new('RGB', size, color='white')
                draw = ImageDraw.Draw(img)
                w, h = size

                # Draw a gray tennis ball
                ball_radius = min(w, h) // 3
                center = (w // 2, h // 2)
                bbox = [
                    (center[0] - ball_radius, center[1] - ball_radius),
                    (center[0] + ball_radius, center[1] + ball_radius)
                ]
                gray_ball = (160, 160, 160)
                draw.ellipse(bbox, fill=gray_ball, outline=(100, 100, 100))

                # Add curved seams in lighter gray
                if w >= 50:  # Skip seams on very small avatars
                    seam_offset = ball_radius // 2
                    light_gray = (220, 220, 220)
                    draw.arc([bbox[0][0] + seam_offset, bbox[0][1],
                             bbox[1][0] - seam_offset, bbox[1][1]],
                             start=0, end=180, fill=light_gray, width=2)
                    draw.arc([bbox[0][0], bbox[0][1] + seam_offset,
                             bbox[1][0], bbox[1][1] - seam_offset],
                             start=90, end=270, fill=light_gray, width=2)

                img.save(default_path, quality=95)
                print(f"Created tennis-themed default avatar: {filename}")

        print(f"Upload directories created at {profile_pics_dir}")


# Template filter for easy use in Jinja2
def avatar_url(user, size='medium'):
    """Template filter to get avatar URL"""
    return user.get_avatar_url(size)


# Register the filter (add this to your app factory)
def register_avatar_filter(app):
    app.jinja_env.filters['avatar_url'] = avatar_url
