"""The application's model objects"""
import PIL
from PIL import Image
import sys
import os
import hashlib
import binascii
import lxml
import logging
import warnings
import string
import StringIO
from math import ceil
from random import Random
from binascii import a2b_base64, b2a_base64
from pylons import url
from random import randrange
import pkg_resources
from datetime import date, datetime, timedelta
from ututi.lib import urlify

from pylons import config
from pylons.templating import render_mako_def

from sqlalchemy import orm, Column, Integer, Sequence, Table
from sqlalchemy.types import Unicode
from sqlalchemy.exc import DatabaseError, SAWarning
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import relation, backref, deferred
from sqlalchemy import func
from sqlalchemy.sql.expression import desc
from sqlalchemy.sql.expression import and_, or_
from sqlalchemy.orm.interfaces import MapperExtension

from ututi.migration import GreatMigrator
from ututi.model import meta
from ututi.lib.helpers import image
from ututi.lib.emails import group_invitation_email
from ututi.lib.security import check_crowds
from nous.mailpost import copy_chunked

from zope.cachedescriptors.property import Lazy

from pylons.i18n import _

log = logging.getLogger(__name__)

def init_model(engine):
    """Call me before using any of the tables or classes in the model"""
    ## Reflected tables must be defined and mapped here
    meta.Session.configure(bind=engine)
    meta.engine = engine


def process_logo(value):
    if value is None:
        return

    image = Image.open(StringIO.StringIO(value))

    width = height = 500
    if image.size[0] < width and image.size[1] < height:
        return value

    width = min(width, image.size[0])
    height = min(height, image.size[1])

    width = float(width)
    height = float(height)
    limit_x = width / height

    original_x = float(image.size[0]) / image.size[1]

    if limit_x > original_x:
        width = height * original_x
    elif limit_x <= original_x:
        height = width / original_x

    new_image = image.resize((int(width), int(height)), PIL.Image.ANTIALIAS)
    # Try saving as png
    png_buffer = StringIO.StringIO()
    new_image.save(png_buffer, "PNG")
    png_result = png_buffer.getvalue()

    # Try preserving original format (JPEG most of the time)
    orig_buffer = StringIO.StringIO()
    new_image.save(orig_buffer, image.format)
    orig_result = orig_buffer.getvalue()

    # see which one is the smallest one, resized png, resized original
    # or plain original
    size, result = min((len(png_result), png_result),
                       (len(orig_result), orig_result),
                       (len(value), value))
    return result


def logo_property():
    def get(self):
        return self.raw_logo
    def set(self, value):
        self.raw_logo = process_logo(value)
    return property(get, set)


