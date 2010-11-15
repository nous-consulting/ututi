import logging

from pylons import request

from ututi.lib.base import BaseController
from ututi.model import Group
from ututi.model import GroupMailingListMessage
from ututi.model import File
from ututi.model import meta
from ututi.model.mailing import MessageAlreadyExists

log = logging.getLogger(__name__)


class ReceivemailController(BaseController):

    def __before__(self):
        self.message_queue = []

    def _queueMessage(self, message):
        self.message_queue.append(message)

    def _sendQueuedMessages(self):
        for message in self.message_queue:
            message.send(self._recipients(message.group))

    def _recipients(self, group):
        recipients = []
        for member in group.members:
            if not member.subscribed:
                continue
            for email in member.user.emails:
                if email.confirmed:
                    recipients.append(email.email)
                    break
        return recipients

    def index(self):
        md5_list = request.POST.getall("md5[]")
        mime_type_list = request.POST.getall("mime-type[]")
        file_name_list = request.POST.getall("filename[]")

        message_text = request.str_POST['Mail']
        try:
            message = GroupMailingListMessage.fromMessageText(message_text)
        except MessageAlreadyExists:
            return "Ok!"

        if message is None:
            return "Silent bounce!"

        if message.author is None:
            return "Silent bounce!"

        if message.group_id is None:
            return "Silent bounce!"

        meta.Session.execute("SET ututi.active_user TO %d" % message.author.id)
        request.environ['repoze.who.identity'] = message.author.id

        meta.Session.add(message)

        group = Group.get(message.group_id)
        if not group.is_member(message.author):
            if group.mailinglist_moderated:
                message.in_moderation_queue = True
            else:
                return "Silent bounce!"

        meta.Session.commit() # to keep message and attachment ids stable
        attachments = []
        for md5, mimetype, filename in zip(md5_list,
                                           mime_type_list,
                                           file_name_list):

            # XXX we are not filtering nonsense files like small
            # images, pgp signatures, vcards and html bodies yet.
            f = File(filename,
                     filename,
                     mimetype=mimetype,
                     md5=md5)
            f.parent = message
            meta.Session.add(f)
            attachments.append(f)
            meta.Session.commit() # to keep attachment ids stable

        message.attachments.extend(attachments)

        if not message.in_moderation_queue:
            # only send emails for messages that don't have to be
            # moderated first
            self._queueMessage(message)

        meta.Session.commit()
        # Only send actual emails if commit succeeds
        self._sendQueuedMessages()
        return "Ok!"
