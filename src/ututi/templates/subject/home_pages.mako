<%inherit file="/subject/home.mako" />
<%namespace file="/sections/content_snippets.mako" import="*"/>
<%namespace name="files" file="/sections/files.mako" />

<%def name="css()">
div.wiki-tekstas, div.wiki-tekstas-last {background-color: white;}
</%def>

%if c.subject.n_pages():
  <%self:rounded_block class_='portletGroupFiles' id="subject_pages">
  <div class="GroupFiles GroupFilesWiki">
    <%
       if h.check_crowds(['moderator']):
         pages = c.subject.pages
       else:
         pages = [page for page in c.subject.pages if not page.isDeleted()]
       count = len(pages)
    %>
    <h2 class="portletTitle bold">${_("Subject's Wiki Pages")} (${count})</h2>
    %if c.user:
    <span class="group-but">
        ${h.button_to(_('Create a wiki document'), url(controller='subjectpage', action='add', id=c.subject.subject_id, tags=c.subject.location_path),
                  method='GET')}
    </span>
    %endif
  </div>
  % if pages:
    ## show teacher notes before the rest (python sort is stable)
    <% pages = sorted(pages, lambda x, y: int(y.original_version.created.is_teacher) - \
                                                    int(x.original_version.created.is_teacher)) %>

    % for n, page in enumerate(pages):
      % if not page.isDeleted() or h.check_crowds(['moderator']):
       <% teacher_class = 'teacher-content' if page.original_version.created.is_teacher else '' %>
       <div class="${teacher_class} ${'wiki-tekstas' if n < count else 'wiki-tekstas-last'}">
         <p>
            %if page.original_version.created.is_teacher:
              ${tooltip(_("Teacher's material"), img='/img/icons/teacher-cap.png')}
            %endif
           <span class="orange bold"><a href="${page.url()}" title="${page.title}">${page.title}</a></span>
           <span class="grey verysmall"> ${h.fmt_dt(page.last_version.created_on)} </span>
           <span class="author verysmall"><a href="${page.last_version.created.url()}">${page.last_version.created.fullname}</a></span>
         </p>
         <p>
           ${h.ellipsis(page.last_version.plain_text, 250)}
         </p>
       </div>
      % endif
    % endfor
  % else:
    <br />
    <span class="notice">${_('The subject has no pages yet - create one!')}</span>
  % endif
  </%self:rounded_block>

%else:

    <div id="page-intro" ${"style='display: none'" if blank_subject else ''}>

  <%self:rounded_block class_='subject-intro-block' id="subject-intro-block-pages">
    <h2 style="margin-top: 5px">${_('Create wiki documents')}</h2>
    <p>
      ${_('Collecting course notes in Word? Writing things down on a computer during lectures? You can store your notes here, where they can be read and edited by your classmates.')}
    </p>
    <h2>${_('What can be a wiki document?')}</h2>
    <ul class="subject-intro-message">
      <li>${_('Shared course notes')}</li>
      <li>${_('Personal course notes written down during a lecture')}</li>
      <li>${_('Any text that you want to collaborate on with your classmates')}</li>
    </ul>

    <div style="margin-top: 10px; margin-left: 20px">
      ${h.button_to(_('Create a wiki document'), url(controller='subjectpage', action='add', id=c.subject.subject_id, tags=c.subject.location_path),
                method='GET')}
    </div>
  </%self:rounded_block>

</div>

%endif
