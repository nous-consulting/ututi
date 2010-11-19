from datetime import date
import logging
import facebook
import random

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql.expression import desc, asc, func
from formencode import htmlfill
from formencode.api import Invalid

from webhelpers import paginate

from pylons import request, tmpl_context as c, url, config, session
from pylons.templating import render_mako_def
from pylons.controllers.util import abort, redirect

from pylons.i18n import _

import ututi.lib.helpers as h
from ututi.lib.base import render
from ututi.lib.emails import email_confirmation_request
from ututi.lib.search import search_query
from ututi.lib.security import ActionProtector
from ututi.lib.image import serve_logo
from ututi.lib.forms import validate
from ututi.lib import gg, sms
from ututi.lib.validators import manual_validate

from ututi.model.events import Event
from ututi.model import get_supporters
from ututi.model import LocationTag, BlogEntry
from ututi.model import meta, Email, Group, SearchItem, User
from ututi.controllers.profile.validators import HideElementForm
from ututi.controllers.profile.validators import ContactForm, LocationForm, LogoUpload, PhoneConfirmationForm, PhoneForm, ProfileForm, PasswordChangeForm
from ututi.controllers.profile.wall import WallMixin
from ututi.controllers.profile.subjects import WatchedSubjectsMixin
from ututi.controllers.search import SearchSubmit, SearchBaseController
from ututi.controllers.home import sign_in_user
from ututi.controllers.home import UniversityListMixin

log = logging.getLogger(__name__)

