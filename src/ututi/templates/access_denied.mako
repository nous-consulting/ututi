<%inherit file="/base.mako" />

<%def name="head_tags()">
${parent.head_tags()}
</%def>

<h1>${_('Permission denied!')}</h1>

<img src="${url('/images/nope.png')}" />

<div>
${_('You do not have the rights to see this page, or perform this action. Go back or go to the search page please.')}
</div>

% if request.referrer.startswith(url("/", qualified=True)):
    <a href="#" onclick="javascript: history.go(-1); return false;">go back</a>
% else:
    <a href="${url(controller='search')}">go find something else</a>
% endif
