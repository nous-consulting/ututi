<%inherit file="/base.mako" />

<%def name="title()">
  ${c.subject.title}
</%def>

<h1>${c.subject.title}</h1>

<div>
${c.subject.lecturer}
</div>

<h2>${_('Files')}</h2>

% for folder in c.subject.folders:
<ul>
  % if folder.title == '':
    % for file in folder:
  <li>
      ${file.title}
  </li>
    % endfor
  % else:
    % for file in folder:
    <li>
      ${folder.title}
      ${file.title}
    </li>
    % endfor
  % endif
</ul>
% endfor

<div id="subject_pages">
  <h2>${_('Pages')}</h2>

  % if c.subject.pages:
    <ul>
    % for page in c.subject.pages:
      <li>
        ${h.link_to(page.title, url(controller='subjectpage', page_id=page.id, id=c.subject.id, tags=c.subject.location_path))}
      </li>
    % endfor
    </ul>
  % endif
  ${h.link_to(_('Add page'), url(controller='subjectpage', action='add', id=c.subject.id, tags=c.subject.location_path))}
</div>