def setup_orm(engine):
    #relationships between content items and tags
    global files_table
    files_table = Table("files", meta.metadata,
                        Column('filename', Unicode(assert_unicode=True)),
                        Column('folder', Unicode(assert_unicode=True)),
                        Column('title', Unicode(assert_unicode=True)),
                        Column('description', Unicode(assert_unicode=True)),
                        autoload=True,
                        useexisting=True,
                        autoload_with=engine)

    global file_downloads_table
    file_downloads_table = Table("file_downloads", meta.metadata,
                                 autoload=True,
                                 autoload_with=engine)


    global forum_categories_table
    forum_categories_table = Table("forum_categories", meta.metadata,
                         autoload=True,
                         autoload_with=engine)


    global forum_posts_table
    forum_posts_table = Table("forum_posts", meta.metadata,
                              Column('title', Unicode(assert_unicode=True)),
                              Column('message', Unicode(assert_unicode=True)),
                              autoload=True,
                              useexisting=True,
                              autoload_with=engine)

    global seen_threads_table
    seen_threads_table = Table("seen_threads", meta.metadata,
                              autoload=True,
                              useexisting=True,
                              autoload_with=engine)

    global subscribed_threads_table
    subscribed_threads_table = Table("subscribed_threads", meta.metadata,
                              autoload=True,
                              useexisting=True,
                              autoload_with=engine)

    global users_table
    users_table = Table("users", meta.metadata,
                        Column('id', Integer, Sequence('users_id_seq'), primary_key=True),
                        Column('fullname', Unicode(assert_unicode=True)),
                        Column('description', Unicode(assert_unicode=True)),
                        Column('site_url', Unicode(assert_unicode=True)),
                        autoload=True,
                        useexisting=True,
                        autoload_with=engine)

    global content_items_table
    content_items_table = Table("content_items", meta.metadata,
                                autoload=True,
                                autoload_with=engine)

    global content_tags_table
    content_tags_table = Table("content_tags", meta.metadata,
                               autoload=True,
                               autoload_with=engine)

    global tags_table
    tags_table = Table("tags", meta.metadata,
                               Column('id', Integer, Sequence('tags_id_seq'), primary_key=True),
                               Column('title_short', Unicode(assert_unicode=True)),
                               Column('title', Unicode(assert_unicode=True)),
                               Column('description', Unicode(assert_unicode=True)),
                               Column('site_url', Unicode(assert_unicode=True)),
                               useexisting=True,
                               autoload=True,
                               autoload_with=engine)
    tag_mapper = orm.mapper(Tag,
                            tags_table,
                            polymorphic_on=tags_table.c.tag_type,
                            polymorphic_identity='',
                            properties={'raw_logo': deferred(tags_table.c.logo)})

    orm.mapper(LocationTag,
               inherits=Tag,
               polymorphic_on=tags_table.c.tag_type,
               polymorphic_identity='location',
               properties = {'children': relation(LocationTag, order_by=LocationTag.title.asc(), backref=backref('parent', remote_side=tags_table.c.id))})

    orm.mapper(SimpleTag,
               inherits=tag_mapper,
               polymorphic_on=tags_table.c.tag_type,
               polymorphic_identity='tag')

    orm.mapper(ContentItem,
               content_items_table,
               polymorphic_on=content_items_table.c.content_type,
               polymorphic_identity='generic',
               properties = {'created': relation(User,
                                                 primaryjoin=content_items_table.c.created_by==users_table.c.id),
                             'modified': relation(User,
                                                  primaryjoin=content_items_table.c.modified_by==users_table.c.id),
                             'deleted': relation(User,
                                                 primaryjoin=content_items_table.c.deleted_by==users_table.c.id),
                             'tags': relation(SimpleTag,
                                              secondary=content_tags_table),
                             'location': relation(LocationTag)})

    orm.mapper(File, files_table,
               inherits=ContentItem,
               inherit_condition=files_table.c.id==ContentItem.id,
               polymorphic_identity='file',
               polymorphic_on=content_items_table.c.content_type,
               extension=NotifyGG(),
               properties = {'parent': relation(ContentItem,
                                                primaryjoin=files_table.c.parent_id==content_items_table.c.id,
                                                backref=backref("files", order_by=files_table.c.filename.asc()))})

    orm.mapper(ForumCategory, forum_categories_table,
               properties={'group': relation(Group,
                                       backref=backref("forum_categories",
                                          order_by=forum_categories_table.c.id.asc()))})

    orm.mapper(ForumPost, forum_posts_table,
               inherits=ContentItem,
               inherit_condition=forum_posts_table.c.id==ContentItem.id,
               polymorphic_identity='forum_post',
               polymorphic_on=content_items_table.c.content_type,
               properties = {'category': relation(ForumCategory,
                                                  backref="posts"),
                             'parent': relation(ContentItem,
                                                primaryjoin=forum_posts_table.c.parent_id==content_items_table.c.id,
                                                backref="forum_posts")
                            })

    orm.mapper(SeenThread, seen_threads_table,
               properties = {'thread': relation(ForumPost),
                             'user': relation(User)})


    orm.mapper(SubscribedThread, subscribed_threads_table,
               properties = {'thread': relation(ForumPost,
                                                backref='subscriptions'),
                             'user': relation(User)})

    orm.mapper(User,
               users_table,
               properties = {'emails': relation(Email, backref='user'),
                             'medals': relation(Medal, backref='user'),
                             'raw_logo': deferred(users_table.c.logo),
                             'location': relation(LocationTag)})

    orm.mapper(FileDownload,
               file_downloads_table,
               properties = {'user' : relation(User, backref='downloads'),
                             'file' : relation(File)})

    global emails_table
    emails_table = Table("emails", meta.metadata,
                         autoload=True,
                         autoload_with=engine)
    orm.mapper(Email, emails_table)

    global user_medals_table
    user_medals_table = Table("user_medals", meta.metadata,
                              autoload=True,
                              autoload_with=engine)
    orm.mapper(Medal, user_medals_table)

    global subject_pages_table
    subject_pages_table = Table("subject_pages", meta.metadata,
                                autoload=True,
                                autoload_with=engine)

    global pages_table
    pages_table = Table("pages", meta.metadata,
                        autoload=True,
                        autoload_with=engine)
    orm.mapper(Page, pages_table,
               inherits=ContentItem,
               polymorphic_identity='page',
               polymorphic_on=content_items_table.c.content_type)

    global page_versions_table
    page_versions_table = Table("page_versions", meta.metadata,
                                Column('title', Unicode(assert_unicode=True)),
                                Column('content', Unicode(assert_unicode=True)),
                                autoload=True,
                                autoload_with=engine)
    orm.mapper(PageVersion, page_versions_table,
               inherits=ContentItem,
               polymorphic_identity='page_version',
               polymorphic_on=content_items_table.c.content_type,
               inherit_condition=page_versions_table.c.id == content_items_table.c.id,
               properties={'page': relation(Page,
                                            primaryjoin=pages_table.c.id==page_versions_table.c.page_id,
                                            backref=backref('versions',
                                                            order_by=content_items_table.c.created_on.desc()))})

    global subjects_table
    subjects_table = Table("subjects", meta.metadata,
                           Column('title', Unicode(assert_unicode=True)),
                           Column('lecturer', Unicode(assert_unicode=True)),
                           Column('description', Unicode(assert_unicode=True)),
                           autoload=True,
                           useexisting=True,
                           autoload_with=engine)
    orm.mapper(Subject, subjects_table,
               inherits=ContentItem,
               polymorphic_identity='subject',
               polymorphic_on=content_items_table.c.content_type,
               properties={'pages': relation(Page,
                                             secondary=subject_pages_table,
                                             backref="subject")})

    global group_membership_types_table
    group_membership_types_table = Table("group_membership_types", meta.metadata,
                                         autoload=True,
                                         autoload_with=engine)
    orm.mapper(GroupMembershipType,
               group_membership_types_table)

    global group_members_table
    group_members_table = Table("group_members", meta.metadata,
                                autoload=True,
                                autoload_with=engine)
    orm.mapper(GroupMember,
               group_members_table,
               properties = {'user': relation(User, backref='memberships'),
                             'group': relation(Group, backref=backref('members', cascade='save-update, merge, delete')),
                             'role': relation(GroupMembershipType)})


    global groups_table
    groups_table = Table("groups", meta.metadata,
                         Column('title', Unicode(assert_unicode=True)),
                         Column('description', Unicode(assert_unicode=True)),
                         Column('page', Unicode(assert_unicode=True)),
                         useexisting=True,
                         autoload=True,
                         autoload_with=engine)

    global group_watched_subjects_table
    group_watched_subjects_table = Table("group_watched_subjects", meta.metadata,
                                         autoload=True,
                                         autoload_with=engine)

    orm.mapper(Group, groups_table,
               inherits=ContentItem,
               polymorphic_identity='group',
               polymorphic_on=content_items_table.c.content_type,
               properties ={'watched_subjects': relation(Subject,
                                                         backref=backref("watching_groups", lazy=True),
                                                         secondary=group_watched_subjects_table),
                            'raw_logo': deferred(groups_table.c.logo)})

    orm.mapper(GroupSubjectMonitoring, group_watched_subjects_table,
               properties ={'subject': relation(Subject),
                            'group': relation(Group)
                            })


    global group_invitations_table
    group_invitations_table = Table("group_invitations", meta.metadata,
                                    autoload=True,
                                    autoload_with=engine)

    global group_requests_table
    group_requests_table = Table("group_requests", meta.metadata,
                                    autoload=True,
                                    autoload_with=engine)

    orm.mapper(PendingRequest, group_requests_table,
               properties = {'group': relation(Group, backref=backref('requests', cascade='save-update, merge, delete')),
                             'user': relation(User,
                                              primaryjoin=group_requests_table.c.user_id==users_table.c.id,
                                              backref='requests')})

    orm.mapper(PendingInvitation, group_invitations_table,
               properties = {'user': relation(User,
                                              primaryjoin=group_invitations_table.c.user_id==users_table.c.id,
                                              backref='invitations'),
                             'author': relation(User,
                                                primaryjoin=group_invitations_table.c.author_id==users_table.c.id),
                             'group': relation(Group, backref=backref('invitations', cascade='save-update, merge, delete'))})

    global user_monitored_subjects_table
    user_monitored_subjects_table = Table("user_monitored_subjects", meta.metadata,
                                        autoload=True,
                                        autoload_with=engine)

    orm.mapper(UserSubjectMonitoring, user_monitored_subjects_table,
               properties ={'subject': relation(Subject, backref=backref("watching_users", lazy=True)),
                            'user': relation(User)
                            })

    # ignoring error about unknown column type for now
    warnings.simplefilter("ignore", SAWarning)

    global search_items_table
    search_items_table = Table("search_items", meta.metadata,
                               autoload=True,
                               autoload_with=engine)

    global tag_search_items_table
    tag_search_items_table = Table("tag_search_items", meta.metadata,
                                   autoload=True,
                                   autoload_with=engine)

    warnings.simplefilter("default", SAWarning)

    orm.mapper(SearchItem, search_items_table,
               properties={'object' : relation(ContentItem, lazy=True, backref=backref("search_item", uselist=False, cascade="all"))})

    orm.mapper(TagSearchItem, tag_search_items_table,
               properties={'tag' : relation(LocationTag)})

    global blog_table
    blog_table = Table("blog", meta.metadata,
                       Column('content', Unicode(assert_unicode=True)),
                       autoload=True,
                       useexisting=True,
                       autoload_with=engine)

    orm.mapper(BlogEntry, blog_table)

    global payments_table
    payments_table = Table("payments", meta.metadata,
                           autoload=True,
                           useexisting=True,
                           autoload_with=engine)
    orm.mapper(Payment, payments_table,
               properties={'user': relation(User),
                           'group': relation(Group, backref=backref('payments', order_by=payments_table.c.created.desc()))})

    from ututi.model import mailing
    mailing.setup_orm(engine)

    from ututi.model import events
    events.setup_orm(engine)


