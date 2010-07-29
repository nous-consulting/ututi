<%inherit file="/portlets/base.mako"/>

<%def name="portlet_file(file)">
  <li>
    <a href="${file.url()}" title="${file.title}">${h.ellipsis(file.title, 30)}</a>
    <input class="delete_url" type="hidden" value="${file.url(action='delete')}" />
  </li>
</%def>

<%def name="group_info_portlet(group=None)">
  <%
     if group is None:
         group = c.group
  %>

  <%self:uportlet id="group_info_portlet" portlet_class="MyProfile first">

    <%def name="header()">
      <a ${h.trackEvent(c.group, 'home', 'portlet_header')} href="${group.url()}" title="${group.title}">${_('Group information')}</a>
    </%def>

    <div class="profile">
      <div class="floatleft avatar">
        <img id="group-logo" src="${url(controller='group', action='logo', id=group.group_id, width=70, height=70)}" alt="logo" />
      </div>
      <div class="floatleft personal-data">
        <div><h2 class="grupes-portlete">${group.title}</h2></div>
        %if not c.group.forum_is_public:
        <div>
          <a href="${group.location.url()}">${' | '.join(group.location.title_path)}</a>
          <span class="right_arrow"></span>
        </div>
        %else:
        <div style="width: 190px">
          <a href="${group.url()}">${group.url(qualified=True)}</a>
        </div>
        %endif
        %if not c.group.forum_is_public:
        <div>
          %if group.is_member(c.user):
            <a href="${url(controller='mailinglist', action='new_thread', id=c.group.group_id)}" title="${_('Mailing list address')}">${group.group_id}@${c.mailing_list_host}</a>
          %elif c.user is not None:
            <a href="${url(controller='mailinglist', action='new_anonymous_post', id=c.group.group_id)}" title="${_('Mailing list address')}">${group.group_id}@${c.mailing_list_host}</a>
          %endif
        </div>
        %endif
        <div>${ungettext("%(count)s member", "%(count)s members", len(group.members)) % dict(count=len(group.members))}</div>
      </div>
      ##<div style="float: left; margin-top: 3px">
      ##  <fb:like width="90" show_faces="false" url=${group.url(qualified=True)}></fb:like>
      ##</div>
      <div class="clear"></div>
    </div>
    %if (group.is_member(c.user) or c.security_context and h.check_crowds(['admin', 'moderator'])) and group.has_file_area:
    <div class="profile topLine grey" style="font-size: 11px">
      <span class="bold">${_('Available space for private group files:')}</span>
      <span class="verysmall">${h.file_size(group.free_size)}</span>
      ${h.image('/images/details/pbar%d.png' % group.free_size_points, alt=h.file_size(group.size), class_='area_size_points')|n}
      <div style="padding-top: 4px; padding-bottom: 7px" class="bottomLine">
        ${h.button_to(_('Get more space'), group.url(action='pay'))}
      </div>
    </div>
    %endif
    <p class="grupes-aprasymas">
      ${group.description}
    </p>

    %if group.is_member(c.user) or c.security_context and h.check_crowds(['admin', 'moderator']):
    <div class="click2show">
      <div class="remeju-sarasas click">
        <a href="#">${_("More settings")}</a>
      </div>
      <div class="show" id="group_settings_block">
        %if group.is_subscribed(c.user):
        <div style="display: inline-block; padding-top: 8px">
          ${h.button_to(_("Do not get email"), group.url(action='unsubscribe'), class_='btn inactive')}
        </div>
        %else:
        <div style="display: inline-block; padding-top: 8px">
          ${h.button_to(_("Get email"), group.url(action='subscribe'), class_='btn')}
        </div>
        %endif
        <div style="display: inline-block; padding-top: 8px">
          ${h.button_to(_("Leave group"), group.url(action='leave'), class_='btn warning')}
        </div>
      </div>
    </div>
    %endif

    %if group.is_admin(c.user) or c.security_context and h.check_crowds(['admin', 'moderator']):
      <div class="floatright" style="margin-top: 6px">
      <span class="right_arrow">
        <a href="${url(controller='group', action='edit', id=group.group_id)}" title="${_('Edit group settings')}">${_('Edit')}</a>
      </span>
    </div>
    %endif
    <br class="clear-right" />
  </%self:uportlet>
</%def>

<%def name="group_watched_subjects_portlet(group=None)">
  <%
     if group is None:
         group = c.group
  %>
  <%self:uportlet id="subject_portlet">
    <%def name="header()">
      <a ${h.trackEvent(c.group, 'subjects', 'portlet_header')} href="${group.url(action='subjects')}" title="${_('All watched subjects')}">${_('Watched subjects')}</a>
    </%def>
    %if not group.watched_subjects:
      ${_('Your group is not watching any subjects!')}
    %else:
    <ul id="DalykaiList" class="subjects-list">
      % for subject in group.watched_subjects[:5]:
      <li class="grupes-dalykai">
        <a href="${subject.url()}" title="${subject.title}">${h.ellipsis(subject.title, 35)}</a>
      </li>
      % endfor
    </ul>
    %endif
    <div class="secondModuleLayer">
      <a style="float: right; margin-top: 4px;" class="right_arrow" href="${group.url(action='subjects')}">${_('all subjects')}</a>
      ${h.button_to(_('choose subjects'), group.url(action='subjects'))}
    </div>
  </%self:uportlet>
