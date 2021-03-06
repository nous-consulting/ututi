<%inherit file="/group/create_base.mako" />
<%namespace name="members" file="/group/members.mako" />

<%def name="css()">
  ${parent.css()}
  ${members.css()}
</%def>

<%def name="title()">
  ${_('Invite group members')}
</%def>

${self.path_steps(2)}

${members.group_members_invite_section(wizard=True)}
