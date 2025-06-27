import logging
from flask import render_template, redirect, url_for, flash
from flask_login import login_required
from . import bp
from .forms import ScoreTemplateForm
from app.services import role_required
import sqlalchemy as sa
from app import db
from app.models import ScoreTemplate


logger = logging.getLogger(__name__)


@bp.route('/score-templates')
@login_required
@role_required(['superadmin'])
def score_templates():
    """List all score templates"""

    templates = db.session.scalars(
        sa.select(ScoreTemplate)
        .order_by(sa.desc(ScoreTemplate.score))
    ).all()

    return render_template('rating/score_templates.html', title='Шаблоны очков', templates=templates)


@bp.route('/score-templates/add', methods=['GET', 'POST'])
@login_required
@role_required(['superadmin'])
def add_score_template():
    """Create new score template"""

    form = ScoreTemplateForm()

    if form.validate_on_submit():
        # check for existing template
        existing_template = db.session.scalar(sa.select(ScoreTemplate).where(ScoreTemplate.name == form.name.data))
        if existing_template:
            flash('Шаблон с таким именем уже существует', 'error')
            return render_template('rating/score_template_add_edit.html', title='Добавление шаблона', form=form)

        template = ScoreTemplate.from_dict(form.data)
        db.session.add(template)
        db.session.commit()

        logger.info(f'Added score template: {template.name}')
        flash(f'Шаблон "{template.name}" добавлен')

        return redirect(url_for('rating.score_templates'))

    return render_template('rating/score_template_add_edit.html', title='Добавление шаблона', form=form)


@bp.route('/score-templates/<int:template_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(['superadmin'])
def edit_score_template(template_id):
    """Edit score template"""

    template = db.get_or_404(ScoreTemplate, template_id)
    form = ScoreTemplateForm(obj=template)

    if form.validate_on_submit():
        # check for existing template
        existing_template = db.session.scalar(sa.select(ScoreTemplate)
                                              .where(ScoreTemplate.name == form.name.data,
                                                     ScoreTemplate.id != template.id))
        if existing_template:
            flash('Шаблон с таким именем уже существует', 'error')
            return render_template('rating/score_template_add_edit.html',
                                   title='Редактирование шаблона',
                                   form=form, template=template, action='edit')

        template.update_from_dict(form.data)
        db.session.commit()

        logger.info(f'Updated score template: {template.name}')
        flash(f'Шаблон "{template.name}" обновлён')

        return redirect(url_for('rating.score_templates'))

    return render_template('rating/score_template_add_edit.html',
                           title='Редактирование шаблона',
                           form=form, template=template, action='edit')


@bp.route('/score-templates/<int:template_id>/delete', methods=['GET'])
@login_required
def delete_score_template(template_id):
    """Delete score template"""

    template = db.get_or_404(ScoreTemplate, template_id)
    db.session.delete(template)
    db.session.commit()

    logger.info(f'Deleted score template: {template.name}')
    flash(f'Шаблон "{template.name}" удалён')

    return redirect(url_for('rating.score_templates'))
