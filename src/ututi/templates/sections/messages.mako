<%def name="unverified_teacher_message(user=None)">
<% if user is None: user = c.user %>
%if user is not None and user.is_teacher and not user.teacher_verified:
<div class="flash-message">
  <span class="close-link hide-parent">
    ${h.image('/img/icons.com/close.png', alt=_('Close'))}
  </span>
  <span class="flash-message-content">
      ${_('At the moment you are not confirmed as teacher. Our administrators have been notified and will verify you shortly.')}
  </span>
</div>
%endif
</%def>

<%def name="confirmation_messages(user=None)">
<%
   if user is None and c.user is not None:
       user = c.user
%>
%if c.user and not c.user.isConfirmed:
<div class="flash-message">
  <span class="close-link hide-parent">
    ${h.image('/img/icons.com/close.png', alt=_('Close'))}
  </span>
  <span class="flash-message-content">
      ${_('Your email (%(email)s) is not confirmed! '
      'Please confirm your email by clicking on the link sent '
      'to your address or ') % dict(email=c.user.email.email) |n}
  </span>
  <form method="post" action="${url(controller='profile', action='confirm_emails')}" id="email_confirmation_request" class="inline-form">
    <div>
      <input type="hidden" name="came_from" value="${request.url}" />
      <input type="hidden" name="email" value="${c.user.email.email}" />
      <input type="submit" class="text_button" value="${_('get another confirmation email')}" style="font-size: 13px;"/>
    </div>
  </form>
</div>
%endif

%if c.user and c.user.phone_number is not None and not c.user.phone_confirmed:
<div class="flash-message" id="confirm-phone-flash-message">
  <span class="close-link hide-parent">
    ${h.image('/img/icons.com/close.png', alt=_('Close'))}
  </span>
  <span class="flash-message-content">
    ${_('Your phone is not confirmed! Please <a href="%s">confirm</a> it by entering the code sent to you.') % url(controller='profile', action='edit_contacts')|n}
  </span>
</div>
%endif

</%def>

<%def name="invitation_messages(user=None)">
<%
   if user is None and c.user is not None:
       user = c.user
%>
%if user:
  %for invitation in user.invitations:
    % if invitation.active:
      <div class="flash-message">
        <span class="flash-message-content">
          ${h.literal(_(u"%(author)s has sent you an invitation to group %(group)s. Do you want to become a member of this group?") %\
                      dict(author=h.object_link(invitation.author), group=h.object_link(invitation.group)))}
        </span>
        <br />
        <form method="post"
              action="${invitation.group.url(action='invitation')}"
              id="${invitation.group.group_id}_invitation_accept"
              class="inline-form">
          <div style="display: inline;">
            <input type="hidden" name="accept" value="True"/>
            <input type="hidden" name="came_from" value="${request.url}"/>
            ${h.input_submit(_('Accept'), class_='dark inline add')}
          </div>
        </form>
        <form method="post"
              action="${invitation.group.url(action='invitation')}"
              id="${invitation.group.group_id}_invitation_reject"
              class="inline-form">
          <div style="display: inline;">
            <input type="hidden" name="accept" value="False"/>
            <input type="hidden" name="came_from" value="${request.url}"/>
            ${h.input_submit(_('Reject'), class_='dark inline')}
          </div>
        </form>
      </div>
    %endif
  %endfor
%endif

</%def>

<%def name="request_messages(user=None)">
<%
   if user is None and c.user is not None:
       user = c.user
%>
%if user:
  %for rq in user.group_requests():
  <div class="flash-message">
    <span class="flash-message-content">
      ${_(u"%(user)s wants to join the group %(group)s. Do you want to confirm this membership?") % \
        dict(user=h.object_link(rq.user), group=h.object_link(rq.group))|n}
    </span>
    <br />
    <form style="display: inline;" method="post" action="${url(controller='group', action='request', id=rq.group.group_id)}">
      <div style="display: inline;">
        <input type="hidden" name="hash_code" value="${rq.hash}"/>
        <input type="hidden" name="action" value="confirm"/>
        <input type="hidden" name="came_from" value="${request.url}"/>
        ${h.input_submit(_('Confirm'), class_='dark inline add')}
      </div>
    </form>
    <form style="display: inline;" method="post" action="${url(controller='group', action='request', id=rq.group.group_id)}">
      <div style="display: inline;">
        <input type="hidden" name="hash_code" value="${rq.hash}"/>
        <input type="hidden" name="action" value="deny"/>
                <input type="hidden" name="came_from" value="${request.url}"/>
        ${h.input_submit(_('Deny'), class_='dark inline')}
      </div>
    </form>
  </div>
  %endfor
%endif
</%def>
