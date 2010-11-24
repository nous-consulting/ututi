<%inherit file="/books/base.mako" />

<%def name="book_information(book)">
<div class="book-information">
  <div class="book-cover">
  </div>
  <div class="book-textual-info">
    <h3 class="book-title">${book.title}</h3>
    <div class="book-cover">
      <img src="${url(controller='books', action='logo', id=book.id, width=150, height=200)}" alt="${_('Book cover')}" />
    </div>
    <div>
      ${_('Author')}: ${book.author}<br />
      ${h.ellipsis(book.description, 100)|n}<br />
      %if book.city:
          <span class="book-location-title">${_('City')}:</span>
          <span class="book-location-name"> ${book.city.name}</span>
          <br />
      %endif
      <span class="book-price-title">${_('Price')}:</span>
      <span class="book-location-name">
        %if book.price == 0:
        ${_('free')}
        %else:
        ${book.price} Lt
        %endif
      </span>
      <br />
      ${h.button_to(_("more"), url(controller="books", action="show", id=book.id))}
      %if c.user is book.owner:
      ${h.button_to(_("Edit"), url(controller="books", action="edit", id=book.id))}
      %endif
    </div>
  </div>
</div>
</%def>

<%def name="ubooks_advicer()">
<div id="what_is_ubooks">
  <h3>${_("U-Books - what's that?")}</h3>
  ${h.button_to(_("Add book"), url(controller="books", action="add"))}
  <ul class="ubooks_explanation">
    <li>${_("It's school books exchange / selling place.")}</li>
    <li>${_("It's place where you can get cheap stydy book.")}</li>
    <li>${_("It's place where you find new owner for you old good textbook.")}</li>
  </ul>
</div>
</%def>

<%self:ubooks_advicer />
<div>
%for book in c.books:
    ${book_information(book)}
%endfor
  <div id="pager">${c.books.pager(format='~3~') }</div>
</div>

