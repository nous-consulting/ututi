<%namespace name="base" file="/prebase.mako" import="rounded_block"/>
<%namespace file="/widgets/sms.mako" import="sms_widget"/>
<%namespace name="moderation" file="/mailinglist/administration.mako" />

<%def name="head_tags()">
  ${h.javascript_link('/javascript/jquery.jtruncate.pack.js')}
  ${h.javascript_link('/javascript/wall.js')}
  <script type="text/javascript">
    $(document).ready(function(){
      $('span.truncated').jTruncate({
          length: 150,
          minTrail: 50,
          moreText: "${_('More')}",
          lessText: "",
          moreAni: 300,
          lessAni: 200});
    });
  </script>
  ${h.javascript_link('/javascript/mailinglist.js')}
  ${h.javascript_link('/javascript/moderation.js')}
</%def>

<%def name="wall_item(event)">
<div class="wall_item click2show ${caller.classes()} type_${event.event_type}" id="wallevent-${event.id}">
  %if c.user is not None:
  <div class="hide_me">
    <form method="POST" action="${url(controller='profile', action='hide_event')}">
      <div>
        <input type="hidden" name="event_type" value="${event.event_type}" class="event_type"/>
        <input type="image" src="/images/details/icon_delete.png" title="${_('Ignore events like this')}" class="hide_event"/>
      </div>
    </form>
  </div>
  %endif
  <div class="description">
    ${caller.body()}
  </div>
  %if hasattr(caller, "content"):
    <div class="content">
      ${caller.content()}
    </div>
  %endif
  <div class="event_time">
    ${caller.when()}
    %if hasattr(caller, "action_link"):
      <a href='#' class="click hide action_link">
        ${caller.action_link()}
      </a>
    %endif
  </div>
  %if hasattr(caller, "action"):
    <div class="action show">
      ${caller.action()}
    </div>
  %endif
</div>
</%def>

<%def name="file_uploaded_subject(event)">
  <%self:wall_item event="${event}">
    <%def name="classes()">file_uploaded subject_event</%def>
    <%def name="content()">
      <div class="file_link">
        ${h.object_link(event.file)}
      </div>
    </%def>
    <%def name="when()">${event.when()}</%def>
    ${_("%(user_link)s has uploaded a new file in the subject %(subject_link)s.") % \
       dict(user_link=h.object_link(event.user),
            subject_link=h.object_link(event.file.parent)) | n}
  </%self:wall_item>
</%def>

<%def name="folder_created_subject(event)">
  <%self:wall_item event="${event}">
    <%def name="classes()">folder_created subject_event</%def>
    <%def name="when()">${event.when()}</%def>
    ${_("%(user_link)s has created a new folder %(folder_name)s in the subject %(subject_link)s.") % \
       dict(user_link=h.object_link(event.user),
            folder_name=event.file.folder,
            subject_link=h.object_link(event.file.parent)) | n}
  </%self:wall_item>
</%def>

<%def name="file_uploaded_group(event)">
  <%self:wall_item event="${event}">
    <%def name="classes()">file_uploaded group_event</%def>
    <%def name="content()">
      <div class="file_link">
        ${h.object_link(event.file)}
      </div>
    </%def>
    <%def name="when()">${event.when()}</%def>
    ${_("%(user_link)s has uploaded a new file in the group %(group_link)s.") % \
       dict(user_link=h.object_link(event.user),
            group_link=h.object_link(event.file.parent)) | n}
  </%self:wall_item>
</%def>

<%def name="folder_created_group(event)">
  <%self:wall_item event="${event}">
    <%def name="classes()">folder_created group_event</%def>
    <%def name="when()">${event.when()}</%def>
    ${_("%(user_link)s has created a new folder %(folder_name)s in the group %(group_link)s.") % \
       dict(user_link=h.object_link(event.user),
            folder_name=event.file.folder,
            group_link=h.object_link(event.file.parent)) | n}
  </%self:wall_item>
</%def>

<%def name="subject_modified(event)">
  <%self:wall_item event="${event}">
    <%def name="classes()">subject_event subject_modified</%def>
    <%def name="when()">${event.when()}</%def>
    ${_("%(user_link)s has edited the subject %(subject_link)s.") % \
       dict(user_link=h.object_link(event.user),
            subject_link=h.object_link(event.context)) | n}
  </%self:wall_item>
</%def>

