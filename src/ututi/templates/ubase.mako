<%namespace file="/sections/messages.mako" import="*"/>

<%
c.new_design = True
%>

<%def name="title()">
${_('student information online')}
</%def>

<%def name="head_tags()">
</%def>

<%def name="body_class()">
%if c.user is None:
    noMenu
%endif
</%def>

<%def name="anonymous_header()">
<ul id="socialLinks">
  <li id="blogLink"><a href="${_('ututi_blog_url')}">${_(u'„Ututi“ blog')}</a></li>
  <li id="twitterLink"><a href="${_('ututi_twitter_url')}">${_(u'„Ututi“ on twitter')}</a></li>
  <li id="facebookLink"><a href="${_('ututi_facebook_url')}">${_(u'„Ututi“ on Facebook')}</a></li>
</ul>
<form method="post" id="loginForm" action="${url('/login')}">
  <fieldset>
    <input type="hidden" name="came_from" value="${request.params.get('came_from', request.url)}" />
    <legend class="a11y">${_('Join!')}</legend>
    <label class="textField"><span class="overlay">${_('Email')}:</span><input type="text" name="login" /><span class="edge"></span></label>
    <label class="textField"><span class="overlay">${_('Password')}</span><input type="password" name="password" /><span class="edge"></span></label>
    <button class="btn" type="submit" value="${_('Login')}"><span>${_('Login')}</span></button><br />
    <label id="rememberMe"><input type="checkbox"> ${_('remember me')}</label><br />
    <a href="${url(controller='home', action='pswrecovery')}">${_('forgotten password?')}</a>
  </fieldset>
  <script type="text/javascript">
    $(window).load(function() {
    $(".textField .overlay").labelOver('over');
    });
  </script>

</form>
</%def>

<%def name="loggedin_header(user)">
<form id="searchForm" action="${url(controller='profile', action='search')}">
	<fieldset>
		<legend class="a11y">${_('Search')}</legend>
		<label class="textField">
          <span class="a11y">${_('Search text')}</span>
          <input type="text" name="text"/>
          <span class="edge"></span>
        </label>
        ${h.input_submit(_('search_'))}
	</fieldset>
</form>
<p class="a11y">${_('Main menu')}</p>
<ul id="mainMenu">
	<li><a href="${url(controller='profile', action='home')}">${_('Home')}</a></li>
	<li><a href="${url(controller='profile', action='browse')}">${_('Browse')}</a></li>
	<li class="expandable XXXdisabled"><a href="">${_('Groups')}</a></li>
	<li><a href="${url(controller='community', action='index')}">${_('Community')}</a></li>
</ul>
<p class="a11y">${_('User menu')}</p>
<ul id="userMenu">
	<li id="checkMail" class="XXXdisabled"><a href="">${_('inbox (%d)') % 4}</a></li>

	<li id="profileInfo">
		<a href="${url(controller='profile', action='edit')}">${c.user.fullname}</a>
	</li>
	<li id="logout"><a href="${url(controller='home', action='logout')}">${_('exit')}</a></li>
</ul>

</%def>

<%def name="flash_messages()">
<div id="flash-messages">
  % if c.serve_file:
  <iframe style="display: none;" src="${c.serve_file.url()}"> </iframe>
  % endif

  <% messages = h.flash.pop_messages() %>
  % for message in messages:
  <div class="flash-message"><span class="close-link hide-parent">${_('Close')}</span><span>${h.literal(unicode(message))}</span></div>
  % endfor
  ${invitation_messages(c.user)}
  ${request_messages(c.user)}
  ${confirmation_messages(c.user)}
</div>
</%def>

<!DOCTYPE HTML>
<html xml:lang="lt" xmlns="http://www.w3.org/1999/xhtml" lang="lt">
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">

    <script type="text/javascript">
      var lang = '${c.lang}';
    </script>
    ${h.javascript_link('/javascript/jquery-1.3.2.min.js')}
    ${h.javascript_link('/javascript/ajaxupload.3.5.js')}
    ${h.javascript_link('/javascript/jquery.qtip.min.js')}
    ${h.javascript_link('/javascript/tooltips.js')}
    ${h.stylesheet_link('/newstyle.css')}
    ${h.stylesheet_link('/localstyle.css')}
    ${h.javascript_link('/javascript/expand.js')}
    ${h.javascript_link('/javascript/hide_parent.js')}
    ${h.javascript_link('/javascript/forms.js')}
    ${self.head_tags()}
    <title>
      ${self.title()} - ${_('UTUTI')}
    </title>
    <script type="text/javascript">
      var _gaq = _gaq || [];
      _gaq.push(['_setAccount', '${c.google_tracker}']);
      _gaq.push(['_trackPageview']);

      (function() {
      var ga = document.createElement('script');
      ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
      ga.setAttribute('async', 'true');
      document.documentElement.firstChild.appendChild(ga);
      })();

    </script>
  </head>
  <body class="${self.body_class()}">
    <div id="wrap"><div id="widthLimiter">
      <%
         if c.user:
             u_url = url(controller='profile', action='browse')
             track_event = h.trackEvent(None, 'user_search', 'logo')
         else:
             u_url = url('/')
             track_event = ''
      %>
      <h1 id="siteName"><a href="${u_url}">Ututi</a></h1>
      %if c.user is None:
        ${self.anonymous_header()}
      %else:
        ${self.loggedin_header(c.user)}
      %endif

      ${self.flash_messages()}
      ${next.body()}
      </div>
      <div class="push"></div>
    </div>

    <div id="footer">
      <%
         nofollow = h.literal(request.path != '/' and  'rel="nofollow"' or '')
      %>
      <p>Copyright © <a href="${_('ututi_link')}">${_(u'UAB „UTUTI“')}</a></p>
      <ul>
        <li><a ${nofollow} href="${url(controller='home', action='about')}">${_('About ututi')}</a></li>
        <li><a ${nofollow} href="${_('ututi_blog_url')}">${_('U-blog')}</a></li>
        <li><a ${nofollow} href="${url(controller='home', action='terms')}">${_('Terms of use')}</a></li></ul>
    </div>

  </body>
</html>
