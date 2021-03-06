<%inherit file="/profile/base.mako" />
<%namespace file="/widgets/tags.mako" import="*"/>
<%namespace file="/search/index.mako" import="search_form"/>
<%namespace file="/search/browse.mako" import="universities_section"/>

<%def name="pagetitle()">
${_('Universities')}
</%def>

${search_form(c.text, c.obj_type, c.tags, parts=['text'], target=url(controller='profile', action='search'))}

${universities_section(c.unis, url(controller='profile', action='browse'), collapse=False)}
<br class="clear-left" />