</%def>

<%def name="group_forum_post_portlet(group=None)">
  <%
     if group is None:
         group = c.group
  %>
  <%self:action_portlet id="forum_post_portlet">
    <%def name="header()">
    <a class="blark" ${h.trackEvent(None, 'click', 'group_forum_post', 'action_portlets')} href="${url(controller='mailinglist', action='new_thread', id=group.group_id)}">${_('email your group')}</a>
    ${h.image('/images/details/icon_question.png',
            alt=_("Write an email to the group's forum - accessible by all your classmates."),
             class_='tooltip', style='margin-top: 4px;')|n}

    </%def>
  </%self:action_portlet>
</%def>

<%def name="group_invite_member_portlet(group=None)">
  <%
     if group is None:
         group = c.group
  %>
  <%self:action_portlet id="invite_member_portlet">
    <%def name="header()">
    <a class="blark" ${h.trackEvent(None, 'click', 'group_invite_members', 'action_portlets')} href="${group.url(action='members')}">${_('invite classmates')}</a>
    ${h.image('/images/details/icon_question.png',
            alt=_("Invite your classmates to use Ututi with you."),
             class_='tooltip', style='margin-top: 4px;')|n}

    </%def>
  </%self:action_portlet>
</%def>

<%def name="group_members_portlet(group=None)">
  <%
     if group is None:
         group = c.group
  %>
  <%self:uportlet id="group_info_portlet" portlet_class="MyProfile first">

    <%def name="header()">
      <a ${h.trackEvent(c.group, 'home', 'portlet_header')} href="${group.url(action='members')}" title="${_('''Group's members''')}">${_("Group's members")}</a>
    </%def>
    <div class="members_list">
      %for member in group.members[:8]:
        <div class="user-logo-link">
          <div class="user-logo">
            <a href="${url(controller="user", action="index", id=member.user.id)}" title="${member.user.fullname}">
              %if member.user.logo is not None:
                <img src="${url(controller='user', action='logo', id=member.user.id, width=45, height=45)}" alt="logo" />
              %else:
                ${h.image('/img/avatar-light-small.png', alt='logo')}
              %endif
            </a>
          </div>
          <div>
            <a class="verysmall blark" href="${url(controller="user", action="index", id=member.user.id)}" title="${member.user.fullname}">
              ${h.ellipsis(member.user.fullname, 10)}
            </a>
          </div>
        </div>
      %endfor
        <br class="clear-left" />
    </div>
    %if not group.is_member(c.user):
      ${h.button_to(_('become a member'), url(controller='group', action='request_join', id=group.group_id))}
    %endif
  </%self:uportlet>
</%def>

