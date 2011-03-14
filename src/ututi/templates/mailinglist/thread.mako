<%inherit file="/mailinglist/base.mako" />

<div class="back-link">
  <a class="back-link" href="${h.url_for(action='index')}">${_('Back to the topic list')}</a>
</div>


<%self:rounded_block class_="portletGroupFiles portletMailingListThread smallTopMargin">
<div class="single-title">
  <div class="floatleft bigbutton2">
    <h2 class="portletTitle bold category-title">${c.thread.subject}</h2>
  </div>
  <div class="clear"></div>
</div>

<table id="forum-thread">
% for message in c.messages:
  ${self.render_message(message)}
% endfor
</table>

% if h.check_crowds(['member', 'admin']):
<div id="reply-section">
  <a name="reply"></a>
  <h2>${_('Reply')}</h2>
  <form method="post" action="${url(controller='mailinglist', action='reply', thread_id=c.thread.id, id=c.group.group_id)}"
       id="group_add_form" class="fullForm" enctype="multipart/form-data">
    ${h.input_area('message', _('Message'))}
    ${h.input_submit(_('Reply'))}
  </form>
</div>
% endif
</%self:rounded_block>