def reset_db(engine):
    connection = meta.engine.connect()
    connection.execute("drop schema public cascade;")
    connection.execute("create schema public;")
    connection.close()


def initialize_dictionaries(engine):
    initial_db_data = pkg_resources.resource_string(
        "ututi",
        "model/stemming.sql").split(";;")
    connection = meta.engine.connect()
    for statement in initial_db_data:
        statement = statement.strip()
        if (statement):
            try:
                txn = connection.begin()
                connection.execute(statement)
                txn.commit()
            except DatabaseError, e:
                print >> sys.stderr, ""
                print >> sys.stderr, e.message
                print >> sys.stderr, e.statement
                txn.rollback()
                return
    connection.close()


def initialize_db_defaults(engine):
    initial_db_data = pkg_resources.resource_string(
        "ututi",
        "model/defaults.sql").split(";;")
    connection = meta.engine.connect()
    for statement in initial_db_data:
        statement = statement.strip()
        if (statement):
            try:
                txn = connection.begin()
                connection.execute(statement)
                txn.commit()
            except DatabaseError, e:
                print >> sys.stderr, ""
                print >> sys.stderr, e.message
                print >> sys.stderr, e.statement
                txn.rollback()
                return
    connection.close()
    migrator = GreatMigrator(engine)
    migrator.initializeVersionning()


def teardown_db_defaults(engine, quiet=False):
    connection = meta.engine.connect()
    tx = connection.begin()
    connection.execute("drop schema public cascade")
    connection.execute("create schema public")
    tx.commit()
    connection.close()


content_items_table = None
class ContentItem(object):
    """A generic class for content items."""

    @classmethod
    def get(cls, id):
        try:
            return meta.Session.query(cls).filter_by(id=id).one()
        except NoResultFound:
            return None

    def url(self):
        raise NotImplementedError("This method should be overridden by content"
                                  " objects to provide their urls.")

    def snippet(self):
        """Render a short snippet with the basic item's information. Used in search to render the results."""
        return render_mako_def('/sections/content_snippets.mako','generic', object=self)

    def isDeleted(self):
        return self.deleted_on is not None

    def rating(self):
        """Rank the subject from 0 to 5."""
        intervals = ((5, 50), (4, 30), (3, 15), (2, 5), (1, 1))

        for level, limit in intervals:
            if self.search_item.rating >= limit:
                return level
        return 0

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
    try:
        ref = a2b_base64(reference)
    except binascii.Error:
        return False
    salt = ref[20:]
    compare = b2a_base64(hashlib.sha1(password + salt).digest() + salt)[:-1]
    return compare == reference


class UserSubjectMonitoring(object):

    def __init__(self, user, subject, ignored=False):
        self.user, self.subject, self.ignored = user, subject, ignored


users_table = None
user_monitored_subjects_table = None

class User(object):

    @property
    def email(self):
        email = self.emails[0]
        return email

    def send(self, msg):
        """Send a message to the user."""
        email = self.emails[0]
        if email.confirmed or msg.force:
            msg.send(email.email)
        else:
            log.info("Could not send message to uncofirmed email %(email)s" % dict(email=email.email))

    def checkPassword(self, password):
        """Check the user's password."""
        return validate_password(self.password, password)

    @classmethod
    def authenticate(cls, username, password):
        try:
            user = meta.Session.query(Email).filter_by(email=username.strip().lower()).one().user
            if validate_password(user.password, password):
                return username
            else:
                return None
        except NoResultFound:
            return None
        return None

    @classmethod
    def get(cls, username):
        """Get a user by his email."""
        try:
            return meta.Session.query(Email).filter_by(email=username.lower()).one().user
        except NoResultFound:
            return None

    @classmethod
    def get_byid(cls, id):
        try:
            return meta.Session.query(cls).filter_by(id=id).one()
        except NoResultFound:
            return None

    @property
    def ignored_subjects(self):
        umst = user_monitored_subjects_table
        user_ignored_subjects = meta.Session.query(Subject)\
            .join((umst,
                   and_(umst.c.subject_id==subjects_table.c.id,
                        umst.c.subject_id==subjects_table.c.id)))\
            .filter(and_(umst.c.user_id == self.id,
                         umst.c.ignored == True))
        return user_ignored_subjects.all()

    @property
    def watched_subjects(self):
        umst = user_monitored_subjects_table
        directly_watched_subjects = meta.Session.query(Subject)\
            .join((umst,
                   and_(umst.c.subject_id==subjects_table.c.id,
                        umst.c.subject_id==subjects_table.c.id)))\
            .filter(and_(umst.c.user_id == self.id,
                         umst.c.ignored == False))
        return directly_watched_subjects.all()

    @property
    def all_watched_subjects(self):
        umst = user_monitored_subjects_table
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

        gwst = group_watched_subjects_table
        gmt = group_members_table
        gt = groups_table
        group_watched_subjects = meta.Session.query(Subject)\
            .join((gwst,
                   and_(gwst.c.subject_id==subjects_table.c.id,
                        gwst.c.subject_id==subjects_table.c.id)))\
            .join((gmt, gmt.c.group_id == gwst.c.group_id))\
            .join((gt, gmt.c.group_id == gt.c.id))\
            .filter(gmt.c.user_id == self.id)
        return directly_watched_subjects.union(
            group_watched_subjects.except_(user_ignored_subjects))\
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
        return url(controller=controller,
                   action=action,
                   id=self.id,
                   **kwargs)

    def watches(self, subject):
        return subject in self.watched_subjects

    @property
    def groups(self):
        return [membership.group
                for membership in self.memberships]

    def all_medals(self):
        """Return a list of medals for this user, including implicit medals."""
        is_moderator = bool(meta.Session.query(GroupMember
            ).filter_by(user=self, role=GroupMembershipType.get('moderator')
            ).count())
        is_admin = bool(meta.Session.query(GroupMember
            ).filter_by(user=self, role=GroupMembershipType.get('administrator')
            ).count())
        is_supporter = bool(meta.Session.query(Payment
            ).filter_by(user=self, payment_type='support'
            ).count())

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
                medals.append(Medal(self, medal_type))
        order = [m[0] for m in Medal.available_medals()]
        medals.sort(key=lambda m: order.index(m.medal_type))
        return medals

    def __init__(self, fullname, password, gen_password=True):
        self.fullname = fullname
        self.update_password(password, gen_password)

    def update_password(self, password, gen_password=True):
        self.password = password
        if gen_password:
            self.password = generate_password(password)

    def download(self, file):
        self.downloads.append(FileDownload(self, file))

    @property
    def isConfirmed(self):
        return self.emails[0].confirmed

    logo = logo_property()


