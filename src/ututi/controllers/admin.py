import csv
import string
import os
import logging
import base64

from sqlalchemy.sql.expression import desc
from sqlalchemy.sql.expression import not_
from sqlalchemy import func
from magic import from_buffer
from datetime import date
from webhelpers import paginate

from pylons import request, c
from pylons.controllers.util import redirect_to, abort

from random import Random
from ututi.lib.security import ActionProtector
from ututi.lib.base import BaseController, render
from ututi.model.events import Event
from ututi.model import SimpleTag
from ututi.model import UserSubjectMonitoring
from ututi.model import Page
from ututi.model import (meta, User, Email, LocationTag, Group, Subject,
                         GroupMember, GroupMembershipType, File)
from ututi.lib import helpers as h

log = logging.getLogger(__name__)

email_map = {'inf@mytutor.lt'             : 'info@mytutor.lt',
             'indremilukaite@gmai.com'    : 'indremilukaite@gmail.com',
             'svaras456@gmai.com'         : 'svaras456@gmail.com',
             'veju.mote@gmsil.com'        : 'dainius1989@gmail.com',
             'dainius1989@gnail.com'      : 'veju.mote@gmail.com',
             'jurgis.pragauskis@gmail.com': 'jurgis.pralgauskis@gmail.com',
             'jarekass+petras@takas.lt'   : '',
             'asta.samulionyte@khf.vu.lt' : '',
             'jana89@one.lt'              : '',
             'info@ututi.lt'              : '',
             'ted.bing@gmail.com'         : ''}


def store_file(file_obj, file_name):
    path = os.environ.get("upload_import_path", None)
    if path is not None:
        file_obj.store(open(os.path.join(path, file_name)))
    else:
        file_obj.store('Whatever!')


class AdminController(BaseController):
    """Controler for system administration."""

    def _stripAndDecode(self, rows):
        return [[column.strip().decode('utf-8') for column in row]
                for row in rows]

    def _getReader(self):
        file = request.POST.get('file_upload', None)
        if file is not None and file != '':
            return self._stripAndDecode(csv.reader(file.value.splitlines()))
        return []

    def _getLines(self):
        """CSV parser especially for logo import.

        We need to split the logo lines ourselves - csv reader is
        written in C and can't handle very very long lines.

        Only ids and logos are in the file, so we can assume no quoted
        cells in the csv file.
        """
        file = request.POST.get('file_upload', None)

        if file is not None and file != '':
            return self._stripAndDecode(
                [line.split(',')
                 for line in file.value.splitlines()])
        return []

    @ActionProtector("root")
    def index(self):
        return render('/admin/dashboard.mako')

    @ActionProtector("root")
    def import_csv(self):
        return render('/admin/import.mako')

    @ActionProtector("root")
    def users(self):
        users = meta.Session.query(User).order_by(desc(User.id))
        c.users = paginate.Page(
            users,
            page=int(request.params.get('page', 1)),
            item_count=users.count() or 0,
            items_per_page=100)
        return render('/admin/users.mako')

    @ActionProtector("root")
    def import_users(self):
        for line in self._getReader():
            fullname = line[2]
            password = line[1][6:]
            email = line[3].lower()
            email = email_map.get(email, email)
            if not email:
                continue
            user = User.get(email)
            if user is None:
                user = User(fullname, password, False)
                email = Email(email)
                user.emails = [email]
                email.confirmed = True
                meta.Session.add(user)

            meta.Session.commit()
        redirect_to(controller='admin', action='users')

    @ActionProtector("root")
    def import_structure(self):
        for line in self._getReader():
            title = line[1]
            title_short = line[0]
            description = line[2]
            parent = line[3]

            tag = LocationTag.get([parent, title_short])
            if tag is None:
                tag = LocationTag(title=title,
                                  title_short=title_short,
                                  description=description)
            tag.title = title
            tag.title_short = title_short
            tag.description = description

            meta.Session.add(tag)
            if parent:
                parent = LocationTag.get([parent])
                parent.children.append(tag)
            meta.Session.commit()
        redirect_to(controller='structure', action='index')

    @ActionProtector("root")
    def import_groups(self):
        for row in self._getReader():
            uni_id = row[5]
            fac_id = row[4]
            location = LocationTag.get([uni_id, fac_id])

            id, title, desc, year = row[:4]
            group = Group.get(id)
            if group is None:
                group = Group(group_id=id)
                meta.Session.add(group)

            group.title = title
            group.description = desc
            group.location = LocationTag.get([uni_id, fac_id])

            if year != '' and year != 'None':
                group.year = date(int(year), 1, 1)
            else:
                group.year = date(2008, 1, 1)

        meta.Session.commit()
        redirect_to(controller='admin', action='groups')

    @ActionProtector("root")
    def import_subjects_without_ids(self):
        for row in self._getReader():
            title, lecturer = row[:2]
            location_path = reversed(row[2:4])
            tags = filter(bool, [tag.strip() for tag in row[5].split(',')])
            description = row[-2]
            id = ''.join(Random().sample(string.ascii_lowercase, 8)) # use random id first
            location = LocationTag.get(location_path)

            #do not import duplicates
            existing = meta.Session.query(Subject).filter(Subject.location_id == location.id).filter(func.upper(Subject.title) == func.upper(title)).first()
            if existing:
                log.info('Subject exists: %s' % row)
                h.flash('Subject exists: %s' % row)
                continue

            title = title
            lecturer = lecturer
            subj = Subject('', title, location)
            subj.lecturer = lecturer
            subj.description = description
            meta.Session.add(subj)
            meta.Session.flush()
            subj.subject_id = subj.generate_new_id()
            for tag in tags:
                subj.tags.append(SimpleTag.get(tag))
        meta.Session.commit()
        redirect_to(controller='admin', action='subjects')

    @ActionProtector('root')
    def files(self):

        files = meta.Session.query(File)\
            .order_by(desc(File.created_on))\
            .filter(File.title != u'text.html')\
            .filter(File.title != u'Null File')

        c.files = paginate.Page(
            files,
            page=int(request.params.get('page', 1)),
            item_count=files.count() or 0,
            items_per_page=100)

        return render('admin/files.mako')

    @ActionProtector("root")
    def groups(self):
        c.groups = meta.Session.query(Group).order_by(Group.created_on).all()
        return render('admin/groups.mako')

    @ActionProtector("root")
    def subjects(self):
        subjects = meta.Session.query(Subject)\
            .order_by(desc(Subject.created_on))
        c.subjects = paginate.Page(
            subjects,
            page=int(request.params.get('page', 1)),
            item_count=subjects.count() or 0,
            items_per_page=100)
        return render('admin/subjects.mako')

    @ActionProtector("root")
    def events(self):
        c.events = meta.Session.query(Event)\
            .order_by(desc(Event.created))\
            .limit(500).all()
        return render('admin/events.mako')
