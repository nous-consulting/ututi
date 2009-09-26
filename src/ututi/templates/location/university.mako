<%inherit file="/base.mako" />
<%namespace file="/search/index.mako" import="search_form"/>
<%namespace file="/search/index.mako" import="search_results"/>


<%def name="title()">
  Ututi: ${c.location.title}
</%def>

<h2 class="underline">${c.location.title_short} ${_('department list')}</h2>
<%
   children = c.location.children
   l = len(children)
   children = [children[l/2:], children[:l/2]]
%>
<table style="margin-top: 25px;">
  <tr>
    %for group in children:
      <td style="width: 50%;">
        <ul class="u-list">
        %for department in group:
        <li><a href="${department.url()}" title="${department.title}">${department.title}</a> (${department.count()})</li>
        %endfor
        </ul>
      </td>
    %endfor
  </tr>
</table>


<h2 class="underline">${_('Search')}</h2>
${search_form(c.text, c.obj_type, c.location.hierarchy, parts=['obj_type', 'text'], target=c.location.url())}

%if c.searched:
  ${search_results(c.results)}

  %if c.user:
    %if c.obj_type == 'group':
    <div class="create_item">
      <span class="notice">${_('Did not find what you were looking for?')}</span>
      ${h.button_to(_('Create a new group'), url(controller='group', action='add'))}
      ${h.image('/images/details/icon_question.png', alt=_('Create your group, invite your classmates and use the mailing list, upload private group files'), class_='tooltip')|n}
    </div>
    %else:
    <div class="create_item">
      <span class="notice">${_('Did not find what you were looking for?')}</span>
      ${h.button_to(_('Create a new subject'), url(controller='subject', action='add'))}
      ${h.image('/images/details/icon_question.png',
                alt=_("Store all the subject's files and notes in one place."),
                class_='tooltip')|n}
    </div>
    %endif
  %endif
%endif
