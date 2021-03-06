import logging
import string
from random import Random
from pylons import url
from sqlalchemy.sql.expression import func
from sqlalchemy.sql.expression import and_, or_, not_
from sqlalchemy.sql import select
from sqlalchemy.orm.exc import NoResultFound
from random import randrange
from binascii import a2b_base64, b2a_base64
import binascii
import hashlib
from urlparse import urlparse
from datetime import datetime, timedelta
from time import mktime

from ututi.model.util import logo_property, read_facebook_logo
from ututi.model import meta
from ututi.lib.helpers import image, user_done_items, teacher_done_items
from ututi.lib.emails import send_email_confirmation_code

from zope.cachedescriptors.property import CachedProperty

from pylons.i18n import _
from pylons import config
from pylons.templating import render_mako_def

log = logging.getLogger(__name__)


class UserSubjectMonitoring(object):
    """Relationship between user and subject."""
    def __init__(self, user, subject, ignored=False):
        self.user, self.subject, self.ignored = user, subject, ignored


def generate_salt():
    """Generate the salt used in passwords."""
    salt = ''
    for n in range(7):
        salt += chr(randrange(256))
    return salt


def generate_password(password):
    """Generate a hash for a given password."""
    salt = generate_salt()
    password = password.encode('utf-8')
    return b2a_base64(hashlib.sha1(password + salt).digest() + salt)[:-1]


def validate_password(reference, password):
    """Verify a password given the original hash."""
    if not reference:
        return False
    try:
        ref = a2b_base64(reference)
    except binascii.Error:
        return False
    salt = ref[20:]
    compare = b2a_base64(hashlib.sha1(password + salt).digest() + salt)[:-1]
    return compare == reference


class AdminUser(object):

    @classmethod
    def authenticate(cls, username, password):
        user = cls.get(username)
        if user is None:
            return None
        if validate_password(user.password, password):
            return user
        else:
            return None

    @classmethod
    def get(cls, username):
        """Get a user by his email or id."""
        try:
            if isinstance(username, (long, int)):
                return meta.Session.query(cls).filter_by(id=username).one()
            else:
                return meta.Session.query(cls).filter_by(email=username.strip().lower()).one()
        except NoResultFound:
            return None

    def has_logo(self):
        return False


class Author(object):
    """The Author object - for references to authorship. Persists even when the user is deleted."""

    is_teacher = False

    @classmethod
    def get_byid(cls, id):
        try:
            return meta.Session.query(cls).filter_by(id=id).one()
        except NoResultFound:
            return None

    def url(self, controller='user', action='index', **kwargs):
        return url(controller=controller,
                   action=action,
                   id=self.id,
                   **kwargs)

    @property
    def logo(self):
        return None

    def has_logo(self):
        return False


