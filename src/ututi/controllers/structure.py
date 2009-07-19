import logging

from formencode import Schema, validators, Invalid
from sqlalchemy.orm.exc import NoResultFound

from pylons.controllers.util import abort
from pylons import request, c
from pylons.controllers.util import redirect_to
from pylons.decorators import validate
from pylons.i18n import _

from ututi.lib.image import serve_image
from ututi.lib.base import BaseController, render
from ututi.model import meta, LocationTag

log = logging.getLogger(__name__)


class StructureIdValidator(validators.FancyValidator):

    messages = {
        'not_exist': _(u"The element does not exist.")
        }

    def _to_python(self, value, state):
        return int(value.strip())

    def validate_python(self, value, state):
        if value != 0:
            try:
                meta.Session.query(LocationTag).filter_by(id=value).one()
            except:
                raise Invalid(self.message('not_exist', state), value, state)


class NewStructureForm(Schema):

    allow_extra_fields = False

    title = validators.UnicodeString(not_empty=True, strip=True)
    title_short = validators.UnicodeString(not_empty=True, strip=True, max=50)

    description = validators.UnicodeString(strip=True)
    parent = StructureIdValidator()


class StructureController(BaseController):

    def index(self):
        c.structure = meta.Session.query(LocationTag).filter_by(parent=None).all()
        return render('structure.mako')

    @validate(schema=NewStructureForm, form='index')
    def create(self):
        values = self.form_result
        structure = LocationTag(title=values['title'],
                                title_short=values['title_short'],
                                description=values['description'])
        meta.Session.add(structure)

        # XXX why zero?
        if int(values['parent']) != 0:
            parent = meta.Session.query(LocationTag).filter_by(id=values['parent']).one()
            parent.children.append(structure)
        meta.Session.commit()
        redirect_to(controller='structure', action='index')

    def edit(self, id):
        try:
            c.item = meta.Session.query(LocationTag).filter_by(id=id).one()
        except NoResultFound:
            abort(404)

        c.structure = meta.Session.query(LocationTag).filter_by(parent=None).filter(LocationTag.id != id).all()
        return render('structure/edit.mako')

    @validate(schema=NewStructureForm, form='edit')
    def update(self, id):
        try:
            c.item = meta.Session.query(LocationTag).filter_by(id=id).one()
        except NoResultFound:
            abort(404)

        values = self.form_result
        c.item.title = values['title']
        c.item.title_short = values['title_short']
        c.item.description = values['description']

        if values.get('parent') is not None and int(values.get('parent', '0')) != 0:
            parent = meta.Session.query(LocationTag).filter_by(id=values['parent']).one()
            parent.children.append(c.item)
        meta.Session.commit()
        redirect_to(controller='structure', action='index')

    def logo(self, id, width=None, height=None):
        tag = meta.Session.query(LocationTag).filter_by(id=id).one()
        return serve_image(tag.logo, width, height)
