<%inherit file="/ubase-sidebar.mako" />
<%namespace file="/portlets/sections.mako" import="*"/>

<%def name="portlets()">
${user_sidebar()}
</%def>

<%def name="pagetitle()">
${_('Home')}
</%def>

<h1 class="pageTitle">${self.pagetitle()}</h1>
%if c.action:
<ul class="moduleMenu">
  <li class="${'current' if c.action == 'home' else ''}"><a href="${url(controller='profile', action='home')}">${_('Start')}<span class="edge"></span></a></li>
  <li class="${'current' if c.action == 'feed' else ''}"><a href="${url(controller='profile', action='feed')}">${_("What's new?")}<span class="edge"></span></a></li>
  <li><a href="${url(controller='messages', action='index')}">${_("Messages")}<span class="edge"></span></a></li>
</ul>
%endif
${next.body()}
