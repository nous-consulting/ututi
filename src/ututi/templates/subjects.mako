<%inherit file="/base.mako" />

<%def name="title()">
  Subjects
</%def>

<h1>${_('Subjects')}</h1>

%if c.subjects:
    <ol id="subject_list">
    %for subj in c.subjects:
         <li>
           <a href="${url(controller='subject', action='subject_home', id=subj.id, tags=subj.location_path)}" class="subject-link">${subj.title}</a>
         </li>
    %endfor
    </ul>
%endif