email_table = None

class Email(object):
    """Class representing one email address of a user."""

    def __init__(self, email):
        self.email = email.strip().lower()

    @classmethod
    def get(cls, email):
        try:
            return meta.Session.query(Email).filter(Email.email == email.lower()).one()
        except NoResultFound:
            return None


class Medal(object):
    """A medal for a user."""

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


class Folder(list):

    def __init__(self, title, parent):
        self.title = title
        self.parent = parent

    def can_write(self, user=None):
        if len(self) == 0 and user is None:
            return False
        can_write = True
        for file in self:
            can_write = can_write and file.can_write(user)
        return can_write


class FolderMixin(object):

    @property
    def folders_dict(self):
        result = {'': Folder('', parent=self)}
        for file in self.files:
            if file.deleted_by is None:
                result.setdefault(file.folder, Folder(file.folder, parent=self))
                if not file.isNullFile():
                    result[file.folder].append(file)
        return result

    def getFolder(self, title):
        return self.folders_dict.get(title, None)

    @property
    def folders(self):
        return sorted(self.folders_dict.values(), key=lambda f: f.title)


class LimitedUploadMixin(object):
    """Mix-in for determining whether uploads are enabled for the object."""

    CAN_UPLOAD = 1
    CAN_UPLOAD_SINGLE_FOLDER = 2
    LIMIT_REACHED = 0

    available_size = 1

    @property
    def paid(self):
        return True

    @property
    def upload_status(self):
        """Information on the group's file upload limits."""
        upload_status = self.free_size > 0 and self.CAN_UPLOAD or self.LIMIT_REACHED

        have_root_folder = len(self.folders) == 1
        if self.paid and have_root_folder:
            return self.CAN_UPLOAD_SINGLE_FOLDER
        elif self.paid:
            return self.CAN_UPLOAD

        can_upload = upload_status == self.CAN_UPLOAD
        if can_upload and have_root_folder:
            return self.CAN_UPLOAD_SINGLE_FOLDER

        return upload_status

    @property
    def file_count(self):
        return len([file for file in self.files if not file.isNullFile() and file.deleted_on is None])

    @property
    def size(self):
        return sum([file.size for file in self.files if not file.isNullFile() and file.deleted_on is None])

    @property
    def free_size(self):
        """The size of files in group private area is limited to 200 Mb."""
        avail = max(0, self.available_size - self.size)
        return avail

    @property
    def free_size_points(self):
        """Return the amount of free size in the area in points from 5 (empty) to 0 (full)."""
        pts = min(5, ceil(5 * float(self.size) / self.available_size))
        return pts


group_watched_subjects_table = None
groups_table = None

class GroupSubjectMonitoring(object):

    def __init__(self, group, subject, ignored=False):
        self.group, self.subject, self.ignored = group, subject, ignored


