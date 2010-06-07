<%inherit file="/forum/base.mako" />

<div class="back-link">
  <a class="back-link" href="${url(controller=c.controller, action='index', id=c.group_id, category_id=c.category_id)}"
    >${_('Back to the topic list')}</a>
</div>

<h1>${c.thread.title}</h1>

<table id="forum-thread">
  <tr>
    <td colspan="2" style="padding-top: 0">
      <div style="float: right">
        % if not c.subscribed:
          ${h.button_to(_('Subscribe to emails'), url(controller=c.controller, action='subscribe', id=c.group_id, category_id=c.category_id, thread_id=c.thread.id))}
        % else:
          ${h.button_to(_('Unsubscribe from emails'), url(controller=c.controller, action='unsubscribe', id=c.group_id, category_id=c.category_id, thread_id=c.thread.id))}
        % endif
      </div>
    </td>
  </tr>

% for forum_post in c.forum_posts:
  % if forum_post != c.forum_posts[0] and c.first_unseen and forum_post.id == c.first_unseen.id:
    <tr> <td colspan="2"><a name="unseen"></a><hr /><td>
    </tr>
  % endif
  <tr>
    <td colspan="2" class="author">
      <a href="${forum_post.created.url()}">${forum_post.created.fullname}</a>
      % for medal in forum_post.created.all_medals():
          ${medal.img_tag()}
      % endfor
      <span class="created-on">${h.fmt_dt(forum_post.created_on)}</span>
        % if c.can_manage_post(forum_post):
          <div style="float:right">
            ${h.button_to(_('Edit'), url(controller=c.controller, action='edit', id=c.group_id, category_id=c.category_id, thread_id=forum_post.id))}
          </div>
          <div style="float:right">
            ${h.button_to(_('Delete') if forum_post != c.forum_posts[0] else _('Delete thread'), url(controller=c.controller, action='delete_post', id=c.group_id, category_id=c.category_id, thread_id=forum_post.id))}
          </div>
        % endif
        % if c.can_post(c.user):
          <div style="float: right">
            ${h.button_to(_('Reply'), url(controller=c.controller, action='thread', id=c.group_id, category_id=c.category_id, thread_id=c.thread_id) + '#reply')}
          </div>
        % endif
    </td>
  </tr>
  <tr class="thread-post">
    <td class="author-logo">
      <a href="${forum_post.created.url()}">
        %if forum_post.created.logo is not None:
          <img alt="user-logo" src="${url(controller='user', action='logo', id=forum_post.created.id, width='45', height='60')}"/>
        %else:
          ${h.image('/images/user_logo_45x60.png', alt='logo', id='group-logo')|n}
        %endif
      </a>
    </td>
    <td class="forum_post">
      <div class="forum_post-content">
        <div class="post-body">
          ${h.nl2br(forum_post.message)}
        </div>
      </div>
    </td>
  </tr>
% endfor
</table>

% if c.can_post(c.user):
  <div id="reply-section">
    <a name="reply"></a>
    <h2>${_('Reply')}</h2>
    <br />
    <form method="post" action="${url(controller=c.controller, action='reply', id=c.group_id, category_id=c.category_id, thread_id=c.thread_id)}"
         id="group_add_form" class="fullForm" enctype="multipart/form-data">
      ${h.input_area('message', _('Message'))}
      <br />
      ${h.input_submit(_('Reply'))}
    </form>
  </div>
% endif
