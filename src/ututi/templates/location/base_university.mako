<%inherit file="/ubase-sidebar.mako" />
<%namespace file="/portlets/structure.mako" import="*"/>
<%namespace file="/portlets/school.mako" import="*"/>
<%namespace file="/sections/content_snippets.mako" import="tabs"/>
<%namespace file="/anonymous_index.mako" import="universities_section"/>

<%def name="title()">
  ${c.location.title}
</%def>

<%def name="pagetitle()">
  ${c.location.title}
</%def>

<%def name="portlets()">
<div id="sidebar">
  ${struct_info_portlet()}
  ${school_members_portlet(_("School's members"))}
</div>
</%def>

<h1 class="page-title">${self.pagetitle()}</h1>

${universities_section(c.departments, c.location.url(), collapse=True, collapse_text=_('More departments'))}
${tabs()}

${next.body()}