class Group(ContentItem, FolderMixin, LimitedUploadMixin):

    def send(self, msg):
        msg.send([mship.user for mship in self.members])

    def recipients(self, period):
        recipients = meta.Session.query(GroupMember).\
            filter_by(group=self, receive_email_each=period).all()
        return [recipient.user for recipient in recipients]

    def recipients_gg(self):
        recipients = meta.Session.query(GroupMember).\
            filter_by(group=self).all()
        return [recipient.user for recipient in recipients
                if (recipient.user.gadugadu_get_news and
                    recipient.user.gadugadu_confirmed)]

    @classmethod
    def get(cls, id):
        query = meta.Session.query(cls)
        try:
            if isinstance (id, (long, int)):
                return query.filter_by(id=id).one()
            else:
                return query.filter(func.lower(cls.group_id)==id.strip().lower()).one()
        except NoResultFound:
            return None

    @property
    def list_address(self):
        return "%s@%s" % (self.group_id, config.get('mailing_list_host', ''))

    @property
    def last_seen_members(self):
        gmt = group_members_table
        return meta.Session.query(User).join((gmt,
                                      gmt.c.user_id == users_table.c.id))\
                                      .filter(gmt.c.group_id == self.id)\
                                      .order_by(User.last_seen.desc()).all()

    def is_subscribed(self, user):
        membership = GroupMember.get(user, self)
        if self.mailinglist_enabled:
            return membership and membership.subscribed
        else:
            return membership and membership.subscribed_to_forum

    def set_subscription(self, user, subscribed=True):
        membership = GroupMember.get(user, self)
        if membership is None:
            return
        if self.mailinglist_enabled:
            membership.subscribed = subscribed
        else:
            membership.subscribed_to_forum = subscribed
        meta.Session.commit()

    def is_member(self, user):
        """Is the user a member of the group?"""
        return GroupMember.get(user, self)

    def is_admin(self, user):
        """Is the user an administrator of the group?"""
        membership = GroupMember.get(user, self)
        return membership and membership.is_admin

    @property
    def administrators(self):
        """List of all the administrators of the group."""
        admin_type = GroupMembershipType.get('administrator')
        return [membership.user for membership in self.members if membership.role == admin_type]

    def add_member(self, user, admin=False):
        if not self.is_member(user):
            membership = GroupMember(user, self, admin)
            meta.Session.add(membership)

    def url(self, controller='group', action='index', **kwargs):
        return url(controller=controller, action=action, id=self.group_id, **kwargs)

    def invite_user(self, email, author):
        user = User.get(email)
        if user is None or not self.is_member(user):
            try:
                invitation = meta.Session.query(PendingInvitation).filter_by(email=email, group=self).one()
                invitation.created = datetime.today()
            except NoResultFound:
                invitation = PendingInvitation(email, author=author, group=self)
                meta.Session.add(invitation)
            group_invitation_email(invitation, email)
            return invitation
        else:
            return None

    def request_join(self, user):
        request = PendingRequest(user, group=self)
        meta.Session.add(request)
        return request

    def snippet(self):
        """Render the group's information."""
        return render_mako_def('/sections/content_snippets.mako','group', object=self)


    def __init__(self, group_id, title=u'', location=None, year=None, description=u''):
        self.group_id = group_id.strip().lower()
        self.title = title
        self.location = location
        self.page = u''
        if year is None:
            year = date(date.today().year, 1, 1)
        self.year = year
        self.description = description

    @property
    def all_messages(self):
        return meta.Session.query(GroupMailingListMessage)\
            .filter_by(group_id=self.id)\
            .order_by(GroupMailingListMessage.sent.desc())\
            .all()

    def top_level_messages(self, sort=False, limit=None):
        if self.mailinglist_enabled:
            return self.top_level_messages_ml(sort=sort, limit=limit)
        else:
            return self.top_level_messages_forum(sort=sort, limit=limit)

    def top_level_messages_ml(self, sort=False, limit=None):
        messages = meta.Session.query(GroupMailingListMessage.thread_message_id,
                                      GroupMailingListMessage.thread_group_id,
                                      func.max(GroupMailingListMessage.sent).label('last_msg'))\
                                      .group_by(GroupMailingListMessage.thread_message_id, GroupMailingListMessage.thread_group_id)\
                                      .filter_by(group_id=self.id)\
                                      .order_by(desc('last_msg'))
        if limit is not None:
            messages = messages.limit(limit)

        for msg in messages.all():
            thread = GroupMailingListMessage.get(msg[0], msg[1])
            yield {'subject': thread.subject,
                   'url': thread.url(),
                   'last_reply': msg[2]}

    def top_level_messages_forum(self, sort=False, limit=None):
        category_ids = [r[0] for r in meta.Session.query(ForumCategory.id
                                        ).filter_by(group_id=self.id).all()]
        messages = meta.Session.query(
                ForumPost.thread_id,
                func.max(ForumPost.created_on).label('created_on'))\
                .group_by(ForumPost.thread_id, ForumPost.category_id)\
                .filter(ForumPost.category_id.in_(category_ids))\
                .order_by(desc('created_on'))
        if limit is not None:
            messages = messages.limit(limit)

        for msg in messages.all():
            post = ForumPost.get(msg[0])
            yield {'subject': post.title,
                   'url': post.url(new=True),
                   'last_reply': msg[1]}

    def all_files(self, limit=None):
        ids = [subject.id for subject in self.watched_subjects]
        ids.append(self.id)

        files = meta.Session.query(File).filter(File.parent_id.in_(ids)).filter(File.md5 != None).order_by(File.created_on.desc())
        if limit is not None:
            files = files.limit(limit)
        return files.all()

    @property
    def group_events(self):
        return self.filtered_events()

    def filtered_events(self, types=[], limit=20):
        from ututi.model.events import Event
        events = meta.Session.query(Event)\
            .filter(or_(Event.object_id.in_([s.id for s in self.watched_subjects]),
                        Event.object_id == self.id))
        if types != []:
            events = events.filter(Event.event_type.in_(types))

        events = events.order_by(Event.created.desc()).limit(limit).all()
        return events

    @property
    def message_count(self):
        from ututi.model.mailing import GroupMailingListMessage
        return meta.Session.query(GroupMailingListMessage)\
            .filter_by(group_id=self.id, reply_to=None)\
            .order_by(desc(GroupMailingListMessage.sent))\
            .count()

    logo = logo_property()

    @property
    def available_size(self):
        return int(config.get('group_file_limit', 100*1024**2))

    @property
    def paid(self):
        if len(self.payments) > 0:
            pmnt = self.payments[-1]
            period = 0
            if pmnt.amount == int(config.get('group_payment_month', 1000)):
                period = 31
            elif pmnt.amount == int(config.get('group_payment_quarter', 2000)):
                period = 100
            elif pmnt.amount == int(config.get('group_payment_halfyear', 3000)):
                period = 200
            return pmnt.created - datetime.utcnow() <= timedelta(days=period)
        return False


group_members_table = None

class GroupMember(object):
    """A membership object that associates a user with a group.

    It has attributes for `group', `user' and `membership_type',
    membership types are listed in group_membership_types table.
    """
    def __init__(self, user=None, group=None, admin=False):
        """Create a group membership object."""
        role_admin = GroupMembershipType.get('administrator')
        role_member = GroupMembershipType.get('member')
        self.user = user
        self.group = group
        self.role = role_member
        if admin:
            self.role = role_admin

    @classmethod
    def get(cls, user, group):
        try:
            return meta.Session.query(cls).filter(GroupMember.user == user).filter(GroupMember.group == group).one()
        except NoResultFound:
            return None

    @property
    def is_admin(self):
        return self.role == GroupMembershipType.get('administrator')


class GroupMembershipType(object):

    @classmethod
    def get(cls, membership_type):
        try:
            return meta.Session.query(cls).filter_by(membership_type=membership_type).one()
        except NoResultFound:
            return None


group_requests_table = None

class PendingInvitation(object):
    """The group invites a user."""
    def __init__(self, email, group = None, author=None):
        self.author = author
        self.hash = ''.join(Random().sample(string.ascii_lowercase, 8))
        if group is not None:
            self.group = group

        user = User.get(email)
        if user is not None:
            self.user = user

        self.email = email

    @classmethod
    def get(cls, hash):
        try:
            return meta.Session.query(cls).filter(cls.hash == hash).one()
        except NoResultFound:
            return None


group_invitations_table = None

class PendingRequest(object):
    """The user requests to join a group."""
    def __init__(self, user, group = None):
        self.hash = ''.join(Random().sample(string.ascii_lowercase, 8))
        if group is not None:
            self.group = group

        if user is not None:
            self.user = user

    @classmethod
    def get(cls, user, group):
        """Return a a group request matching the user and the group."""
        try:
            return meta.Session.query(PendingRequest).filter(and_(PendingRequest.user == user, PendingRequest.group == group)).one()
        except NoResultFound:
            return None


