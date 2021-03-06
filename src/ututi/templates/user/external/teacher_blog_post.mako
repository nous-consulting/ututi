<%inherit file="/user/external/teacher_base.mako" />
<%namespace name="snippets" file="/sections/content_snippets.mako" />

<%def name="pagetitle()">${_("Blog")}</%def>

<%def name="actionlink()">
  <a href="${url(controller='profile', action='edit_blog_post', id=c.blog_post.id)}">
    ${_("edit post")}
  </a>
</%def>

<div class="back-link">
  <a class="back-link" href="${url(controller='user', action='external_teacher_blog_index', id=c.teacher.id, path=c.location.url_path)}"
    >${_('Back to post list')}</a>
</div>
<div class="page-section blog">
  <%snippets:blog_post post="${c.blog_post}" />
</div>