<%def name="subject_created(event)">
  <%self:wall_item event="${event}">
    <%def name="classes()">subject_event subject_created</%def>
    <%def name="when()">${event.when()}</%def>
    ${_("%(user_link)s has created the subject %(subject_link)s.") % \
       dict(user_link=h.object_link(event.user),
            subject_link=h.object_link(event.context)) | n}
  </%self:wall_item>
</%def>

<%def name="group_created(event)">
  <%self:wall_item event="${event}">
    <%def name="classes()">group_event group_created</%def>
    <%def name="when()">${event.when()}</%def>
    ${_("%(user_link)s has created the group %(subject_link)s.") % \
       dict(user_link=h.object_link(event.user),
            subject_link=h.object_link(event.context)) | n}
  </%self:wall_item>
</%def>

<%def name="mailinglistpost_created(event)">
  <%self:wall_item event="${event}">
    <%def name="classes()">
      %if event.user is not None and event.user.is_teacher:
        teacher_event
      %else:
        message_event
      %endif
      mailinglistpost_created
    </%def>
    <%def name="content()">
      <span class="truncated">${h.email_with_replies(event.message.body, True)}</span>
    </%def>
    <%def name="when()">${event.when()}</%def>
    <%def name="action_link()">${_('Reply')}</%def>
    <%def name="action()">
      <%base:rounded_block>
      <form method="post" action="${url(controller='mailinglist', action='reply', thread_id=event.message.thread.id, id=event.context.group_id)}"
            id="mail_reply_form" class="wallForm">
        ${h.input_area('message', '', rows=2)}
        <div class="line">
          ${h.input_submit(_('Send reply'), class_='btn action_submit')}
        </div>
      </form>
      </%base:rounded_block>
    </%def>
    ${_("%(user_link)s has posted a new message %(message_link)s to the group %(group_link)s.") % \
       dict(user_link=event.link_to_author(),
            group_link=h.object_link(event.context),
            message_link=h.object_link(event.message)) | n}
  </%self:wall_item>
</%def>

<%def name="moderated_post_created(event)">
  <%self:wall_item event="${event}">
    <%def name="classes()">message_event mailinglistpost_created</%def>
    <%def name="content()">
      <span class="truncated">${h.email_with_replies(event.message.body, True)}</span>
    </%def>
    <%def name="when()">${event.when()}</%def>
    ${_("%(user_link)s has posted a new message %(message_link)s to the group's %(group_link)s moderation queue.") % \
         dict(user_link=event.link_to_author(),
              group_link=h.object_link(event.context),
              message_link=h.object_link(event.message)) | n}
    <%def name="action_link()">${_('Moderate')}</%def>
    <%def name="action()">
      <%base:rounded_block>
      ${moderation.listThreadsActions(event.message)}
      </%base:rounded_block>
    </%def>
  </%self:wall_item>
</%def>

<%def name="forumpost_created(event)">
  <%self:wall_item event="${event}">
    <%def name="classes()">message_event forumpost_created</%def>
    <%def name="content()">
      <span class="truncated">${h.nl2br(event.post.message)}</span>
    </%def>
    <%def name="when()">${event.when()}</%def>
    <%def name="action_link()">${_('Reply')}</%def>
    <%def name="action()">
      <%base:rounded_block>
      <form method="post" action="${url(controller='forum', action='reply', id=event.context.group_id, category_id=event.post.category_id, thread_id=event.post.thread_id)}"
            id="forum_reply_form" class="fullForm" enctype="multipart/form-data">
        ${h.input_area('message', '', rows=2)}
        <div class="line">
          ${h.input_submit(_('Send reply'), class_='btn action_submit')}
        </div>
      </form>
      </%base:rounded_block>
    </%def>
    ${_("%(user_link)s has posted a new message %(message_link)s in the forum %(group_link)s.") % \
       dict(user_link=h.object_link(event.user),
            group_link=h.object_link(event.context),
            message_link=h.object_link(event.post)) | n}
  </%self:wall_item>
</%def>

<%def name="sms_sent(event)">
  <%self:wall_item event="${event}">
    <%def name="classes()">sms_event sms_sent</%def>
    <%def name="content()">${event.sms_text()}</%def>
    <%def name="when()">${event.when()}</%def>
    <%def name="action_link()">${_('Reply')}</%def>
    <%def name="action()">
      <%base:rounded_block>
      ${sms_widget(c.user, event.context)}
      </%base:rounded_block>
    </%def>

    ${_("%(user_link)s has sent an sms to the group %(group_link)s.") % \
       dict(user_link=h.object_link(event.user),
            group_link=h.object_link(event.context)) | n}
  </%self:wall_item>
