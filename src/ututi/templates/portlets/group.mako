<%inherit file="/portlets/base.mako"/>

<%def name="group_info_portlet(group=None)">
  <%
     if group is None:
         group = c.group
  %>

  <%self:portlet id="group_info_portlet">
    <%def name="header()">
      ${_('Group information')}
    </%def>
    %if group.logo is not None:
      <img id="group-logo" src="${url(controller='group', action='logo', id=group.group_id, width=70)}" alt="logo" />
    %endif
    <div class="structured_info">
      <h4>${group.title}</h4>
      <span class="small">${group.location and ' | '.join(group.location.path)}</span><br/>
      <a class="small" href="mailto:${group.group_id}@${c.mailing_list_host}" title="${_('Mailing list address')}">${group.group_id}@${c.mailing_list_host}</a><br/>
      <span class="small">${len(group.members)} ${_('members')}</span>
    </div>
    <div class="description small">
      ${group.description}
    </div>
    <span class="portlet-link">
      <a class="small" href="${url(controller='group', action='edit', id=group.group_id)}" title="${_('Edit group settings')}">${_('Edit')}</a>
    </span>
    <br style="clear: right;" />
  </%self:portlet>
</%def>

<%def name="group_changes_portlet(group=None)">
  <%
     if group is None:
         group = c.group
  %>

  <%self:portlet id="group_changes_portlet" portlet_class="inactive XXX">
    <%def name="header()">
      ${_('Latest changes')}
    </%def>
    <table class="group-changes">
      <tr>
        <td class="change-category">${_('New files')}</td>
        <td class="change-count">2</td>
      </tr>
      <tr>
        <td class="change-category">${_('New messages')}</td>
        <td class="change-count">123</td>
      </tr>
      <tr>
        <td class="change-category">${_('Wiki edits')}</td>
        <td class="change-count">0</td>
      </tr>
    </table>
    <span class="portlet-link">
      <a class="small" href="${url(controller='group', action='changes', id=group.group_id)}" title="${_('More')}">${_('More')}</a>
    </span>
    <br style="clear: right;" />
  </%self:portlet>
</%def>

<%def name="group_members_portlet(group=None)">
  <%
     if group is None:
         group = c.group
  %>

  <%self:portlet id="group_members_portlet" portlet_class="inactive">
    <%def name="header()">
      ${_('Recently seen')}
    </%def>
    %for member in group.last_seen_members[:3]:
    <div class="user-logo-link">
      <div class="user-logo">
        <a href="${url(controller='user', action='index', id=member.id)}" title="${member.fullname}">
          %if member.logo is not None:
            <img src="${url(controller='user', action='logo', id=member.id, width=40, height=40)}" alt="${member.fullname}"/>
          %else:
            ${h.image('/images/user_logo_small.png', alt=member.fullname)|n}
          %endif
        </a>
      </div>
      <div>
        <a href="${url(controller='user', action='index', id=member.id)}" title="${member.fullname}">
          <span class="small">${member.fullname}</span>
        </a>
      </div>
    </div>
    %endfor
    <br style="clear: both;" />
    <span class="portlet-link">
      <a class="small" href="${url(controller='group', action='members', id=group.group_id)}" title="${_('More')}">${_('More') | h.ellipsis}</a>
    </span>
    <br style="clear: both;" />
  </%self:portlet>
</%def>

<%def name="group_watched_subjects_portlet(group=None)">
  <%
     if group is None:
         group = c.group
  %>
  <%self:portlet id="watched_subjects_portlet" portlet_class="inactive XXX">
    <%def name="header()">
      ${_('Watched subjects')}
    </%def>
    %for subject in group.watched_subjects:
    <div>
      <a href="${subject.url()}">
          ${subject.title}
      </a>
    </div>
    %endfor
    <br style="clear: both;" />
    <span class="portlet-link">
      <a class="small" href="${url(controller='group', action='subjects', id=group.group_id)}" title="${_('More')}">${_('More')}</a>
    </span>
    <br style="clear: both;" />
  </%self:portlet>
</%def>

<%def name="group_forum_portlet(group=None)">
  <%
     if group is None:
         group = c.group
  %>
  <%self:portlet id="forum_portlet" portlet_class="inactive">
    <%def name="header()">
      ${_('Group messages')}
    </%def>
    <table id="group_latest_messages">
      %for message in group.all_messages[:5]:
      <tr>
        <td class="time">${h.fmt_shortdate(message.sent)}</td>
        <td class="subject"><a href="${message.url()}" title="${message.subject}, ${message.author.fullname}">${h.ellipsis(message.subject, 35)}</a></td>
      </tr>
      %endfor
    </table>
    <br style="clear: both;" />
    <span class="portlet-link">
      <a class="small" href="${url(controller='group', action='forum', id=group.group_id)}" title="${_('More')}">${_('More')}</a>
    </span>

    <a href="${url(controller='groupforum', action='new_thread', id=c.group.group_id)}" class="btn"><span>${_("New topic")}</span></a>
    <br style="clear: both;" />
  </%self:portlet>
</%def>