class ProfileController(SearchBaseController, UniversityListMixin, WallMixin, WatchedSubjectsMixin):
    """A controller for the user's personal information and actions."""

    def __before__(self):
        c.ututi_supporters = get_supporters()
        if c.user is not None:
            c.breadcrumbs = [{'title': c.user.fullname, 'link': url(controller='profile', action='home')}]
            c.blog_entries = meta.Session.query(BlogEntry).order_by(BlogEntry.created.desc()).limit(10).all()

    def _actions(self, selected):
        """Generate a list of all possible actions.

        The action with the name matching the `selected' parameter is
        marked as selected.
        """
        bcs = {
            'home':
            {'title': _("What's New?"),
             'link': url(controller='profile', action='home')},
            'subjects':
            {'title': _("Subjects"),
             'link': url(controller='profile', action='subjects')}
            }
        if selected in bcs.keys():
            return bcs[selected]

    @ActionProtector("user")
    def browse(self):
        c.breadcrumbs = [{'title': _('Search'), 'link': url(controller='profile', action='browse')}]
        self._get_unis()

        c.obj_type = '*'
        if request.params.has_key('js'):
            return render_mako_def('/anonymous_index/lt.mako', 'universities',
                                   unis=c.unis, ajax_url=url(controller='profile', action='browse'))

        return render('/profile/browse.mako')

    @ActionProtector("user")
    @validate(schema=SearchSubmit, form='index', post_only=False, on_get=True)
    def search(self):
        c.breadcrumbs = [{'title': _('Search'), 'link': url(controller='profile', action='browse')}]
        self._search()
        self._search_locations(self.form_result.get('text', ''))
        return render('/profile/search.mako')

    @ActionProtector("user")
    @validate(schema=SearchSubmit, form='index', post_only=False, on_get=True)
    def search_js(self):
        self._search()
        return render_mako_def('/search/index.mako','search_results', results=c.results, controller='profile', action='search')

    @ActionProtector("user")
    def index(self):
        c.events = meta.Session.query(Event)\
            .filter(Event.author_id == c.user.id)\
            .order_by(desc(Event.created))\
            .limit(20).all()

        c.fullname = c.user.fullname
        c.emails = [email.email for email in
                    meta.Session.query(Email).filter_by(id=c.user.id).filter_by(confirmed=False).all()]
        c.emails_confirmed = [email.email for email in
                              meta.Session.query(Email).filter_by(id=c.user.id).filter_by(confirmed=True).all()]
        return render('profile/profile.mako')

    @ActionProtector("user")
    def home(self):
        c.breadcrumbs.append(self._actions('home'))
        c.action = 'home'

        return render('/profile/home.mako')

    def _edit_form(self, defaults=None):
        return render('profile/edit.mako')

    def _edit_form_defaults(self):
        defaults = {
            'email': c.user.emails[0].email,
            'gadugadu_uin': c.user.gadugadu_uin,
            'gadugadu_get_news': c.user.gadugadu_get_news,
            'phone_number': c.user.phone_number,
            'fullname': c.user.fullname,
            'site_url': c.user.site_url,
            'description': c.user.description,
            'profile_is_public': c.user.profile_is_public,
            }
        if c.user.location is not None:
            location = dict([('location-%d' % n, tag)
                             for n, tag in enumerate(c.user.location.hierarchy())])
        else:
            location = []
        defaults.update(location)

        return defaults

    @ActionProtector("user")
    def edit(self):
        return htmlfill.render(self._edit_form(),
                               defaults=self._edit_form_defaults())

    @ActionProtector("user")
    def link_google(self):
        session['linking_to_user'] = c.user.id
        session.save()
        redirect(url(controller='federation', action='google_register'))

    @ActionProtector("user")
    def unlink_google(self):
        c.user.openid = None
        meta.Session.commit()
        h.flash(_('Your Google account has been unlinked.'))
        redirect(url(controller='profile', action='edit'))

    @ActionProtector("user")
    def link_facebook(self):
        fb_user = facebook.get_user_from_cookie(request.cookies,
                         config['facebook.appid'], config['facebook.secret'])
        if not fb_user:
            h.flash(_("Failed to link Facebook account"))
        else:
            facebook_id = int(fb_user['uid'])
            if not User.get_byfbid(facebook_id):
                c.user.facebook_id = facebook_id
                c.user.update_logo_from_facebook()
                meta.Session.commit()
                h.flash(_("Linked to Facebook account."))
            else:
                h.flash(_('This Facebook account is already linked to another Ututi account.'))
        redirect(url(controller='profile', action='edit'))

    @ActionProtector("user")
    def unlink_facebook(self):
        c.user.facebook_id = None
        meta.Session.commit()
        h.flash(_('Your Facebook account has been unlinked.'))
        redirect(url(controller='profile', action='edit'))

    @validate(PasswordChangeForm, form='_edit_form',
              ignore_request=True, defaults=_edit_form_defaults)
    @ActionProtector("user")
    def password(self):
        if hasattr(self, 'form_result'):
            c.user.update_password(self.form_result['new_password'].encode('utf-8'))
            meta.Session.commit()
            h.flash(_('Your password has been changed!'))
            redirect(url(controller='profile', action='home'))
        else:
            redirect(url(controller='profile', action='edit'))

    @validate(LogoUpload)
    @ActionProtector("user")
    def logo_upload(self):
        if self.form_result['logo'] is not None:
            logo = self.form_result['logo']
            c.user.logo = logo.file.read()
            meta.Session.commit()
            return ''

    @validate(ProfileForm, form='_edit_form', defaults=_edit_form_defaults)
    @ActionProtector("user")
    def update(self):
        fields = ('fullname', 'logo_upload', 'logo_delete', 'site_url',
                  'description', 'profile_is_public', 'location')
        values = {}
        for field in fields:
            values[field] = self.form_result.get(field, None)

        c.user.fullname = values['fullname']
        c.user.site_url = values['site_url']
        c.user.description = values['description']
        tag = values.get('location', None)
        c.user.profile_is_public = bool(values['profile_is_public'])
        c.user.location = tag

        if values['logo_delete'] == 'delete' and c.user.logo is not None:
            c.user.logo = None

        if values['logo_upload'] is not None and values['logo_upload'] != '':
            logo = values['logo_upload']
            c.user.logo = logo.file.read()

        meta.Session.commit()
        h.flash(_('Your profile was updated.'))
        redirect(url(controller='profile', action='home'))

    def confirm_emails(self):
        if c.user is not None:
            emails = request.POST.getall('email')
            for email in emails:
                email_confirmation_request(c.user, email)
            h.flash(_('Confirmation message sent. Please check your email.'))
            dest = request.POST.get('came_from', None)
            if dest is not None:
                redirect(dest.encode('utf-8'))
            else:
                redirect(url(controller='profile', action='edit'))
        else:
            redirect(url(controller='home', action='home'))

    def confirm_user_email(self, key):
        try:
            email = meta.Session.query(Email).filter_by(confirmation_key=key).one()
            email.confirmed = True
            email.confirmation_key = ''
            meta.Session.commit()
            h.flash(_("Your email %s has been confirmed, thanks." % email.email))
        except NoResultFound:
            h.flash(_("Could not confirm email: invalid confirmation key."))

        redirect(url(controller='profile', action='home'))

    @ActionProtector("user")
    def register_welcome(self):
        if request.params.get('fb'):
            FB_POST_MESSAGES = [_('I like it'),
                                _('I joined too ;)'),
                                _('Nice tool for students.'),
                                _('Maybe You will also find it useful'),
                                _('I found my University on Ututi ;)'),
                                _('Where are your notes?')]
            c.fb_random_post = random.choice(FB_POST_MESSAGES)

        return render('profile/home.mako')

    @validate(schema=SearchSubmit, form='test', post_only = False, on_get = True)
    @ActionProtector("user")
    def findgroup(self):
        """Find the requested group, filtering by location id and year."""
        #collect default search parameters
        c.text = self.form_result.get('text', '')

        tags = []

        if 'tagsitem' in self.form_result:
            tags = self.form_result.get('tagsitem', None)
        elif 'tags' in self.form_result:
            tags = self.form_result.get('tags', [])
            if isinstance(tags, basestring):
                tags = tags.split(', ')
        elif c.user.location is not None:
            tags = c.user.location.hierarchy()

        c.tags = tags

        c.tags.extend(self.form_result.get('location', []))
        c.tags = filter(bool, c.tags)

        #keep location information for group creation view
        c.location = LocationTag.get_by_title(filter(bool, self.form_result.get('location', [])))
        if c.location is not None:
            c.location = '/'.join(c.location.path)

        #extra search parameters
        c.year = self.form_result.get('year', None)

        search_params = {}
        if c.text:
            search_params['text'] = c.text
        if c.tags:
            search_params['tags'] = c.tags
        else:
            search_params['tags'] = []

        search_params['obj_type'] = 'group'

        if search_params != {}:
            results = search_query(**search_params)

            if c.year is not None:
                try:
                    c.year = int(c.year)
                    search_params['year'] = c.year
                    results = results.join((Group, SearchItem.content_item_id == Group.id))\
                        .order_by(asc(func.abs(Group.year - date(int(c.year), 1, 1))))

                except:
                    pass

        c.year = c.year and int(c.year) or date.today().year
        c.years = range(date.today().year - 10, date.today().year + 5)
        c.tags = ', '.join(c.tags)

        # XXX OMG WTF PYLONS URL_FOR!
        # url_for can't encode unicode parameters itself
        # as it is used by paginate.Page we must do that for it
        # weird, because url manages to accomplish this task pretty easily
        search_params['tags'] = [tag.encode('utf-8')
                                 for tag in search_params['tags']]
        c.results = paginate.Page(
            results,
            page=int(request.params.get('page', 1)),
            item_count = results.count() or 0,
            items_per_page = 10,
            **search_params)

        return render('profile/findgroup.mako')

    @ActionProtector("user")
    def logo(self, width=None, height=None):
        return serve_logo('user', c.user.id, width=width, height=height,
                default_img_path="public/images/user_ico.png")

    @ActionProtector("user")
    def set_receive_email_each(self):
        if request.params.get('each') in ('day', 'hour', 'never'):
            c.user.receive_email_each = request.params.get('each')
            meta.Session.commit()
        if request.params.get('ajax'):
            return 'OK'
        redirect(url(controller='profile', action='subjects'))

    @validate(ContactForm, form='_edit_form', defaults=_edit_form_defaults)
    @ActionProtector("user")
    def update_contacts(self):
        if hasattr(self, 'form_result'):
            if self.form_result['confirm_email']:
                h.flash(_('Confirmation message sent. Please check your email.'))
                email_confirmation_request(c.user, c.user.emails[0].email)
                redirect(url(controller='profile', action='edit'))

            # handle email
            email = self.form_result['email']
            if email != c.user.emails[0].email:
                c.user.emails[0].email = email
                c.user.emails[0].confirmed = False
                email_confirmation_request(c.user, email)
                meta.Session.commit()
                sign_in_user(email)

            # handle GG
            gadugadu_uin = self.form_result['gadugadu_uin']
            gadugadu_confirmation_key = self.form_result['gadugadu_confirmation_key']

            if self.form_result['resend_gadugadu_code']:
                gg.confirmation_request(c.user)
                meta.Session.commit()
            elif gadugadu_uin != c.user.gadugadu_uin:
                c.user.gadugadu_uin = gadugadu_uin
                c.user.gadugadu_confirmed = False
                c.user.gadugadu_get_news = False
                if gadugadu_uin:
                    gg.confirmation_request(c.user)
                meta.Session.commit()
            elif gadugadu_confirmation_key:
                c.user.gadugadu_confirmed = True
                meta.Session.commit()
            else:
                c.user.gadugadu_get_news = self.form_result['gadugadu_get_news']
                meta.Session.commit()

            # handle phone number
            phone_number = self.form_result['phone_number']
            phone_confirmation_key = self.form_result['phone_confirmation_key']

            if self.form_result['resend_phone_code']:
                sms.confirmation_request(c.user)
                meta.Session.commit()
            elif phone_number != c.user.phone_number:
                c.user.phone_number = phone_number
                c.user.phone_confirmed = False
                if phone_number:
                    sms.confirmation_request(c.user)
                meta.Session.commit()
            elif phone_confirmation_key:
                c.user.confirm_phone_number()
                meta.Session.commit()

        redirect(url(controller='profile', action='edit'))

    @ActionProtector("user")
    def thank_you(self):
        return render('/profile/thank_you.mako')

    @ActionProtector("user")
    def no_thank_you(self):
        return render('/profile/no_thank_you.mako')

    def support(self):
        if not c.user:
            redirect(url(controller='home',
                         action='login',
                         came_from=url(controller='profile', action='support'),
                         context_type='support'))
        return render('/profile/support.mako')

    @ActionProtector("user")
    @validate(schema=LocationForm, form='home')
    def update_location(self):
        c.user.location = self.form_result.get('location', None)
        meta.Session.commit()
        h.flash(_('Your university information has been updated.'))
        redirect(url(controller='profile', action='home'))

    @ActionProtector("user")
    def js_update_location(self):
        try:
            fields = manual_validate(LocationForm)
            c.user.location = fields.get('location', None)
            meta.Session.commit()
            return render_mako_def('/profile/home.mako', 'location_updated')
        except Invalid, e:
            abort(400)

    @ActionProtector("user")
    @validate(schema=PhoneForm, form='home')
    def update_phone(self):
        c.user.location = self.form_result.get('phone_number', None)
        meta.Session.commit()
        h.flash(_('Your phone number has been updated.'))
        redirect(url(controller='profile', action='home'))

    @ActionProtector("user")
    def js_update_phone(self):
        try:
            fields = manual_validate(PhoneForm)
            c.user.phone_number = fields.get('phone_number', None)
            c.user.phone_confirmed = False
            if c.user.phone_number:
                sms.confirmation_request(c.user)
            meta.Session.commit()
            return render_mako_def('/profile/home.mako', 'phone_updated')
        except Invalid, e:
            return ''

    @ActionProtector("user")
    @validate(schema=PhoneConfirmationForm, form='home')
    def confirm_phone(self):
        c.user.location = self.form_result.get('phone_confirmation_key', None)
        meta.Session.commit()
        h.flash(_('Your phone number has been confirmed.'))
        redirect(url(controller='profile', action='home'))

    @ActionProtector("user")
    def js_confirm_phone(self):
        key = request.params.get('phone_confirmation_key')
        if key.strip() != c.user.phone_confirmation_key.strip():
            return ''
        c.user.confirm_phone_number()
        meta.Session.commit()
        return render_mako_def('/profile/home.mako', 'phone_confirmed')

    @ActionProtector("user")
    @validate(schema=LocationForm, form='home')
    def goto_location(self):
        if hasattr(self, 'form_result'):
            location = self.form_result.get('location', None)
            if location is not None:
                redirect(location.url())
        redirect(url(controller='profile', action='home'))

    @ActionProtector("user")
    @validate(schema=HideElementForm)
    def js_hide_element(self):
        if hasattr(self, 'form_result') and self.form_result['type'] not in c.user.hidden_blocks.split(' '):
            c.user.hidden_blocks = "%s %s" % (c.user.hidden_blocks, self.form_result['type'])
            meta.Session.commit()

    @ActionProtector("root")
    def session_info(self):
        """ Display session values for testing purposes. """
        ret = ""
        items = session.items()
        items.sort()
        for key, value in items:
            ret += "%s => %s\n" % (key, value)
        return ret

    @ActionProtector("user")
    def set_location(self):
        location_id = request.params.get('location_id')
        c.user.location_id = location_id
        meta.Session.commit()
        location = meta.Session.query(LocationTag).filter_by(id=location_id).one()
        redirect(url(controller='structureview', action='index', path='/'.join(location.path)))