class User(Author):
    """The User object - Ututi users."""
    is_teacher = False

    def delete_user(self):
        """Low level delete so author record would not get deleted."""
        conn = meta.engine.connect()
        users_table = meta.metadata.tables['users']
        upd = users_table.delete().where(users_table.c.id==self.id)
        conn.execute(upd)
        meta.Session.expire(self)

    def change_type(self, type, **kwargs):
        conn = meta.engine.connect()
        authors_table = meta.metadata.tables['authors']
        upd = authors_table.update().where(authors_table.c.id==self.id).values(type=type, **kwargs)
        conn.execute(upd)

    @property
    def created(self):
        """Return user creation time in Unix time format"""
        return mktime(self.accepted_terms.timetuple())

    @property
    def email(self):
        return filter(lambda email: email.main, self.emails)[0]

    @property
    def hidden_blocks_list(self):
        return self.hidden_blocks.strip().split(' ')

    def send(self, msg):
        """Send a message to the user."""
        from ututi.lib.messaging import EmailMessage, SMSMessage
        if isinstance(msg, EmailMessage):
            email = self.email
            if email.confirmed or msg.force:
                msg.send(email.email)
            else:
                log.info("Could not send message to unconfirmed email %(email)s" % dict(email=email.email))
        elif isinstance(msg, SMSMessage):
            if self.phone_number is not None and (self.phone_confirmed or msg.force):
                msg.recipient=self
                msg.send(self.phone_number)
            else:
                log.info("Could not send message to uncofirmed phone number %(num)s" % dict(num=self.phone_number))

    def checkPassword(self, password):
        """Check the user's password."""
        return validate_password(self.password, password)

    def files(self):
        from ututi.model import ContentItem
        return meta.Session.query(ContentItem).filter_by(
                content_type='file', created=self, deleted_by=None).all()

    def files_count(self):
        from ututi.model import ContentItem
        return meta.Session.query(ContentItem).filter_by(
                content_type='file', created=self, deleted_by=None).count()

    def group_requests(self):
        from ututi.model import PendingRequest, Group, GroupMember
        return meta.Session.query(PendingRequest
                ).join(Group).join(GroupMember
                ).filter(GroupMember.user == self
                ).filter(GroupMember.membership_type == 'administrator'
                ).all()

    @classmethod
    def authenticate(cls, location, username, password):
        user = cls.get(username, location)
        if user is None:
            return None
        if validate_password(user.password, password.encode('utf-8')):
            return user
        else:
            return None

    @classmethod
    def authenticate_global(cls, username, password):
        user = cls.get_global(username)
        if user is None:
            return None
        if validate_password(user.password, password):
            return user
        else:
            return None

    @classmethod
    def get(cls, username, location):
        if isinstance(location, (long, int)):
            from ututi.model import LocationTag
            location = LocationTag.get(location)

        if location is None:
            return None

        loc_ids = [loc.id for loc in location.flatten]
        q = meta.Session.query(cls).filter(cls.location_id.in_(loc_ids))

        if isinstance(username, (long, int)):
            q = q.filter_by(id=username)
        else:
            q = q.filter_by(username=username.strip().lower())

        try:
            return q.one()
        except NoResultFound:
            return None

    @classmethod
    def get_all(cls, username):
        """Get all users by username (email)."""
        return meta.Session.query(cls)\
                   .filter_by(username=username.strip().lower()).all()

    @classmethod
    def get_global(cls, username):
        """Get a user by his email or id."""
        try:
            if isinstance(username, (long, int)):
                return meta.Session.query(cls).filter_by(id=username).one()
            else:
                return meta.Session.query(cls).filter_by(username=username.strip().lower()).one()
        except NoResultFound:
            return None

    @classmethod
    def get_byid(cls, id):
        try:
            return meta.Session.query(cls).filter_by(id=id).one()
        except NoResultFound:
            return None

    @classmethod
    def get_byopenid(cls, openid, location=None):
        q = meta.Session.query(cls)
        try:
            q = q.filter_by(openid=openid)
            if location is not None:
                loc_ids = [loc.id for loc in location.root.flatten]
                q = q.filter(cls.location_id.in_(loc_ids))
            return q.one()
        except NoResultFound:
            return None

    @classmethod
    def get_byfbid(cls, facebook_id, location=None):
        q = meta.Session.query(cls)
        try:
            q = q.filter_by(facebook_id=facebook_id)
            if location is not None:
                loc_ids = [loc.id for loc in location.root.flatten]
                q = q.filter(cls.location_id.in_(loc_ids))
            return q.one()
        except NoResultFound:
            return None

    @classmethod
    def get_byphone(cls, phone_number):
        try:
            return meta.Session.query(cls).filter_by(
                    phone_number=phone_number, phone_confirmed=True).one()
        except NoResultFound:
            return None

    def confirm_phone_number(self):
        # If there is another user with the same number, mark his phone
        # as unconfirmed.  This way there is only one person with a specific
        # confirmed phone number at any time.
        other = User.get_byphone(self.phone_number)
        if other is not None:
            other.phone_confirmed = False
        self.phone_confirmed = True

    @property
    def ignored_subjects(self):
        from ututi.model import Subject
        subjects_table = meta.metadata.tables['subjects']
        umst = meta.metadata.tables['user_monitored_subjects']
        user_ignored_subjects = meta.Session.query(Subject)\
            .join((umst,
                   and_(umst.c.subject_id==subjects_table.c.id,
                        umst.c.subject_id==subjects_table.c.id)))\
            .filter(and_(umst.c.user_id == self.id,
                         umst.c.ignored == True))
        return user_ignored_subjects.all()

    @property
    def watched_subjects(self):
        from ututi.model import Subject
        subjects_table = meta.metadata.tables['subjects']
        umst = meta.metadata.tables['user_monitored_subjects']
        directly_watched_subjects = meta.Session.query(Subject)\
            .join((umst,
                   and_(umst.c.subject_id==subjects_table.c.id,
                        umst.c.subject_id==subjects_table.c.id)))\
            .filter(and_(umst.c.user_id == self.id,
                         umst.c.ignored == False))
        return directly_watched_subjects.all()

    @property
    def all_watched_subjects(self):
        from ututi.model import Subject
        subjects_table = meta.metadata.tables['subjects']
        umst = meta.metadata.tables['user_monitored_subjects']
        directly_watched_subjects = meta.Session.query(Subject)\
            .join((umst,
                   and_(umst.c.subject_id==subjects_table.c.id,
                        umst.c.subject_id==subjects_table.c.id)))\
            .filter(and_(umst.c.user_id == self.id,
                         umst.c.ignored == False))

        user_ignored_subjects = meta.Session.query(Subject)\
            .join((umst,
                   and_(umst.c.subject_id==subjects_table.c.id,
                        umst.c.subject_id==subjects_table.c.id)))\
            .filter(and_(umst.c.user_id == self.id,
                         umst.c.ignored == True))

        gwst = meta.metadata.tables['group_watched_subjects']
        gmt = meta.metadata.tables['group_members']
        gt = meta.metadata.tables['groups']
        group_watched_subjects = meta.Session.query(Subject)\
            .join((gwst,
                   and_(gwst.c.subject_id==subjects_table.c.id,
                        gwst.c.subject_id==subjects_table.c.id)))\
            .join((gmt, gmt.c.group_id == gwst.c.group_id))\
            .join((gt, gmt.c.group_id == gt.c.id))\
            .filter(gmt.c.user_id == self.id)
        return directly_watched_subjects.union(
            group_watched_subjects.except_(user_ignored_subjects))\
            .order_by(Subject.title.asc())\
            .all()

    def _setWatchedSubject(self, subject, ignored):
        usm = meta.Session.query(UserSubjectMonitoring)\
            .filter_by(user=self, subject=subject, ignored=ignored).first()
        if usm is None:
            usm = UserSubjectMonitoring(self, subject, ignored=ignored)
            meta.Session.add(usm)

    def _unsetWatchedSubject(self, subject, ignored):
        usm = meta.Session.query(UserSubjectMonitoring)\
            .filter_by(user=self, subject=subject, ignored=ignored).first()
        if usm is not None:
            meta.Session.delete(usm)

    def watchSubject(self, subject):
        self._setWatchedSubject(subject, ignored=False)

    def unwatchSubject(self, subject):
        self._unsetWatchedSubject(subject, ignored=False)

    def ignoreSubject(self, subject):
        self._setWatchedSubject(subject, ignored=True)

    def unignoreSubject(self, subject):
        self._unsetWatchedSubject(subject, ignored=True)

    def url(self, controller='user', action='index', **kwargs):
        kwargs.setdefault('id', self.url_name or self.id)
        return url(controller=controller, action=action, **kwargs)

    def watches(self, subject):
        return subject in self.watched_subjects

    @property
    def groups(self):
        from ututi.model import Group
        from ututi.model import GroupMember
        return meta.Session.query(Group).join(GroupMember).order_by(Group.title.asc()).filter(GroupMember.user == self).all()

    @property
    def group_ids(self):
        return [g.id for g in self.groups]

    @property
    def groups_uploadable(self):
        from ututi.model import Group
        from ututi.model import GroupMember
        return meta.Session.query(Group).join(GroupMember).filter(GroupMember.user == self)\
            .filter(Group.has_file_area == True).all()

    def all_medals(self):
        """Return a list of medals for this user, including implicit medals."""
        from ututi.model import GroupMember, Payment
        from ututi.model import GroupMembershipType
        is_moderator = bool(meta.Session.query(GroupMember
            ).filter_by(user=self, role=GroupMembershipType.get('moderator')
            ).count())
        is_admin = bool(meta.Session.query(GroupMember
            ).filter_by(user=self, role=GroupMembershipType.get('administrator')
            ).count())
        is_supporter = bool(meta.Session.query(Payment
            ).filter_by(user=self, payment_type='support'
            ).filter_by(raw_error='').count())

        implicit_medals = {'support': is_moderator,
                           'admin': is_admin,
                           'buyer': is_supporter}

        medals = list(self.medals)

        def has_medal(medal_type):
            for medal in medals:
                if medal.medal_type == medal_type:
                    return True
            else:
                return False

        for medal_type, test_f in implicit_medals.items():
            if test_f and not has_medal(medal_type):
                medals.append(ImplicitMedal(self, medal_type))
        order = [m[0] for m in Medal.available_medals()]
        medals.sort(key=lambda m: order.index(m.medal_type))
        return medals

    def __init__(self, fullname, username, location, password, gen_password=True):
        self.fullname = fullname
        self.location = location
        self.username = username
        self.update_password(password, gen_password)

    def update_password(self, password, gen_password=True):
        if gen_password:
            self.password = generate_password(password)
        else:
            self.password = password

    def gen_recovery_key(self):
        self.recovery_key = ''.join(Random().sample(string.ascii_lowercase, 8))

    def update_logo_from_facebook(self):
        if self.logo is None: # Never overwrite a custom logo.
            self.logo = read_facebook_logo(self.facebook_id)

    def download(self, file, range_start=None, range_end=None):
        from ututi.model import FileDownload
        self.downloads.append(FileDownload(self, file, range_start, range_end))

    def download_count(self):
        from ututi.model import FileDownload
        download_count = meta.Session.query(FileDownload)\
            .filter(FileDownload.user==self)\
            .filter(FileDownload.range_start==None)\
            .filter(FileDownload.range_end==None).count()
        return download_count

    def download_size(self):
        from ututi.model import File, FileDownload
        download_size = meta.Session.query(func.sum(File.filesize))\
            .filter(FileDownload.file_id==File.id)\
            .filter(FileDownload.user==self)\
            .filter(FileDownload.range_start==None)\
            .filter(FileDownload.range_end==None)\
            .scalar()
        if not download_size:
            return 0
        return int(download_size)

    @property
    def isConfirmed(self):
        return self.email.confirmed

    logo = logo_property()

    def has_logo(self):
        return bool(meta.Session.query(User).filter_by(id=self.id).filter(User.raw_logo != None).count())

    def unread_messages(self):
        from ututi.model import PrivateMessage
        return meta.Session.query(PrivateMessage).filter_by(recipient=self, is_read=False).count()

    def purchase_sms_credits(self, credits):
        self.sms_messages_remaining += credits
        log.info("user %(id)d (%(fullname)s) purchased %(credits)s credits; current balance: %(current)d credits." % dict(id=self.id, fullname=self.fullname, credits=credits, current=self.sms_messages_remaining))

    def can_send_sms(self, group):
        return self.sms_messages_remaining > len(group.recipients_sms(sender=self))

    @property
    def ignored_events_list(self):
        return self.ignored_events.split(',')

    @property
    def all_subjects(self):
        return self.watched_subjects

    def update_ignored_events(self, events):
        self.ignored_events = ','.join(list(set(events)))

    def is_freshman(self):
        if not hasattr(self, '_is_freshman'):
            done = user_done_items(self)
            self._is_freshman = True
            # more than tree actions complete
            if len(done) >= 3:
                self._is_freshman = False
            # more than two actions + more than two weeks
            if self.accepted_terms and len(done) >= 2 and \
                self.accepted_terms < datetime.now() - timedelta(weeks=2):
                self._is_freshman = False
        return self._is_freshman

    @CachedProperty
    def moderated_tags(self):
        # XXX Circular imports!
        from ututi.model import LocationTag, Group, GroupMember
        return meta.Session.query(LocationTag)\
            .join(Group).join(GroupMember)\
            .filter(Group.moderators == True)\
            .filter(GroupMember.user == self)\
            .all()

    def get_wall_events_query(self):
        user_is_admin_of_groups = [membership.group_id
                                   for membership in self.memberships
                                   if membership.membership_type == 'administrator']
        subjects = self.all_watched_subjects
        if self.is_teacher:
            subjects += self.taught_subjects
        from ututi.lib.wall import generic_events_query
        evts_generic = generic_events_query()

        t_evt = meta.metadata.tables['events']
        t_evt_comments = meta.metadata.tables['event_comments']
        t_wall_posts = meta.metadata.tables['wall_posts']
        t_content_items = meta.metadata.tables['content_items']
        subject_ids = [s.id for s in subjects]
        group_ids = [m.group.id for m in self.memberships]
        user_commented_evts_select = select([t_evt_comments.c.event_id],
                                            from_obj=[t_evt_comments.join(t_content_items,
                                                                          t_content_items.c.id == t_evt_comments.c.id)],)\
            .where(t_content_items.c.created_by == self.id)
        user_commented_evts = map(lambda r: r[0], meta.Session.execute(user_commented_evts_select).fetchall())

        query = evts_generic\
            .where(or_(or_(t_evt.c.object_id.in_(subject_ids),
                           t_wall_posts.c.subject_id.in_(subject_ids)) if subject_ids else False,  # subject wall posts
                       and_(or_(t_evt.c.author_id == self.id,  # location wall posts
                                # XXX User comments may grow to 1k-10k scale, consider a different implementation.
                                t_evt.c.id.in_(user_commented_evts) if user_commented_evts else False),
                            t_evt.c.event_type.in_(('subject_wall_post', 'location_wall_post'))),
                       or_(t_evt.c.object_id.in_(group_ids),) if group_ids else False))\
            .where(or_(t_evt.c.event_type != 'moderated_post_created',
                       t_evt.c.object_id.in_(user_is_admin_of_groups) if user_is_admin_of_groups else False))\
            .where(not_(t_evt.c.event_type.in_(self.ignored_events_list) if self.ignored_events_list else False))
        return query

    def get_new_wall_events_count(self):
        t_evt = meta.metadata.tables['events']
        q = self.get_wall_events_query().where(t_evt.c.last_activity > self.last_seen_feed)
        events = meta.Session.execute(q)
        return len(events.fetchall())


