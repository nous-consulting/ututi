<%namespace file="/portlets/user.mako" import="*"/>
<%namespace file="/portlets/group.mako" import="*"/>
<%namespace file="/portlets/universal.mako" import="*"/>
<%namespace file="/portlets/search.mako" import="*"/>
<%namespace file="/portlets/banners/base.mako" import="*"/>

<%def name="user_sidebar(exclude=[])">
<div id="sidebar">
  ${user_information_portlet()}
  %if not 'files' in exclude:
  ${quick_file_upload_portlet(c.user.groups + c.user.watched_subjects, label='user_files')}
  %endif
  %if not 'create_group' in exclude:
  ${user_create_group_portlet()}
  %endif
  %if not 'create_subject' in exclude:
  ${user_create_subject_portlet()}
  %endif
  %if not 'recommend' in exclude:
  ${user_recommend_portlet()}
  %endif
  %if not 'blog' in exclude:
  ${blog_portlet()}
  %endif
  ${user_support_portlet()}
</div>
</%def>

<%def name="group_sidebar(exclude=[])">
<div id="sidebar">
  %if not 'info' in exclude:
  ${group_info_portlet()}
  %endif
  %if not c.group.forum_is_public:
    %if not 'files' in exclude and c.group.has_file_area:
    ${quick_file_upload_portlet([c.group] + c.group.watched_subjects, label='group_files')}
    %endif
    %if not 'forum' in exclude:
    ${group_forum_post_portlet()}
    %endif
    %if not 'members' in exclude:
    ${group_invite_member_portlet()}
    %endif
    %if not 'subjects' in exclude and c.group.wants_to_watch_subjects:
    ${group_watched_subjects_portlet()}
    %endif
    ${ututi_prizes_portlet()}
  %else:
    ${group_members_portlet()}
    ${user_support_portlet()}
  %endif
</div>
</%def>