</%def>

<%def name="privatemessage_sent(event)">
  <%self:wall_item event="${event}">
    <%def name="classes()">privatemessage_event privatemessage_sent</%def>
    <%def name="content()">
      <span class="truncated">${h.nl2br(event.message_text())}</span>
    </%def>
    <%def name="when()">${event.when()}</%def>
    <%def name="action_link()">${_('Reply')}</%def>
    <%def name="action()">
      <%base:rounded_block>
      <form method="post" action="${url(controller='messages', action='reply', id=event.private_message.id)}"
            id="message_reply_form" class="wallForm">
        ${h.input_area('message', '', rows=2)}
        <div class="line">
          ${h.input_submit(_('Send reply'), class_='btn action_submit')}
        </div>
      </form>
      </%base:rounded_block>
    </%def>
    %if event.user != c.user:
      ${_("%(user_link)s has sent you a private message \"%(msg_link)s\".") % \
         dict(user_link=h.object_link(event.user),
              msg_link=h.object_link(event.private_message)) | n}
    %else:
      ${_("%(user_link)s has sent %(recipient_link)s a private message \"%(msg_link)s\".") % \
         dict(user_link=h.object_link(event.user),
              recipient_link=h.object_link(event.recipient),
              msg_link=h.object_link(event.private_message)) | n}
    %endif
  </%self:wall_item>
</%def>


<%def name="groupmember_joined(event)">
  <%self:wall_item event="${event}">
    <%def name="classes()">group_event groupmember_joined</%def>
    <%def name="when()">${event.when()}</%def>
    ${_("%(user_link)s joined the group %(group_link)s.") % \
       dict(user_link=h.object_link(event.user),
            group_link=h.object_link(event.context)) | n}
  </%self:wall_item>
</%def>

<%def name="groupmember_left(event)">
  <%self:wall_item event="${event}">
    <%def name="classes()">group_event groupmember_left</%def>
    <%def name="when()">${event.when()}</%def>
    ${_("%(user_link)s left the group %(group_link)s.") % \
       dict(user_link=h.object_link(event.user),
            group_link=h.object_link(event.context)) | n}
  </%self:wall_item>
</%def>

<%def name="groupsubject_start(event)">
  <%self:wall_item event="${event}">
    <%def name="classes()">group_event groupsubject_start</%def>
    <%def name="content()">
      <div class="subject_link">
        ${h.object_link(event.subject)}
      </div>
    </%def>
    <%def name="when()">${event.when()}</%def>
    ${_("The group %(group_link)s has started watching the subject %(subject_link)s.") % \
       dict(subject_link=h.object_link(event.subject),
            group_link=h.object_link(event.context)) | n}
  </%self:wall_item>
</%def>

<%def name="groupsubject_stop(event)">
  <%self:wall_item event="${event}">
    <%def name="classes()">group_event groupsubject_stop</%def>
    <%def name="content()">
      <div class="subject_link">
        ${h.object_link(event.subject)}
      </div>
    </%def>
    <%def name="when()">${event.when()}</%def>
    ${_("The group %(group_link)s has stopped watching the subject %(subject_link)s.") % \
       dict(subject_link=h.object_link(event.subject),
            group_link=h.object_link(event.context)) | n}
  </%self:wall_item>
</%def>

<%def name="page_created(event)">
  <%self:wall_item event="${event}">
    <%def name="classes()">page_event page_created</%def>
    <%def name="when()">${event.when()}</%def>
    ${_("%(user_link)s has created a page %(page_link)s in the subject %(subject_link)s.") % \
       dict(subject_link=h.object_link(event.context),
            page_link=h.object_link(event.page),
            user_link=h.object_link(event.user)) | n}
  </%self:wall_item>
</%def>

<%def name="page_modified(event)">
  <%self:wall_item event="${event}">
    <%def name="classes()">page_event page_modified</%def>
    <%def name="when()">${event.when()}</%def>
    ${_("%(user_link)s has modified a page %(page_link)s in the subject %(subject_link)s.") % \
       dict(subject_link=h.object_link(event.context),
            page_link=h.object_link(event.page),
            user_link=h.object_link(event.user)) | n}
  </%self:wall_item>
</%def>

<%def name="render_events(events=None)">
  <%
     if events is None:
       events = c.events
  %>
  % for event in events:
    ${event.snippet()}
  % endfor
</%def>
