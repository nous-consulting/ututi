import logging

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql.expression import literal_column
from sqlalchemy.sql.expression import or_, and_
from pylons.controllers.util import abort, redirect
from pylons import tmpl_context as c, request, url

from pylons.i18n import _

from ututi.lib.forms import validate

from ututi.controllers.home import sign_in_user

from ututi.lib.security import ActionProtector, deny
from ututi.lib.image import serve_logo
from ututi.lib.base import BaseController, render
from ututi.lib.wall import WallMixin

from ututi.model import meta, User, Medal, LocationTag, TeacherBlogPost, TeacherBlogComment

from ututi.controllers.profile.validators import BlogPostCommentForm, BlogPostCommentDeleteForm

log = logging.getLogger(__name__)

def find_user(id):
    """Get's user object by specified id or url_name."""
    try:
        id = int(id)
        return User.get_byid(id)
    except ValueError:
        # it may be url_name then
        return meta.Session.query(User).filter_by(url_name=id).first()

def profile_action(method):
    def _profile_action(self, id):
        user = find_user(id)

        if user is None:
            abort(404)

        if not user.profile_is_public and not c.user:
            deny(_('This user profile is not public'), 401)

        c.user_info = user
        c.theme = user.location.get_theme()

        return method(self, user)
    return _profile_action


def teacher_profile_action(method):
    def _profile_action(self, id):
        user = find_user(id)

        if user is None or not user.is_teacher:
            abort(404)

        if not user.profile_is_public and not c.user:
            deny(_('This user profile is not public'), 401)

        c.teacher = user
        c.tabs = teacher_tabs(user)
        c.theme = user.location.get_theme()

        return method(self, user)
    return _profile_action


def teacher_blog_post_action(method):
    def _blog_post_action(self, id, post_id):
        user = find_user(id)
        if user is None or not user.is_teacher:
            abort(404)

        post = meta.Session.query(TeacherBlogPost).filter_by(id=post_id, created=user).one()
        if not post:
            abort(404)

        if not user.profile_is_public and not c.user:
            deny(_('This user profile is not public'), 401)

        c.teacher = user
        c.tabs = teacher_tabs(user)
        c.current_tab = 'blog'
        c.theme = user.location.get_theme()
        return method(self, user, post)
    return _blog_post_action


def external_teacher_profile_action(method):
    def _profile_action(self, path, id):
        location = LocationTag.get(path)
        user = find_user(id)

        if user is None or not user.is_teacher or user.location != location:
            abort(404)

        if not user.profile_is_public and not c.user:
            deny(_('This user profile is not public'), 401)

        c.teacher = user
        c.location = user.location
        c.tabs = external_teacher_tabs(user)
        c.theme = None

        return method(self, user)
    return _profile_action


def external_teacher_blog_post_action(method):
    def _profile_action(self, path, id, post_id):
        location = LocationTag.get(path)
        user = find_user(id)

        if user is None or not user.is_teacher or user.location != location:
            abort(404)

        if not user.profile_is_public and not c.user:
            deny(_('This user profile is not public'), 401)

        post = meta.Session.query(TeacherBlogPost).filter_by(id=post_id, created=user).one()
        if not post:
            abort(404)

        c.teacher = user
        c.location = user.location
        c.tabs = external_teacher_tabs(user)
        c.current_tab = 'blog'
        c.theme = None

        return method(self, user, post)
    return _profile_action


def teacher_tabs(teacher):
    tabs = [
        {'title': _('General'),
         'name': 'information',
         'link': teacher.url(action='teacher_index')},
    ]
    if teacher.blog_posts:
        tabs.append({
            'title': _('Blog'),
            'name': 'blog',
            'link': teacher.url(action='teacher_blog_index')})
    if teacher.publications:
        tabs.append({
            'title': _('Publications'),
            'name': 'publications',
            'link': teacher.url(action='teacher_publications')})
    if teacher.taught_subjects:
        tabs.append({
            'title': _('Teaching'),
            'name': 'subjects',
            'link': teacher.url(action='teacher_subjects')})
    tabs.append({
        'title': _("Activity"),
        'name': 'feed',
        'link': teacher.url(action='teacher_activity')})

    return tabs

def external_teacher_tabs(teacher):
    tabs = [
        {'title': _('General'),
         'name': 'information',
         'link': teacher.url(action='external_teacher_index')},
    ]
    if teacher.blog_posts:
        tabs.append({
            'title': _('Blog'),
            'name': 'blog',
            'link': teacher.url(action='external_teacher_blog_index')})
    if teacher.publications:
        tabs.append({
            'title': _('Publications'),
            'name': 'publications',
            'link': teacher.url(action='external_teacher_publications')})
    if teacher.taught_subjects:
        tabs.append({
            'title': _('Teaching'),
            'name': 'subjects',
            'link': teacher.url(action='external_teacher_subjects')})

    return tabs


