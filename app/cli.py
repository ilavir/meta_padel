import click
from flask import Blueprint
from flask.cli import with_appcontext
from app.models import User
from app.avatar_utils import AvatarManager


bp = Blueprint('cli', __name__, cli_group=None)


@bp.cli.group()
def avatar():
    """Avatar management commands."""
    pass


@avatar.command()
@with_appcontext
def cleanup():
    """Remove orphaned avatar files."""
    # Get all active avatar filenames from database
    active_filenames = [user.avatar_filename for user in User.query.all()]

    removed_count = AvatarManager.cleanup_orphaned_avatars(active_filenames)
    click.echo(f"Removed {removed_count} orphaned avatar files.")


@avatar.command()
@with_appcontext
def regenerate():
    """Regenerate all avatar sizes for all users."""
    users = User.query.filter(User.avatar_filename != 'default.jpg').all()

    success_count = 0
    error_count = 0

    for user in users:
        if AvatarManager.regenerate_sizes(user.avatar_filename):
            success_count += 1
            click.echo(f"✓ Regenerated sizes for {user.username}")
        else:
            error_count += 1
            click.echo(f"✗ Failed to regenerate sizes for {user.username}")

    click.echo(f"\nCompleted: {success_count} successful, {error_count} errors")


@avatar.command()
@click.argument('username')
@with_appcontext
def regenerate_user(username):
    """Regenerate avatar sizes for a specific user."""
    user = User.query.filter_by(username=username).first()
    if not user:
        click.echo(f"User '{username}' not found.")
        return

    if user.avatar_filename == 'default.jpg':
        click.echo(f"User '{username}' does not have an avatar.")
        return

    if AvatarManager.regenerate_sizes(user.avatar_filename):
        click.echo(f"✓ Regenerated avatar sizes for {username}")
    else:
        click.echo(f"✗ Failed to regenerate avatar sizes for {username}")
