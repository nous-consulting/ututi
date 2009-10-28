<%inherit file="/profile/base.mako" />
<%namespace file="/portlets/user.mako" import="*"/>
<%namespace file="/widgets/tags.mako" import="*"/>
<%namespace file="/search/index.mako" import="search_form"/>
<%namespace file="/anonymous_index.mako" import="*"/>

<%def name="head_tags()">
${h.stylesheet_link('/stylesheets/tagwidget.css')|n}

${parent.head_tags()}
</%def>

<%def name="portlets()">
<div id="sidebar">
  ${user_subjects_portlet()}
  ${user_groups_portlet()}

</div>
</%def>


<h1>${_('Search')}</h1>
${search_form(c.text, c.obj_type, c.tags, parts=['obj_type', 'text', 'tags'], target=url(controller='profile', action='search'))}

${universities_section(c.unis, url(controller='profile', action='browse'))}
<br class="clear-left" />

