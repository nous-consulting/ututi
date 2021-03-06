<%inherit file="/base.mako" />
<%namespace file="/profile/base.mako" name="profile" />
<%namespace file="/portlets/user.mako" import="invite_friends_portlet,
                                               teacher_page_portlet,
                                               todo_portlet"/>
<%namespace file="/portlets/universal.mako" import="users_online_portlet,
                                                    about_portlet"/>

<%def name="portlets()">
  ${profile.portlets()}
</%def>

<%def name="portlets_secondary()">
  ${about_portlet()}
  %if c.user.is_teacher:
  ${teacher_page_portlet()}
  %endif
  ${todo_portlet()}
  ${invite_friends_portlet()}
  ${users_online_portlet()}
</%def>

%if hasattr(self, 'pagetitle'):
  <h1 class="page-title underline">${self.pagetitle()}</h1>
%endif

${next.body()}