class AnonymousUser(object):
    """Helper class for dealing with anonymous users. No ORM."""

    def __init__(self, name=None, email=None):
        self.name = name
        self.email = email

    @property
    def fullname(self):
        name = self.name or _("Anonymous")
        if self.email:
            return '%s <%s>' % (name, self.email)
        else:
            return name

    def has_logo(self):
        return False

    def url(self, controller='anonymous', action=None, **kwargs):
        if action is None:
            return 'mailto:%s' % self.email
        else:
            return url(controller=controller, action=action, **kwargs)


class Email(object):
    """Class representing one email address of a user."""

    def __init__(self, email, confirmed=False, main=True):
        self.email = email.strip().lower()
        self.confirmed = confirmed
        self.main = main

    @classmethod
    def get(cls, email):
        try:
            return meta.Session.query(Email).filter(Email.email == email.lower()).one()
        except NoResultFound:
            return None


class ImplicitMedal(object):
    """Helper for medals.

    This is a separate class from Medal so that implicit medals can be
    instantiated without touching the database.
    """

    MEDAL_IMG_PATH = '/images/medals/'
    MEDAL_SIZE = dict(height=26, width=26)

    def __init__(self, user, medal_type):
        assert medal_type in self.available_medal_types(), medal_type
        self.user = user
        self.medal_type = medal_type

    @staticmethod
    def available_medals():
        return [
                ('admin2', _('Admin')),
                ('support2', _('Distinguished moderator')),
                ('ututiman2', _('Champion')),
                ('ututiman', _('Distinguished user')),
                ('buyer2', _('Gold sponsor')),
                ('buyer', _('Sponsor')),
                ('support', _('Moderator')),
                ('admin', _('Group admin')),
                ]

    @staticmethod
    def available_medal_types():
        return [m[0] for m in Medal.available_medals()]

    def url(self):
        return self.MEDAL_IMG_PATH + self.medal_type + '.png'

    def title(self):
        return dict(self.available_medals())[self.medal_type]

    def img_tag(self):
        return image(self.url(), alt=self.title(), title=self.title(),
                     **self.MEDAL_SIZE)