subjects_table = None
class Subject(ContentItem, FolderMixin, LimitedUploadMixin):

    def recipients(self, period):
        all_recipients = []
        groups =  meta.Session.query(Group).filter(Group.watched_subjects.contains(self)).all()
        for group in groups:
            all_recipients.extend(group.recipients(period))

        usms = meta.Session.query(UserSubjectMonitoring).\
            filter(UserSubjectMonitoring.subject==self).\
            filter(User.receive_email_each==period).all()
        recipients = [usm.user for usm in usms]
        all_recipients.extend(recipients)
        return list(set(all_recipients))

    def recipients_gg(self):
        all_recipients = []
        groups =  meta.Session.query(Group).filter(Group.watched_subjects.contains(self)).all()
        for group in groups:
            all_recipients.extend(group.recipients_gg())

        usms = meta.Session.query(UserSubjectMonitoring).\
            join(User).\
            filter(UserSubjectMonitoring.subject==self).\
            filter(User.gadugadu_get_news==True).\
            filter(User.gadugadu_confirmed==True).all()
        recipients = [usm.user for usm in usms]
        all_recipients.extend(recipients)
        return list(set(all_recipients))

    @classmethod
    def get(cls, location, id):
        try:
            return meta.Session.query(cls).filter_by(subject_id=id, location=location).one()
        except NoResultFound:
            return None

    @classmethod
    def get_by_id(cls, id):
        try:
            return meta.Session.query(cls).filter_by(id=id).one()
        except NoResultFound:
            return None

    @property
    def location_path(self):
        location = self.location
        path = []
        while location:
            path.append(location.title_short)
            location = location.parent
        return '/'.join(reversed(path))

    def url(self, controller='subject', action='home', **kwargs):
        return url(controller=controller,
                   action=action,
                   id=self.subject_id,
                   tags=self.location_path,
                   **kwargs)

    def snippet(self):
        """Render a short snippet with the basic item's information. Used in search to render the results."""
        return render_mako_def('/sections/content_snippets.mako','subject', object=self)

    def generate_new_id(self):
        title = urlify(self.title, 20)
        lecturer = urlify(self.lecturer or '', 10)

        alternative_ids = [
            '%(title)s' % dict(title=title),
            '%(title)s-%(lecturer)s' % dict(title=title, lecturer=lecturer),
            '%(title)s-%(id)i' % dict(title=title, id=self.id),
            '%(title)s-%(lecturer)s-%(id)i' % dict(title=title, lecturer=lecturer, id=self.id)]
        if self.lecturer is None or self.lecturer.strip() == u'':
            del(alternative_ids[3])
            del(alternative_ids[1])

        for sid in alternative_ids:
            exist = Subject.get(self.location, sid)
            if exist is None:
                return sid
        return None

    def __init__(self, subject_id, title, location, lecturer=None, description=None, tags=[]):
        self.location = location
        self.title = title
        self.subject_id = subject_id
        self.lecturer = lecturer
        self.description = description
        self.tags = tags

    def filtered_events(self, types=[], limit=20):
        """Return a list of events, filtered by their type, that happened to this subject."""
        from ututi.model.events import Event
        events = meta.Session.query(Event)\
            .filter(Event.object_id == self.id)

        if types != []:
            events = events.filter(Event.event_type.in_(types))

        events = events.order_by(Event.created.desc()).limit(limit).all()
        return events

    def user_count(self):
        return len([w_u for w_u in self.watching_users if not w_u.ignored])

    def group_count(self):
        return len(self.watching_groups)


pages_table = None

class Page(ContentItem):
    """Class representing user-editable wiki-like pages."""

    @classmethod
    def get(cls, id):
        try:
            return meta.Session.query(cls).filter_by(id=int(id)).one()
        except NoResultFound:
            return None

    def __init__(self, title, content):
        """The first version of a page is created automatically."""
        self.add_version(title, content)

    def add_version(self, title, content):
        version = PageVersion(title, content)
        self.versions.append(version)

    def save(self, title, content):
        if title != self.title or content != self.content:
            version = PageVersion(title, content)
            self.versions.append(version)

    @property
    def last_version(self):
        if self.versions:
            return self.versions[0]
        else:
            raise AttributeError("This page has no versions!")

    @property
    def title(self):
        return self.last_version.title

    @property
    def content(self):
        return self.last_version.content

    @property
    def author(self):
        return self.last_version.author

    @property
    def created(self):
        return self.last_version.created

    def url(self, controller='subjectpage', action='index', **kwargs):
        return url(controller=controller,
                   action=action,
                   page_id=self.id,
                   id=self.subject[0].subject_id,
                   tags=self.subject[0].location_path,
                   **kwargs)

    def snippet(self):
        """Render a short snippet with the basic item's information. Used in search to render the results."""
        return render_mako_def('/sections/content_snippets.mako','page', object=self)


page_versions_table = None

class PageVersion(ContentItem):
    """Class representing one version of a page."""

    def __init__(self, title, content):
        self.title = title
        self.content = content

    @property
    def plain_text(self):
        doc = lxml.html.fragment_fromstring(self.content, create_parent=True)
        texts = doc.xpath('//text()')
        return ' '.join(texts)

    def url(self, controller='subjectpage', action='show_version', **kwargs):
        return url(controller=controller,
                   action=action,
                   id=self.page.subject[0].subject_id,
                   tags=self.page.subject[0].location_path,
                   page_id=self.page_id,
                   version_id=self.id,
                   **kwargs)


content_tags_table = None
class Tag(object):
    """Class representing tags in general."""

    def __init__(self, title, title_short, description):
        self.title = title
        self.description = description

    @classmethod
    def get(cls, id):
        tag = meta.Session.query(cls)
        if isinstance(id, basestring):
            tag.filter_by(title=id.lower())
        else:
            tag.filter_by(id=id)
        try:
            return tag.one()
        except NoResultFound:
            return None

    logo = logo_property()


class SimpleTag(Tag):
    """Class for simple (i.e. not location or hierarchy -aware) tags."""

    def __init__(self, title):
        self.title = title.lower()

    def hierarchy(self, full=False):
        if full:
            return [self]
        else:
            return [self.title]

    @classmethod
    def get(cls, title, create=True):
        """The method queries for a matching tag, if not found, creates one."""
        try:
            tag = meta.Session.query(cls).filter_by(title=title.lower()).one()
        except NoResultFound:
            if create:
                tag = cls(title)
                meta.Session.add(tag)
            else:
                tag = None

        return tag

    def url(self, controller='search', action='index', **kwargs):
        return url(controller=controller,
                   action=action,
                   tags=self.title,
                   **kwargs)



