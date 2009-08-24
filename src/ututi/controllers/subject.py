import logging

from webhelpers.html.tags import link_to
from formencode.variabledecode import NestedVariables
from formencode.foreach import ForEach
from formencode.compound import Pipe
from formencode import Schema, validators, Invalid, All
from routes import url_for

from pylons import c, request, url
from pylons.templating import render_mako_def
from pylons.decorators import validate
from pylons.controllers.util import redirect_to, abort
from pylons.i18n import _

from ututi.model import meta, LocationTag, Subject, File, SimpleTag
from ututi.lib.security import ActionProtector
from ututi.lib.fileview import FileViewMixin
from ututi.lib.base import BaseController, render
from ututi.lib.validators import LocationTagsValidator

log = logging.getLogger(__name__)

def subject_action(method):
    def _subject_action(self, id, tags):
        location = LocationTag.get(tags)
        subject = Subject.get(location, id)

        if subject is None:
            abort(404)
        c.object_location = subject.location
        c.subject = subject
        return method(self, subject)
    return _subject_action

class SubjectIdValidator(validators.FormValidator):

    messages = {
        'duplicate': _(u"Such id already exists, choose a different one."),
    }

    def validate_python(self, form_dict, state):
        old_subject = Subject.get(LocationTag.get(form_dict.get('old_location', '')),
                                  form_dict.get('id', 0))
        # XXX test for id matching a tag
        location = form_dict['location']
        subject = Subject.get(location, form_dict['id'])
        if subject is not None and not subject is old_subject:
            raise Invalid(self.message('duplicate', state),
                          form_dict, state)


class SubjectForm(Schema):
    """A schema for validating new subject forms."""

    allow_extra_fields = True

    pre_validators = [NestedVariables()]

    location = Pipe(ForEach(validators.String(strip=True)),
                    LocationTagsValidator())

    title = validators.UnicodeString(not_empty=True, strip=True)
    lecturer = validators.UnicodeString(strip=True)
    chained_validators = [SubjectIdValidator()]


class NewSubjectForm(SubjectForm):
    msg = {'invalid': _('The text contains invalid characters, only letters, numbers and the symbols - + _ are allowed.')}
    id = All(validators.Regex(r'^[_\+\-a-zA-Z0-9]*$',
                              messages=msg),
             validators.String(max=50, strip=True, not_empty=True))


class SubjectController(BaseController, FileViewMixin):
    """A controller for subjects."""

    def __before__(self):
        c.breadcrumbs = [
            {'title': _('Subjects'),
             'link': url_for(controller='subject', action='index')}
            ]

    @ActionProtector("root")
    def index(self):
        c.subjects = meta.Session.query(Subject).all()
        return render('subjects.mako')

    @subject_action
    def home(self, subject):
        c.breadcrumbs = [{'link': subject.url(),
                              'title': subject.title}]
        return render('subject/home.mako')

    @ActionProtector("user")
    def add(self):
        return render('subject/add.mako')

    @validate(schema=NewSubjectForm, form='add')
    @ActionProtector("user")
    def create(self):
        title = self.form_result['title']
        id = self.form_result['id'].lower()
        lecturer = self.form_result['lecturer']
        location = self.form_result['location']

        if lecturer == '':
            lecturer = None

        subj = Subject(id, title, location, lecturer)

        #check to see what kind of tags we have got
        tags = [tag.strip().lower() for tag in self.form_result.get('tagsitem', [])]
        if tags == []:
            tags = [tag.strip().lower() for tag in self.form_result.get('tags', '').split(',')]

        subj.tags = []
        for tag in tags:
            subj.tags.append(SimpleTag.get(tag))

        meta.Session.add(subj)
        meta.Session.commit()

        redirect_to(controller='subject',
                    action='home',
                    id=subj.subject_id,
                    tags=subj.location_path)

    @ActionProtector("user")
    @subject_action
    def edit(self, subject):
        c.breadcrumbs = [{'link': c.subject.url(),
                              'title': c.subject.title}]
        c.subject.tags_list = ', '.join([tag.title for tag in c.subject.tags])
        return render('subject/edit.mako')

    @validate(schema=SubjectForm, form='edit')
    @ActionProtector("user")
    @subject_action
    def update(self, subject):

        subject.title = self.form_result['title']
        subject.lecturer = self.form_result['lecturer']
        subject.location = self.form_result['location']

        #check to see what kind of tags we have got
        tags = [tag.strip().lower() for tag in self.form_result.get('tagsitem', [])]
        if tags == []:
            tags = [tag.strip().lower() for tag in self.form_result.get('tags', '').split(',')]

        subject.tags = []
        for tag in tags:
            subject.tags.append(SimpleTag.get(tag))

        meta.Session.commit()

        redirect_to(controller='subject',
                    action='home',
                    id=subject.subject_id,
                    tags=subject.location_path)

    @ActionProtector("user")
    @subject_action
    def upload_file(self, subject):
        return self._upload_file(subject)

    @ActionProtector("user")
    @subject_action
    def create_folder(self, subject):
        return self._create_folder(subject)

    @ActionProtector("moderator", "root")
    @subject_action
    def delete_folder(self, subject):
        return self._delete_folder(subject)
