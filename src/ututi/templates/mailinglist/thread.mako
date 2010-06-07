<%inherit file="/mailinglist/base.mako" />

<div class="back-link">
  <a class="back-link" href="${h.url_for(action='index')}">${_('Back to the topic list')}</a>
</div>

<h1>${c.thread.subject}</h1>

<table id="forum-thread">
% for message in c.messages:
  <tr>
    <td colspan="2" class="author">
      <a href="${message.author.url()}">${message.author.fullname}</a>
      % for medal in message.created.all_medals():
          ${medal.img_tag()}
      % endfor
      <span class="created-on">${h.fmt_dt(message.sent)}</span>
      <div style="float: right">
        ${h.button_to(_('Reply'), url(controller='mailinglist', action='thread', id=c.group.group_id, thread_id=c.thread.id) + '#reply')}
      </div>
    </td>
  </tr>

<tr class="thread-post">
  <td class="author-logo">
    <a href="${message.author.url()}">
      %if message.author.logo is not None:
        <img alt="user-logo" src="${url(controller='user', action='logo', id=message.author.id, width='45', height='60')}"/>
      %else:
        ${h.image('/images/user_logo_45x60.png', alt='logo', id='group-logo')|n}
      %endif
    </a>
  </td>
  <td class="message">
    <div class="message-content">
      <div class="post-body">
        ${h.email_with_replies(message.body)}
      </div>
      % if message.attachments:
      <ul class="post-attachments">
        % for file in message.attachments:
        <li>
          <a href="${file.url()}" class="file-link">${file.title}</a>
        </li>
        % endfor
      </ul>
      % endif
    </div>
  </td>
</tr>
% endfor
</table>

% if h.check_crowds(['member', 'admin']):
<div id="reply-section">
  <a name="reply"></a>
  <h2>${_('Reply')}</h2>
  <br />
  <form method="post" action="${url(controller='mailinglist', action='reply', thread_id=c.thread.id, id=c.group.group_id)}"
       id="group_add_form" class="fullForm" enctype="multipart/form-data">
    ${h.input_area('message', _('Message'))}
    <br />
    ${h.input_submit(_('Reply'))}
  </form>
</div>
% endif