class LocationTag(Tag):
    """Class representing the university and faculty tags."""

    def __init__(self, title, title_short, description, parent=None, confirmed=True):
        self.parent = parent
        self.title = title
        self.title_short = title_short
        self.description = description
        self.confirmed = confirmed

    @property
    def path(self):
        location = self
        path = []
        while location:
            path.append(location.title_short.lower())
            location = location.parent
        return list(reversed(path))

    def hierarchy(self, full=False):
        """Return a list of titles (or the full tags) of all the parents of the tag, including the tag itself."""
        location = self
        path = []
        while location:
            if full:
                path.append(location)
            else:
                path.append(location.title)
            location = location.parent
        return list(reversed(path))

    @Lazy
    def flatten(self):
        """Return a list of the tag's children and the tag's children's children, etc."""
        flat = [self]
        for child in self.children:
            flat.extend(child.flatten)
        return flat

    @classmethod
    def get(cls, path):

        if isinstance(path, basestring):
            path = path.split('/')

        tag = None
        for title_short in filter(bool, path):
            try:
                tag = meta.Session.query(cls)\
                    .filter(func.lower(LocationTag.title_short)==title_short.lower()).filter_by(parent=tag).one()
            except NoResultFound:
                return None
        return tag

    @classmethod
    def get_by_title(cls, title):
        """A method to return the tag either by its full title or its short title.

        A list can be passed for hierarchical traversal.
        """
        hierarchy = True
        if not isinstance(title, list):
            title = [title]
            hierarchy = False

        tag = None
        for title_full in filter(bool, title):
            try:
                q = meta.Session.query(cls).filter(func.lower(LocationTag.title)==title_full.lower())
                if hierarchy:
                    q = q.filter_by(parent=tag)
                tag =  q.one()
            except NoResultFound:
                try:
                    q = meta.Session.query(cls).filter(func.lower(LocationTag.title_short)==title_full.lower())
                    if hierarchy:
                        q = q.filter_by(parent=tag)
                    tag =  q.one()
                except NoResultFound:
                    tag = None
                    break
        return tag

    @classmethod
    def get_all(cls, title):
        items = meta.Session.query(cls).filter(or_(func.lower(LocationTag.title)==title.lower(), func.lower(LocationTag.title_short)==title.lower())).all()
        #items.extend(meta.Session.query(cls).filter_by(title_short=title).all())
        return items

    def url(self, controller='structureview', action='index', **kwargs):
        return url(controller=controller,
                   action=action,
                   path='/'.join(self.path),
                   **kwargs)

    def count(self, obj=Subject):
        if isinstance(obj, basestring):
            obj_types = {
                'subject' : Subject,
                'group' : Group,
                'file' : File,
                }
            obj = obj_types[obj.lower()]
        ids = [t.id for t in self.flatten]
        return meta.Session.query(obj).filter(obj.location_id.in_(ids)).filter(obj.deleted_on == None).count()

    @Lazy
    def stats(self):
        ids = [t.id for t in self.flatten]
        counts = meta.Session.query(ContentItem.content_type, func.count(ContentItem.id))\
            .filter(ContentItem.location_id.in_(ids))\
            .filter(ContentItem.deleted_on == None)\
            .group_by(ContentItem.content_type).all()
        res = {'subject': 0, 'group': 0, 'file': 0}
        res.update(dict(counts))

        return res

    @Lazy
    def rating(self):
        """Calculate the rating of a university."""
        stats = self.stats
        return (stats["subject"] + 1) * (stats["file"] + 1) * (stats["group"] + 1)

    def latest_groups(self):
        ids = [t.id for t in self.flatten]
        grps =  meta.Session.query(Group).filter(Group.location_id.in_(ids)).order_by(Group.created_on.desc()).limit(5).all()
        return grps


def cleanupFileName(filename):
    return filename.split('\\')[-1].split('/')[-1]


class NotifyGG(MapperExtension):

    def after_insert(self, mapper, connection, instance):
        if instance.isNullFile():
            return
        from pylons import tmpl_context as c
        from ututi.lib import gg
        recipients = []
        if isinstance(instance.parent, (Group, Subject)):
            for interested_user in instance.parent.recipients_gg():
                if interested_user is not c.user:
                    recipients.append(interested_user.gadugadu_uin)

        for uin in sorted(recipients):
            msg = _("A new file has been uploaded for the %(title)s:")
            gg.send_message(uin, msg % {
                    'title': instance.parent.title})
            msg = "%s (%s)" % (instance.title, instance.url(qualified=True))
            gg.send_message(uin, msg)


class FileDownload(object):
    """Class representing the user downloading a certain file."""

    def __init__(self, user, file):
        self.user = user
        self.file = file


class File(ContentItem):
    """Class representing user-uploaded files."""

    def can_write(self, user=None):
        can_write = False
        if isinstance(self.parent, Subject):
            can_write = check_crowds(['moderator'], context=self.parent, user=user)
        elif isinstance(self.parent, Group):
            can_write = check_crowds(['admin'], context=self.parent, user=user)
        return can_write or check_crowds(['owner'], context=self, user=user)

    def copy(self):
        """Copy the file."""
        new_file = File(self.filename, self.title,
                        mimetype=self.mimetype,
                        description=self.description,
                        md5=self.md5,
                        folder=self.folder)
        from ututi.lib.security import current_user
        new_file.created = current_user()
        return new_file

    def __init__(self, filename, title, mimetype=None, created=None,
                 description=u'', data=None, md5=None, folder=u''):
        if data is not None:
            md5_digest = hashlib.md5(data).hexdigest()
            if md5 is not None:
                assert md5 == md5_digest
            self.md5 = md5_digest
            self.filesize = len(data)

        if md5 is not None:
            self.md5 = md5

        self.filename = cleanupFileName(filename)
        self.title = cleanupFileName(title)
        if mimetype is not None:
            self.mimetype = mimetype
        if created is not None:
            self.created = created
            self.modified = created
        self.description = description
        self.folder = folder

    @classmethod
    def makeNullFile(cls, folder):
        result = cls(u"Null File", u"Null File", folder=folder)
        return result

    def isNullFile(self):
        return self.md5 == None

    def snippet(self):
        """Render a short snippet with the basic item's information. Used in search to render the results."""
        return render_mako_def('/sections/content_snippets.mako','file', object=self)

    def filepath(self):
        """Calculate the path of a file, based on its md5 checksum."""
        dir_path = [config.get('files_path')]
        segment = ''
        for c in list(self.md5):
            segment += c
            if len(segment) > 7:
                dir_path.append(segment)
                segment = ''
        if segment:
            dir_path.append(segment)

        return os.path.join(*dir_path)

    def store(self, data):
        """Store a given file in the database and the filesystem."""
        self.md5 = self.hash_chunked(data)
        filename = self.filepath()
        if os.path.exists(filename):
            return

        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
        f = open(filename, 'w')
        size = copy_chunked(data, f, 4096)
        self.filesize = size

        f.close()

    def url(self, controller='files', action='get', **kwargs):
        from ututi.model.mailing import GroupMailingListMessage

        if isinstance(self.parent, Subject):
            return self.parent.url(controller='subjectfile',
                                   action=action,
                                   file_id=self.id,
                                   **kwargs)
        elif isinstance(self.parent, Group):
            return self.parent.url(controller='groupfile',
                                   action=action,
                                   file_id=self.id,
                                   **kwargs)
        elif isinstance(self.parent, GroupMailingListMessage):
            message = self.parent
            return message.group.url(controller='mailinglist',
                                     action='file',
                                     message_id=message.id,
                                     file_id=self.id,
                                     **kwargs)
        raise AttributeError("Can't generate url for the file without a parent!")

    def hash_chunked(self, file):
        """Calculate the checksum of a file in chunks."""
        chunk_size = 8 * 1024**2
        size = 0
        hash = hashlib.md5()

        while True:
            if isinstance(file, basestring):
                chunk = file[size:(size+chunk_size)]
            else:
                chunk = file.read(chunk_size)

            size += len(chunk)
            hash.update(chunk)
            if len(chunk) < chunk_size:
                break

        if not isinstance(file, basestring):
            file.seek(0)

        return hash.hexdigest()

    @property
    def size(self):
        if self.filesize is not None:
            return self.filesize
        else:
            try:
                return os.path.getsize(self.filepath())
            except:
                return 0

    @classmethod
    def get(self, file_id):
        try:
            return meta.Session.query(File).filter_by(id=file_id).one()
        except NoResultFound:
            return None


