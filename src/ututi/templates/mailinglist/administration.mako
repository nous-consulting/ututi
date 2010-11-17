<%inherit file="/mailinglist/base.mako" />

<div class="back-link">
  <a class="back-link" href="${h.url_for(action='index')}">${_('Back to the topic list')}</a>
</div>

<%self:rounded_block class_="portletGroupFiles portletGroupMailingList">
  <div class="single-title">
    <div class="floatleft bigbutton2">
      <h2 class="portletTitle bold category-title">${_('Moderation queue')}</h2>
    </div>
    <div class="clear"></div>
  </div>
  %if not c.messages:
    <div class="single-messages" id="single-messages">
      <div class="no-messages">${_('No messages to be moderated yet.')}</div>
    </div>
  %else:
    <div class="single-messages" id="single-messages">
      ${self.listThreads(action='moderate_post', show_reply_count=False)}
    </div>
  %endif
</%self:rounded_block>
