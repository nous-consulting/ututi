<%inherit file="/books/base.mako" />
<%namespace name="books" file="/books/add.mako" />

<%def name = "book_attribute(label, value, **attrs)">
<%
   if not attrs.has_key('is_value_none'):
       attrs['is_value_none'] = value == None
   endif

   if not attrs.has_key('none_value_text'):
       attrs['none_value_text'] = '-'
   endif

   if not attrs.has_key('class_'):
       attrs['class_'] = ''
   endif
%>
<div class="book-attribute ${attrs['class_']}">
  <span class="book-attribute-label">${label}:</span>
  <span class="book-attribute-value">
    %if value:
    ${value}
    %else:
    ${attrs['none_value_text']}
    %endif
  </span>
</div>
</%def>

${h.link_to(_('Back to catalog'), url(controller="books", action="index"), class_="back-link")}
<h2 class="title">${c.book.title}</h2>
<div class="book-cover">
  <img src="${url(controller='books', action='logo', id=c.book.id, width=150, height=200)}" alt="${_('Book cover')}" />
</div>
<div class="books-description">${c.book.description}</div>
${book_attribute(_('Author'), c.book.author)}
${book_attribute(_('Book department'),_(c.book.department.name))}
%if c.book.department.name != 'other':
${book_attribute(_('Book type'), c.book.type.name)}
%endif
%if c.book.department.name == 'school':
${_('School grade')}: ${c.book.school_grade.name}
%endif
%if c.book.department.name != 'other':
${book_attribute(_('Science type'), c.book.science_type.name)}
%endif
${book_attribute(_('City'), c.book.city.name)}
${book_attribute(_('Price'), c.book.price, class_="book-price")}
<div class="owner-information">
  <p>${_("Owner information")}</p>
  <div class="profile ${'bottomLine' if c.book.created.description or c.book.created.site_url else ''}">
    <div class="floatleft avatar">
      %if c.book.created.logo is not None:
      <img src="${url(controller='user', action='logo', id=c.book.created.id, width=70, height=70)}" alt="logo" />
      %else:
      ${h.image('/img/profile-avatar.png', alt='logo')|n}\
      %endif
    </div>
    <div class="floatleft personal-data">
      <div><h2>${c.book.created.fullname}</h2></div>
      <div><a href="mailto:${c.book.created.emails[0].email}">${c.book.created.emails[0].email}</a></div>
      %if c.book.created.phone_number is not None and c.book.created.phone_number != "":
      <div class="user-phone-number">
        ${_('Phone')}: ${c.book.created.phone_number}
      </div>
    %endif
    <div class="medals" id="user-medals">
      %for medal in c.book.created.all_medals():
      ${medal.img_tag()}
      %endfor
    </div>
    <div class="private-message-container">
      <form action="${url(controller='books', action='private_message')}">
        <input type="hidden" name="book_id" value="${c.book.id}" />
        ${h.input_area("message", "Message")}
        ${h.input_submit("Send message")}
      </form>
    </div>
    <div class="clear"></div>
  </div>
</div>