class UserInfoWallMixin(WallMixin):

    def _wall_events_query(self):
        """WallMixin implementation."""
        public_event_types = [
            'group_created',
            'subject_created',
            'subject_modified',
            'page_created',
            'page_modified',
        ]
        from ututi.lib.wall import generic_events_query
        t_evt = meta.metadata.tables['events']
        evts_generic = generic_events_query()

        if hasattr(c, 'teacher'):
            user_id = c.teacher.id
        else:
            user_id = c.user_info.id

        query = evts_generic\
            .where(t_evt.c.author_id == user_id)

        # XXX using literal_column, this is because I don't know how
        # to refer to the column in the query directly
        query = query.where(or_(t_evt.c.event_type.in_(public_event_types),
                                and_(t_evt.c.event_type == 'file_uploaded',
                                     literal_column('context_ci.content_type') == 'subject')))

        return query


class UserController(BaseController, UserInfoWallMixin):

    @profile_action
    def index(self, user):
        self._set_wall_variables(events_hidable=False)
        return render('user/index.mako')

    @teacher_profile_action
    def teacher_index(self, user):
        if c.user is None:
            redirect(user.url(action='external_teacher_index'))
        c.current_tab = 'information'
        return render('user/teacher_information.mako')

    @teacher_profile_action
    def teacher_subjects(self, user):
        if c.user is None:
            redirect(user.url(action='external_teacher_subjects'))
        c.current_tab = 'subjects'
        return render('user/teacher_subjects.mako')

    @teacher_profile_action
    def teacher_publications(self, user):
        if c.user is None:
            redirect(user.url(action='external_teacher_publications'))
        c.current_tab = 'publications'
        return render('user/teacher_publications.mako')

    @teacher_profile_action
    def teacher_blog_index(self, user):
        c.current_tab = 'blog'
        c.blog_posts = user.blog_posts
        return render('user/teacher_blog_index.mako')

    @external_teacher_profile_action
    def external_teacher_blog_index(self, user):
        c.current_tab = 'blog'
        c.blog_posts = user.blog_posts
        return render('user/external/teacher_blog_index.mako')

    @external_teacher_blog_post_action
    def external_teacher_blog_post(self, user, post):
        c.blog_post = post
        return render('user/external/teacher_blog_post.mako')

    @teacher_blog_post_action
    def teacher_blog_post(self, user, post):
        c.blog_post = post
        return render('user/teacher_blog_post.mako')

    @validate(schema=BlogPostCommentForm())
    @teacher_blog_post_action
    @ActionProtector("user")
    def teacher_blog_comment(self, user, post):
        comment = TeacherBlogComment(post=post,
                                     content=self.form_result['content'])
        meta.Session.add(comment)
        meta.Session.commit()
        return redirect(post.url())

    @validate(schema=BlogPostCommentDeleteForm())
    @teacher_blog_post_action
    @ActionProtector("user")
    def teacher_delete_blog_comment(self, user, post):
        if hasattr(self, 'form_result') and self.form_result.get('comment_id'):
            comment = meta.Session.query(TeacherBlogComment).filter_by(id=self.form_result.get('comment_id'), post_id=post.id).one()
            if comment and (c.user.id == comment.created.id or c.user.id == post.created.id):
                meta.Session.delete(comment)
                meta.Session.commit()
        return redirect(request.referrer)

    @teacher_profile_action
    @ActionProtector("user")
    def teacher_activity(self, user):
        self._set_wall_variables(events_hidable=False)
        c.current_tab = 'feed'
        return render('user/teacher_activity.mako')

    @external_teacher_profile_action
    def external_teacher_index(self, user):
        c.current_tab = 'information'
        return render('user/external/teacher_information.mako')

    @external_teacher_profile_action
    def external_teacher_subjects(self, user):
        c.current_tab = 'subjects'
        return render('user/external/teacher_subjects.mako')

    @external_teacher_profile_action
    def external_teacher_publications(self, user):
        c.current_tab = 'publications'
        return render('user/external/teacher_publications.mako')

    @profile_action
    @ActionProtector("root")
    def login_as(self, user):
        sign_in_user(user)
        redirect(url(controller='profile', action='home'))

    @profile_action
    @ActionProtector("root")
    def medals(self, user):
        c.available_medals = [Medal(None, m[0])
                              for m in Medal.available_medals()]
        return render('user/medals.mako')

    @profile_action
    @ActionProtector("root")
    def award_medal(self, user):
        try:
            medal_type = request.GET['medal_type']
        except KeyError:
            abort(404)
        if medal_type not in Medal.available_medal_types():
            abort(404)
        if medal_type in [m.medal_type for m in user.medals]:
            redirect(url.current(action='medals')) # Medal already granted.
        m = Medal(user, medal_type)
        meta.Session.add(m)
        meta.Session.commit()
        redirect(url.current(action='medals'))

    @profile_action
    @ActionProtector("root")
    def take_away_medal(self, user):
        try:
            medal_id = int(request.GET['medal_id'])
        except KeyError:
            abort(404)
        try:
            medal = meta.Session.query(Medal).filter_by(id=medal_id).one()
        except NoResultFound:
            redirect(url.current(action='medals')) # Medal has been already taken away.
        if medal.user is not user:
            abort(404)
        meta.Session.delete(medal)
        meta.Session.commit()
        redirect(url.current(action='medals'))

    def logo(self, id, width=None, height=None):
        user = find_user(id)
        if user is None:
            abort(404)

        if user.is_teacher:
            img_path = 'public/img/teacher_default.png'
        else:
            img_path = 'public/img/user_default.png'

        return serve_logo('user', user.id, width=width, square=True,
                          default_img_path=img_path, cache=False)