class Medal(ImplicitMedal):
    """A persistent medal for a user."""


class Teacher(User):
    """A separate class for the teachers at Ututi."""
    is_teacher = True

    def __init__(self, **kwargs):
        self.teacher_verified = False
        super(Teacher, self).__init__(**kwargs)

    def teaches(self, subject):
        return subject in self.taught_subjects

    def teach_subject(self, subject):
        if not self.teaches(subject):
            self.taught_subjects.append(subject)

    def unteach_subject(self, subject):
        if self.teaches(subject):
            self.taught_subjects.remove(subject)

    @property
    def share_info(self):
        if self.location:
            caption = ' '.join(self.location.title_path) + ' ' + _("teacher")
        else:
            caption = _("Teacher")
        return dict(title=self.fullname,
                    caption=caption,
                    link=self.url(qualified=True),
                    description=self.description)

    @property
    def all_subjects(self):
        return self.taught_subjects + self.watched_subjects

    def snippet(self):
        """Render a short snippet with the basic teacher information.
        Used in university's teacher catalog to render search results."""
        return render_mako_def('/sections/content_snippets.mako', 'teacher', object=self)

    def url(self, controller='user', action='teacher_index', **kwargs):
        kwargs.setdefault('id', self.url_name or self.id)
        if action.startswith('external'):
            kwargs.setdefault('path', self.location.url_path)
        return url(controller=controller, action=action, **kwargs)

    def is_freshman(self):
        if not hasattr(self, '_is_freshman'):
            self._is_freshman = len(teacher_done_items(self)) < 3
        return self._is_freshman

    def confirm(self):
        self.teacher_verified = True

    def revert_to_user(self):
        """Revert teacher account to user account. This is called when teacher
        registration is not verified by administrators."""

        # move taught subjects to watched subject list
        for subject in self.taught_subjects:
            if subject not in self.watched_subjects:
                self.watchSubject(subject)
        meta.Session.commit()

        # a hack: cannot update a polymorphic descriptor column using the orm
        authors_table = meta.metadata.tables['authors']
        teachers_table = meta.metadata.tables['teachers']
        conn = meta.engine.connect()
        upd = authors_table.update().where(authors_table.c.id==self.id).values(type='user')
        ins = teachers_table.delete().where(teachers_table.c.id==self.id)
        conn.execute(upd)
        conn.execute(ins)