class ForumCategory(object):
    """A collection of threads."""

    def __init__(self, title, description, group=None):
        self.title = title
        self.group = group
        self.description = description

    @staticmethod
    def get(category_id):
        try:
            return meta.Session.query(ForumCategory).filter_by(id=category_id).one()
        except NoResultFound:
            return None

    def post_count(self):
        return meta.Session.query(ForumPost
                                   ).filter_by(category_id=self.id,
                                               deleted_by=None
                                   ).count() or 0

    def poster_count(self):
        query = """select count(distinct content_items.created_by)
                       from content_items
                       join forum_posts on forum_posts.id = content_items.id
                       where category_id = %s""" % self.id
        return meta.Session.execute(query).scalar() or 0

    def topic_count(self):
        return meta.Session.query(ForumPost)\
                 .filter_by(category_id=self.id, deleted_by=None)\
                 .filter(ForumPost.thread_id == ForumPost.id)\
                 .count() or 0

    def messages(self, limit=5):
        return meta.Session.query(ForumPost
                ).filter_by(category_id=self.id, deleted_by=None
                ).filter(ForumPost.thread_id == ForumPost.id
                ).limit(limit).all()

    def top_level_messages(self):
        messages = meta.Session.query(ForumPost)\
            .filter_by(category_id=self.id, deleted_by=None)\
            .filter(ForumPost.id == ForumPost.thread_id)\
            .order_by(desc(ForumPost.created_on)).all()

        threads = []
        for message in messages:
            thread = {}

            thread['post'] = message
            thread['thread_id'] = message.thread_id
            thread['title'] = message.title

            replies = meta.Session.query(ForumPost)\
                .filter_by(thread_id=message.thread_id, deleted_by=None)\
                .order_by(ForumPost.created_on).all()

            thread['reply_count'] = len(replies) - 1
            thread['created'] = replies[-1].created_on
            thread['author'] = replies[-1].created
            threads.append(thread)

        return sorted(threads, key=lambda t: t['created'], reverse=True)


class ForumPost(ContentItem):
    """Forum post."""

    def __init__(self, title, message, category_id=None, thread_id=None):
        self.title = title
        self.message = message
        self.category_id = category_id
        self.thread_id = thread_id

    def is_thread(self):
        return self.thread_id == self.id

    def url(self, new=False):
        if self.category_id == 1:
            controller = 'community'
        elif self.category_id == 2:
            controller = 'bugs'
        else:
            controller = 'forum'

        category = ForumCategory.get(self.category_id)
        if category.group_id:
            group_id = category.group.group_id
        else:
            group_id = None
        s = url(controller=controller, action='thread',
                   id=group_id,
                   category_id=self.category_id, thread_id=self.thread_id)
        if new:
            s += '#seen'
        return s

    @staticmethod
    def get(id):
        try:
            return meta.Session.query(ForumPost
                                      ).filter_by(id=id, deleted_by=None
                                      ).one()
        except NoResultFound:
            return None

    def mark_as_seen_by(self, user):
        if user is None:
            return
        seen = SeenThread.get_or_create(self.thread_id, user)
        seen.visited_on = datetime.utcnow()
        meta.Session.commit()

    def first_unseen_thread_post(self, user):
        if user is None:
            return None
        seen = SeenThread.get_or_create(self.thread_id, user)
        posts = meta.Session.query(ForumPost
                ).filter_by(thread_id=self.thread_id,
                ).filter(ForumPost.created_on > seen.visited_on
                ).order_by(ForumPost.created_on.asc()
                ).limit(1).all()
        if posts:
            return posts[0]
        else:
            return None


seen_threads_table = None
class SeenThread(object):

    def __init__(self, thread_id, user):
        self.thread_id = thread_id
        self.user = user

    @staticmethod
    def get_or_create(thread_id, user):
        try:
            return meta.Session.query(SeenThread
                                ).filter_by(thread_id=thread_id,
                                            user=user).one()
        except NoResultFound:
            seen = SeenThread(thread_id, user)
            meta.Session.add(seen)
            meta.Session.commit()
            return seen


subscribed_threads_table = None
class SubscribedThread(object):
    """A relationship between a thread and a user indicating a subscription.

    Subscribed users will receive new posts to subscribed threads by email.

    Subscriptions may be marked inactive, which means that the user should not
    be automatically subscribed to that thread in the future.
    """

    def __init__(self, thread_id, user, active=False):
        self.thread_id = thread_id
        self.user = user
        self.active = active

    @staticmethod
    def get(thread_id, user):
        try:
            return meta.Session.query(SubscribedThread
                                ).filter_by(thread_id=thread_id,
                                            user=user).one()
        except NoResultFound:
            return None

    @staticmethod
    def get_or_create(thread_id, user, activate=False):
        """Find a subscription for a given thread.

        If an existing subscription is not found, one is created.  If `activate`
        is True and a subscription needs to be created, it is initially
        marked as active.
        """
        try:
            return meta.Session.query(SubscribedThread
                                ).filter_by(thread_id=thread_id,
                                            user=user).one()
        except NoResultFound:
            subscription = SubscribedThread(thread_id, user, active=activate)
            meta.Session.add(subscription)
            meta.Session.commit()
            return subscription


blog_table = None
class BlogEntry(object):
    pass


search_items_table = None
class SearchItem(object):
    pass

tag_search_items_table = None
class TagSearchItem(object):
    pass

payments_table = None
class Payment(object):

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, 'raw_' + key, value)

    def process(self):
        payment_type, payment_info = self.raw_orderid.split('_', 1)
        if payment_type == 'support':
            user_id = payment_info
            self.user = User.get_byid(int(user_id))
        elif payment_type == 'grouplimits':
            user_id, group_id = payment_info.split('_', 1)
            self.user = User.get_byid(int(user_id))
            self.group = Group.get(int(group_id))

        self.payment_type = payment_type
        self.amount = int(self.raw_amount)
        self.valid = True
        self.processed = True


def get_supporters():
    return sorted(list(set([payment.user for payment in
                            meta.Session.query(Payment)\
                                .filter_by(payment_type='support')])),
                  key=lambda u:u.id)

# Reimports for convenience
from ututi.model.mailing import GroupMailingListMessage

# Events:
#
#   page added/modified
#   file added
#   message added
#   subject added/modified
#   member joined, invited, left, invitation accepted

# slicing
# user -> groups (pages, files, members?, messages) + subjects (pages, files)
# group -> subjects (pages, files) + group + pages + files + members

#   conversation, comment (feedback)
