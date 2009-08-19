import re
"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to templates as 'h'.
"""
# Import helpers as desired, or define your own, ie:
#from webhelpers.html.tags import checkbox, password
from routes import url_for
from webhelpers.html.tags import stylesheet_link, javascript_link, image, link_to

from webhelpers.html import HTML
from webhelpers.html.tags import convert_boolean_attrs

from webhelpers.pylonslib import Flash as _Flash
flash = _Flash()


def button_to(name, url='', **html_options):
    """Generate a form containing a sole button that submits to
    ``url``. 
    
    Use this method instead of ``link_to`` for actions that do not have
    the safe HTTP GET semantics implied by using a hypertext link.
    
    The parameters are the same as for ``link_to``.  Any 
    ``html_options`` that you pass will be applied to the inner
    ``input`` element. In particular, pass
    
        disabled = True/False
    
    as part of ``html_options`` to control whether the button is
    disabled.  The generated form element is given the class
    'button-to', to which you can attach CSS styles for display
    purposes.
    
    The submit button itself will be displayed as an image if you 
    provide both ``type`` and ``src`` as followed:

         type='image', src='icon_delete.gif'

    The ``src`` path should be the exact URL desired.  A previous version of
    this helper added magical prefixes but this is no longer the case.

    Example 1::
    
        # inside of controller for "feeds"
        >> button_to("Edit", url(action='edit', id=3))
        <form method="POST" action="/feeds/edit/3" class="button-to">
        <div><input value="Edit" type="submit" /></div>
        </form>
    
    Example 2::
    
        >> button_to("Destroy", url(action='destroy', id=3), 
        .. method='DELETE')
        <form method="POST" action="/feeds/destroy/3" 
         class="button-to">
        <div>
            <input type="hidden" name="_method" value="DELETE" />
            <input value="Destroy" type="submit" />
        </div>
        </form>

    Example 3::

        # Button as an image.
        >> button_to("Edit", url(action='edit', id=3), type='image', 
        .. src='icon_delete.gif')
        <form method="POST" action="/feeds/edit/3" class="button-to">
        <div><input alt="Edit" src="/images/icon_delete.gif"
         type="image" value="Edit" /></div>
        </form>
    
    .. note::
        This method generates HTML code that represents a form. Forms
        are "block" content, which means that you should not try to
        insert them into your HTML where only inline content is
        expected. For example, you can legally insert a form inside of
        a ``div`` or ``td`` element or in between ``p`` elements, but
        not in the middle of a run of text, nor can you place a form
        within another form.
        (Bottom line: Always validate your HTML before going public.)
    
    """
    if html_options:
        convert_boolean_attrs(html_options, ['disabled'])
    
    method_tag = ''
    method = html_options.pop('method', '')
    if method.upper() in ['PUT', 'DELETE']:
        method_tag = HTML.input(
            type='hidden', id='_method', name_='_method', value=method)
    
    form_method = (method.upper() == 'GET' and method) or 'POST'
    
    url, name = url, name or url
    
    submit_type = html_options.get('type')
    img_source = html_options.get('src')
    if submit_type == 'image' and img_source:
        html_options["value"] = name
        html_options.setdefault("alt", name)
    else:
        html_options["type"] = "submit"
        html_options["value"] = name
    
    return HTML.form(method=form_method, action=url, class_="button-to",
                     c=[HTML.div(method_tag, HTML.span(HTML.input(**html_options), class_="btn"))])


def get_urls(text):
    urls = re.findall("http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",text)
    return urls


def ellipsis(text, max=20):
    if len(text) > max:
        return text[0:max-3] + '...'
    else:
        return text


def selected_item(list):
    for item in list:
        if item.get('selected', False):
            return item