class GroupNotFoundException(Exception):
    pass


class TeacherGroup(object):
    def __init__(self, title, email):
        self.title = title
        self.email = email
        self.update_binding()

    @classmethod
    def get(cls, id):
        try:
            return meta.Session.query(cls).filter_by(id=id).one()
        except NoResultFound:
            return None

    def update_binding(self):
        from ututi.model import Group
        hostname = config.get('mailing_list_host', 'groups.ututi.lt')
        self.group = None
        if self.email.endswith(hostname):
            group = Group.get(self.email[:-(len(hostname)+1)])
            if group is not None:
                self.group = group
            else:
                raise GroupNotFoundException()


class UserRegistration(object):
    """User registration data."""

    def __init__(self, location=None, email=None, facebook_id=None, name=None):
        """Either email or facebook_id should be given, if location is None,
        then email is required  (this is checked in db).
        """
        self.location = location
        self.email = email
        self.facebook_id = facebook_id
        self.fullname = name

        if email:
            self.hash = hashlib.md5(datetime.now().isoformat() + \
                                    email).hexdigest()
        elif facebook_id:
            self.hash = hashlib.md5(datetime.now().isoformat() + \
                                    str(facebook_id)).hexdigest()

    @classmethod
    def create_or_update(cls, location, email=None, facebook_id=None, name=None):
        """If another pending registration is found in the same university,
        then it is updated and returned. Otherwise new registration is created.
        """
        if email is None and facebook_id is None:
            raise ValueError('Either email or facebook id must be given')

        q = meta.Session.query(cls).filter_by(completed=False)
        if email is not None:
            q = q.filter_by(email=email)
        if facebook_id is not None:
            q = q.filter_by(facebook_id=facebook_id)
        if location is None:
            q = q.filter_by(location=None)
        else:
            loc_ids = [loc.id for loc in location.root.flatten]
            q = q.filter(cls.location_id.in_(loc_ids))

        registration = q.first()

        if registration is None:
            registration = cls(location, email, facebook_id, name)
            meta.Session.add(registration)
        else:
            registration.location = location # update

        return registration

    @classmethod
    def get(cls, id):
        try:
            return meta.Session.query(cls).filter(cls.id == id).one()
        except NoResultFound:
            return None

    @classmethod
    def get_by_hash(cls, hash):
        try:
            return meta.Session.query(cls).filter(cls.hash == hash).one()
        except NoResultFound:
            return None

    def update_password(self, password_plain):
        self.password = generate_password(password_plain)

    logo = logo_property()

    def has_logo(self):
        return self.logo is not None

    def update_logo_from_facebook(self):
        if self.logo is None: # Never overwrite a custom logo.
            self.logo = read_facebook_logo(self.facebook_id)

    university_logo = logo_property(logo_attr='raw_university_logo')

    def send_confirmation_email(self):
        send_email_confirmation_code(self.email,
                                     self.url(action='confirm_email',
                                                      qualified=True))

    def create_user(self):
        """Returns a User object filled with registration data."""
        args = dict(fullname=self.fullname,
                    username=self.email,
                    location=self.location,
                    password=self.password,
                    gen_password=False)

        user = Teacher(**args) if self.teacher else User(**args)
        from string import lower
        emails_src = [self.email, self.openid_email, self.facebook_email]
        emails_src = map(lower, filter(bool, emails_src))
        # remove duplicate emails while preserving order
        emails = []
        seen = set()
        for email in emails_src:
            if email not in seen:
                emails.append(email)
                seen.add(email)

        user.emails = [Email(email, confirmed=True, main=(n == 0)) for n, email in enumerate(emails)]
        user.openid = self.openid
        user.facebook_id = self.facebook_id
        user.logo = self.logo
        user.accepted_terms = datetime.utcnow()
        self.user = user # store reference

        return user

    def create_university(self):
        from ututi.model import LocationTag, EmailDomain

        # parse short title from url
        title_short = urlparse(self.university_site_url).netloc
        if title_short.startswith('www.'):
            title_short = title_short.replace('www.', '', 1)

        university = LocationTag(self.university_title, title_short, confirmed=False)

        # fill out the rest of information
        university.site_url = self.university_site_url
        university.logo = self.university_logo
        university.country = self.university_country
        university.member_policy = self.university_member_policy
        for domain_name in self.university_allowed_domains.split(','):
            university.email_domains.append(EmailDomain(domain_name))

        return university

    def url(self, controller='registration', action='confirm', **kwargs):
        return url(controller=controller,
                   action=action,
                   hash=self.hash,
                   **kwargs)
