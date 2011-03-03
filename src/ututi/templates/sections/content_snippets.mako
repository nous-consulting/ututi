<%doc>
Snippets for rendering various content items, e.g. in search results.
</%doc>

<%def name="location_tag_link(tag)">
  <a class="tag" title="${tag.title}" href="${tag.url()}">
    ${tag.title}
  </a>
</%def>

<%def name="tag_link(tag)">
  %if c.user:
    <a class="tag" title="${tag.title}" href="${url(controller='profile', action='search', tags=', '.join(tag.hierarchy()))}">
      ${tag.title}
    </a>
  %else:
    <a class="tag" title="${tag.title}" href="${url(controller='search', action='index', tags=', '.join(tag.hierarchy()))}">
      ${tag.title}
    </a>
  %endif
</%def>

<%def name="item_tags(object, all=True)">
  <%
  any_tags = False
  for tag in object.tags:
    if tag.title:
      any_tags = True
  %>
  %if any_tags:
  <span class="item-tags">
    <% length = len(object.tags) %>
    %for n, tag in enumerate(object.tags):
      %if n != length - 1:
        ${tag_link(tag)},
      %else:
        ${tag_link(tag)}
      %endif
    %endfor
  </span>
  %endif
</%def>

<%def name="item_location(object)">
  %if object.location:
  <%
    hierarchy_len = len(object.location.hierarchy())
  %>
  <span class="location-tags">
  %for index, tag in enumerate(object.location.hierarchy(True)):
    <a href="${tag.url()}">${tag.title_short}</a>
    %if index != hierarchy_len - 1:
        |
    %endif
  %endfor
  </span>
  %endif
</%def>

<%def name="item_location_full(object)">
  %if object.location:
  <%
    hierarchy_len = len(object.location.hierarchy())
  %>
  <span class="location">
  %for index, tag in enumerate(object.location.hierarchy(True)):
    ${tag.title}
    %if index != hierarchy_len - 1:
        |
    %endif
  %endfor
  </span>
  %endif
</%def>

<%def name="generic(object)">
  <div class="search-item snippet-generic">
    <a href="${object.url()}" title="${object.title}" class="item-title larger bold">${object.title}</a>
    ${item_tags(object)}
  </div>
</%def>

<%def name="group(object)">
  <div class="search-item snippet-group">
    <a href="${object.url()}" title="${object.title}" class="item-title larger bold">${object.title}</a>
    <div class="description">
      ${object.description}
    </div>
    <div class="description">
      ${item_location(object)}
      %if object.tags:
       | ${item_tags(object)}
      %endif
    </div>
  </div>
</%def>

<%def name="file(object)">
  <div class="search-item snippet-file">
    <a href="${object.url()}" title="${object.title}" class="item-title larger bold">${object.title}</a>
    <div class="description">
      ${object.description}
    </div>
    <div class="description">
      ${item_location(object)}
      | <a class="verysmall" href="${object.parent.url()}">${object.parent.title}</a>
      %if object.parent.tags:
       | ${item_tags(object.parent)}
      %endif
    </div>
  </div>
</%def>

<%def name="subject(object)">
  <div class="search-item snippet-subject">
    %if c.user is not None and not c.user.watches(object):
      <div class="action-button">
        ${h.button_to(_('Follow'), object.url(action='watch'), class_='dark add')}
      </div>
    %endif
    <a href="${object.url()}" title="${object.title}" class="item-title">${object.title}</a>
    <div class="description">
      ${item_location(object)}
      % if object.teacher_repr:
       | ${object.teacher_repr}
      % endif
      %if object.tags:
       | ${item_tags(object)}
      %endif
    </div>
    <ul class="statistics medium-icon-list">
        <li class="icon-file">${len(object.files)}</li>
        <li class="icon-note">${len(object.pages)}</li>
        <li class="icon-group">${object.group_count()}</li>
        <li class="icon-user">${object.user_count()}</li>
    </ul>
  </div>
</%def>

<%def name="page(object)">
  <div class="search-item snippet-page">
    <a href="${object.url()}" title="${object.title}" class="item-title larger bold">${object.title}</a>
    <div class="description">
      ${h.ellipsis(object.last_version.plain_text, 250)}
    </div>
    <div class="description">
      ${item_location(object)}
      | <a class="verysmall" href="${object.subject[0].url()}">${object.subject[0].title}</a>
      %if object.tags:
       | ${item_tags(object)}
      %endif
    </div>
  </div>
</%def>

<%def name="page_extra(object)">
  ##page snippet with last edit and author info
  <div class="search-item snippet-page">
    % if object.deleted_on is not None:
      <span style="color: red; font-weight: bold">${_('[DELETED]')}</span>
    % endif
    <a href="${object.url()}" title="${object.title}" class="item-title larger bold">${object.title}</a>
    <span class="small" style="margin-left: 10px;">${h.fmt_dt(object.last_version.created_on)}</span>
    <a style="font-size: 0.9em;" href="${object.last_version.created.url()}">${object.last_version.created.fullname}</a>
    <div class="description">
      ${h.ellipsis(object.last_version.plain_text, 250)}
    </div>
    ${item_tags(object, all=False)}
  </div>
</%def>

<%def name="forum_post(object)">
  <div class="search-item snippet-forum_post">
    <a href="${object.url()}" title="${object.title}" class="item-title larger bold">${object.title}</a>
    <div class="description">
      ${h.ellipsis(object.message, 150)}
    </div>
    <div class="description">
      %if object.category.group:
        ${h.link_to(object.category.group.title, object.category.group.url())}
        | ${item_location(object.category.group)}
        %if object.tags:
         | ${item_tags(object.category.group)}
        %endif
      %else:
        ${h.link_to(object.category.title, object.category.url())}
      %endif
    </div>
  </div>
</%def>

<%def name="book(object)">
  <div class="search-item snippet-book">
    <a href="${object.url()}" title="${object.title}" class="item-title larger bold">${object.title}</a> (${_('Book')})
    <div class="description">
      ${h.ellipsis(object.description, 200)}
    </div>
    <div class="description">
      %if object.city:
          <span class="book-city-label">${_('City')}:</span>
          <span class="book-city-name"> ${object.city.name}</span>
          <br />
      %endif
      <span class="book-price-label">${_('Price')}:</span>
      <span class="book-price">
        ${object.price}
      </span>
    </div>
  </div>
</%def>


<%def name="tooltip(text, style=None, img=None)">
  <% if img is None: img = '/images/details/icon_question.png' %>
  ${h.image(img, alt=text, class_='tooltip', style=style)}
</%def>

<%def name="tabs()">
%if hasattr(c, 'tabs') and c.tabs:
<ul class="moduleMenu tabs" id="moduleMenu">
    %for tab in c.tabs:
      <li class="${'current' if tab['name'] == c.current_tab else ''}">
        <a href="${tab['link']}">${tab['title']}
            <span class="edge"></span>
        </a></li>
    %endfor
</ul>
%endif
</%def>
