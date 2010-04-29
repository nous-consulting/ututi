<%inherit file="/portlets/base.mako"/>

<%def name="forum_info_portlet()">
  <%self:portlet id="forum_info_portlet">
    <%def name="header()">
        <a href="${url.current(action='index')}" title="${c.forum.title}">${c.forum.title}</a>
    </%def>
    <!-- XXX
      <img id="forum-logo"  class="logo" src="${url('/images/%s') }" alt="logo" />
    -->
    <div class="structured_info">
      <span class="small">
        ${ungettext("<em>%(count)s</em> active poster", "<em>%(count)s</em> active posters", c.forum.poster_count()) % dict(count=c.forum.poster_count())|n}
      </span>
      <br />
      <span class="small">
        ${ungettext("<em>%(count)s</em> topic", "<em>%(count)s</em> topics", c.forum.topic_count()) % dict(count=c.forum.topic_count())|n}
      </span>
      <br />
      <span class="small">
        ${ungettext("<em>%(count)s</em> post", "<em>%(count)s</em> posts", c.forum.post_count()) % dict(count=c.forum.post_count())|n}
      </span>
    </div>
    <br />
    <hr />
    <div class="description small">
      ${c.forum.description}
    </div>
  </%self:portlet>
</%def>

<%def name="forum_posts_portlet(forum_id, route_id, new_post_subtitle, messages, portlet_title, new_post_title)">
  <%self:portlet id="group_latest_messages" portlet_class="inactive">
    <%def name="header()">
      <a href="${url(route_id)}">${portlet_title|n}</a>
    </%def>
    %if messages:
      <table id="group_latest_messages">
        %for message in messages[:5]:
        <tr>
          <td class="time">${h.fmt_shortdate(message.created_on)}</td>
          <td class="subject"><a href="${message.url()}" title="${message.title}, ${message.created.fullname}">${h.ellipsis(message.title, 25)}</a></td>
        </tr>
        %endfor
      </table>
    %else:
      <div class="notice">${_("There are no messages.")}</div>
    %endif
    <br style="clear: both;" />
    <div class="footer">
      <a class="more" href="${url.current(action='index')}" title="${_('more')}">${_('more')}</a>
      <a href="${url.current(action='new_thread')}" class="btn"><span>${new_post_title}</span></a>
    </div>
  </%self:portlet>
</%def>

<%def name="community_forum_posts_portlet()">
${forum_posts_portlet(forum_id=1,
                      route_id='forum_community_index',
                      new_post_subtitle='',
                      messages=c.forum.messages(),
                      portlet_title=_('Messages in community forum'),
                      new_post_title=_('New topic'))}
</%def>

<%def name="bugs_forum_posts_portlet()">
${forum_posts_portlet(forum_id=2,
                      route_id='forum_bugs_index',
                      new_post_subtitle=_('You found a bug in our system? Something is broken? Report it.'),
                      messages=c.forum.messages(),
                      portlet_title=_('Messages in Bugs forum'),
                      new_post_title=_('Report a bug'))}
</%def>