<%def name="group_sms_portlet(group=None)">
  <%
     if group is None:
         group = c.group
  %>
  <%self:uportlet id="group_sms_portlet" portlet_class="MyProfile">
    <%def name="header()">
      ${_('Send SMS message to group')}
    </%def>

    <div class="character-counter">
        <span id="sms_message_symbols">140</span> / <span id="sms_messages_num">1</span>
    </div>
    <span>${_('Message text:')}</span>

    ##<div>
    ##  ${_('Send a message to number 1337 (2 Lt): "TXT&nbsp;%(sms_code)s&nbsp;%(group_id)s&nbsp;Your message"') % dict(sms_code=c.pylons_config.get('fortumo.personal_sms_credits.code', 'U2TISMS'), group_id=c.group.group_id) |n}
    ##</div>

    %if c.user.sms_messages_remaining:
      <form method='post' action="${url(controller='group', action='send_sms', id=group.group_id)}">
          <input type="hidden" name="current_url" value="${url.current()}" />
          ${h.input_area('sms_message', '', cols=35)}
          %if not c.group.recipients_sms(sender=c.user):
            <div class="error-container">
              <span class="error-message">${_('No one in this group has confirmed their phone numbers.')}</span>
            </div>
          %endif
          <div style="padding-top: 4px">
            ${h.input_submit(_('Send'))} <span class="recipients">(${len(c.group.recipients_sms(sender=c.user))} ${_('recipients')})</span>
          </div>
      </form>

      <div class="cost">
          <span class="cost-header">${_("Cost:")}</span>
          <span id="sms_message_credits">${len(c.group.recipients_sms(sender=c.user))}</span> ${_('SMS credits')}
          <img style="margin-bottom: -3px" src="/images/details/icon_question.png" class="tooltip " alt="${_('One SMS credits allows you to send one SMS message to a single recipient. When sending a message to a group, one credit is charged for every recipient.')}">
      </div>

      <div class="credits-remaining">
          <span class="credits-header">${_('Credits in your personal account:')}</span>
          <span>${c.user.sms_messages_remaining}</span>
          <div style="padding-top: 3px">
            <form>
              ${h.input_submit(_('Purchase credits'), id='purchase-credits-button')}
            </form>
          </div>

          ${h.javascript_link('/javascript/jquery-ui-1.7.2.custom.min.js')|n}
          ${h.javascript_link('/javascript/jquery.form.js')|n}
          ${h.stylesheet_link('/jquery-ui-1.7.3.custom.css')}

          <div id="purchase-credits-dialog" style="display: none">
              <div style="font-size: 14px">
                ${_('SMS credits can be used to send SMS messages to members of a group. There are two ways to purchase SMS credits:')}
              </div>
              <div style="clear: both"></div>

              <div style="width: 270px; float: left; padding-right: 1em">
                  <div style="font-size: 16px; font-weight: bold; color: #666; padding-top: 1em; padding-bottom: 0.5em">
                      ${_('SMS message')}
                  </div>
                  <div>
                    ${_('Send an SMS message to number <span style="font-size: 14px">1337</span> with the following content:')|n}
                  </div>
                  <div style="font-size: 14px; padding: 0.5em">TXT ${c.pylons_config.get('fortumo.personal_sms_credits.code')} ${c.group.group_id}</div>
                  <div>
                    ${_('The SMS costs <strong>5 Lt</strong> and <strong>50 credits</strong> will be added to your account (one credit is one SMS to a single person).')|n}
                  </div>
              </div>

              <div style="width: 270px; float: left; border-left: 1px solid #ded8d8; padding-left: 1em">
                  <div style="font-size: 16px; font-weight: bold; color: #666; padding-top: 1em; padding-bottom: 0.5em">
                      ${_('E-banking')}
                  </div>
                  <div style="padding-bottom: 10px">
                      ${_('If you pay by bank, <strong>a large discount applies</strong>.')|n}
                  </div>

                  <table>
                    <tr>
                      <td>
                        ${h.button_to(_('5 Lt'), '', class_='btnMedium')}
                      </td>
                      <td>
                        <span style="text-decoration: line-through">50</span>
                        <span style="font-size: 16px">70</span>
                        ${_('credits')}
                      </td>
                    </tr>
                    <tr>
                      <td>
                        ${h.button_to(_('10 Lt'), '', class_='btnMedium')}
                      </td>
                      <td>
                        <span style="text-decoration: line-through">100</span>
                        <span style="font-size: 16px">150</span>
                        ${_('credits')}
                      </td>
                    </tr>
                    <tr>
                      <td>
                        ${h.button_to(_('20 Lt'), '', class_='btnMedium')}
                      </td>
                      <td>
                        <span style="text-decoration: line-through">200</span>
                        <span style="font-size: 16px">350</span>
                        ${_('credits')}
                      </td>
                    </tr>
                  </table>

              </div>
          </div>

          <script>
            $('#purchase-credits-button').click(function() {
                $('#purchase-credits-dialog').dialog({
                    title: '${_('Purchase SMS credits')}',
                    width: 600
                });
                return false;
            });
          </script>
      </div>

      <script>
          $(document).ready(function() {
              $('textarea#sms_message').keyup(function() {
                var el = $('#sms_message')[0];
                var s = el.value;
                var ascii = true;
                for (var i = 0; i < s.length; i++) {
                    var c = s.charCodeAt(i);
                    if (c > 127) {
                        ascii = false;
                        break;
                    }
                }
                var n_recipients = ${len(c.group.recipients_sms(sender=c.user))};
                var text_length = s.length;

                // Please keep math in sync with Python controller code.
                // -----
                var msg_length = text_length * (ascii ? 1 : 2);
                if (msg_length <= 140) {
                    msgs = 1;
                } else {
                    msgs = 1 + Math.floor((msg_length - 1) / 134);
                }
                var cost = n_recipients * msgs;
                // -----

                $('#sms_messages_num').text(msgs);
                $('#sms_message_credits').text(cost);

                var chars_remaining;
                if (msg_length <= 140) {
                    chars_remaining = (140 - msg_length);
                } else {
                    chars_remaining = 134 - (msg_length % 134)
                }
                if (!ascii)
                    chars_remaining = chars_remaining / 2;
                $('#sms_message_symbols').text(chars_remaining);
              });
          });
      </script>
    %else:
      ${_('You need to buy credits to be able to send SMS messages to the group.')}
      % if not c.user.phone_confirmed:
        ${_('You need to confirm your phone in your <a href="%s">profile</a>.') % url(controller='profile', action='edit')|n}
      % endif
      ${_('Send an SMS to number 1337 with the content "TXT&nbsp;%(sms_code)s" (price: 10 Lt) to buy 100 credits.') % dict(sms_code=c.pylons_config.get('fortumo.personal_sms_credits.code', 'U2TISMS')) |n}
    %endif
  </%self:uportlet>
</%def>
