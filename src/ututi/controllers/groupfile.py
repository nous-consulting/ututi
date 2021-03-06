import logging

from sqlalchemy.orm.exc import NoResultFound
from pylons.controllers.util import abort
from pylons import tmpl_context as c, url

from ututi.controllers.files import BasefilesController
from ututi.model import Group, File, meta

from ututi.lib.security import ActionProtector

from pylons.i18n import _

log = logging.getLogger(__name__)


def set_login_url(method):
    def _set_login_url(self, group, file):
        c.login_form_url = url(controller='home',
                               action='login',
                               came_from=group.url(action='files',
                                                   serve_file=file.id),
                               context=file.filename)
        return method(self, group, file)
    return _set_login_url


def group_file_action(method):
    def _group_action(self, id, file_id):
        group = Group.get(id)
        if group is None:
            abort(404)

        file = File.get(file_id)
        if file not in group.files:
            abort(404)

        c.security_context = file
        c.object_location = group.location
        c.group = group
        c.breadcrumbs = [{'title': group.title, 'link': group.url()}]
        return method(self, group, file)
    return _group_action


class GroupfileController(BasefilesController):

    @group_file_action
    @set_login_url
    @ActionProtector('member', 'admin')
    def get(self, group, file):
        return self._get(file)

    @group_file_action
    @ActionProtector('admin', 'owner')
    def delete(self, group, file):
        return self._delete(file)

    @group_file_action
    @ActionProtector('admin', 'owner')
    def rename(self, group, file):
        return self._rename(file)

    @group_file_action
    @ActionProtector('deleter', 'owner')
    def restore(self, group, file):
        return self._restore(file)

    @group_file_action
    @ActionProtector('member', 'admin')
    def move(self, group, file):
        return self._move(group, file)

    @group_file_action
    @ActionProtector('member', 'admin')
    def copy(self, group, file):
        return self._copy(group, file)
