<%inherit file="/portlets/base.mako"/>

<%def name="ututi_join_portlet()">
  <%self:portlet id="ututi_join_portlet">
    <%def name="header()">
      ${_('Join Ututi')}
    </%def>
      <form id="registration_form" method="post" action="${url('/register')}">
        %if c.hash:
          <input type="hidden" name="hash" value="${c.hash}"/>
        %endif
        %if c.came_from:
          <input type="hidden" name="came_from" value="${c.came_from}" />
        %endif
        <form:error name="fullname"/>
        <div class="form-field">
          <div class="input-line"><div>
            <input class="line" type="text" id="fullname" name="fullname" size="40"/>
          </div></div>
          <label for="fullname">${_('Full name')}</label>
        </div>
        <form:error name="email"/>
        <div class="form-field">
          <div class="input-line"><div>
            % if c.email:
              <input  type="text" id="email" name="email" size="40" value="${c.email}" disabled="disabled" class="line"/>
              <input  type="hidden" name="email" value="${c.email}" />
            % else:
              <input  type="text" id="email" name="email" size="40" class="line"/>
            % endif
          </div></div>
          <label for="email">${_('Email')}</label>
        </div>
        %if c.gg_enabled:
        <form:error name="gadugadu"/>
        <div class="form-field">
          <div class="input-line"><div>
              <input  type="text" id="gadugadu" name="gadugadu" size="40" class="line"/>
          </div></div>
          <label for="gadugadu">${_('Gadu gadu')}</label>
        </div>
        %else:
        <input type="hidden" id="gadugadu" name="gadugadu"/>
        %endif
        <form:error name="new_password"/>
        <div class="form-field">
          <div class="input-line"><div>
            <input class="line" type="password" id="new_password" name="new_password" size="40"/>
          </div></div>
          <label for="new_password">${_('Password')}</label>
        </div>
        <form:error name="repeat_password"/>
        <div class="form-field">
          <div class="input-line"><div>
            <input class="line" type="password" id="repeat_password" name="repeat_password" size="40"/>
          </div></div>
          <label for="repeat_password">${_('Repeat password')}</label>
        </div>
        <form:error name="agree"/>
        <div class="form-field" style="clear: right;">
          <label for="agree">${_('I agree to the ')} <a href="${url(controller='home', action='terms')}">${_('terms of use')}</a></label>
          <input type="checkbox" name="agree" value="true" style="float: right;"/>
        </div>
        <div class="form-field" style="clear: right; text-align: right; padding: 15px 0 5px;">
          <span class="btn-large">
            <input type="submit" value="${_('Register')}"/>
          </span>
        </div>
      </form>
  </%self:portlet>
</%def>

<%def name="ututi_join_section_portlet()">
  <%self:portlet id="ututi_join_section_portlet">
    <%def name="header()">
      ${_('Registration')}
    </%def>
      <form id="join_registration_form" method="post" action="${url(controller='home', action='register')}" class="fullForm">
        <fieldset>

        %if c.came_from:
          <input type="hidden" name="came_from" value="${c.came_from}" />
        %endif
        %if c.hash:
          <input type="hidden" name="hash" value="${c.hash}" />
        %endif

        ${h.input_line('fullname', _('Fullname'))}
         % if c.email:
          ${h.input_line('email', _('Email'), disabled="disabled", value=c.email)}
          <input  type="hidden" name="email" value="${c.email}" />
         % else:
           ${h.input_line('email', _('Email'))}
         % endif
        %if c.gg_enabled:
          ${h.input_line('gadugadu', _('Gadu gadu'))}
        %else:
         <input type="hidden" id="gadugadu" name="gadugadu"/>
        %endif

         ${h.input_psw('new_password', _('Password'))}
         ${h.input_psw('repeat_password', _('Repeat password'))}
        <form:error name="agree"/>
        <label id="agreeWithTOC"><input type="checkbox" name="agree" value="true"/>${_('I agree to the ')} <a href="" onclick="return false;">${_('terms of use')}</a></label>
        <div>
          ${h.input_submit(_('Join'))}
        </div>

        </fieldset>
      </form>
  </%self:portlet>
</%def>

<%def name="ututi_login_section_portlet()">
  <%self:portlet id="ututi_login_section_portlet">
    <%def name="header()">
    </%def>
      <form id="join_login_form" method="post" action="${url(controller='home', action='join_login')}" class="fullForm">
        %if c.came_from:
          <input type="hidden" name="came_from" value="${c.came_from}" />
        %endif
        %if c.login_error:
          <div class="error">${c.login_error}</div>
        %endif
        ${h.input_line('login_username', _('Your email address'), value=request.params.get('login'))}
        ${h.input_psw('login_password', _('Password'))}
        ${h.input_submit(_('Login'))}
      </form>

      <div id="federated-login-note" style="padding-top: 2em">
        ${_('Log in or register with your Google or Facebook account.')}
      </div>
      <div id="federated-login-buttons">
        <a href="${url(controller='home', action='google_register', came_from=c.came_from)}" id="google-button">
          ${h.image('/img/google-logo.gif', alt='Log in using Google', class_='google-login')}
        </a>
        <br />
        ## We rely here on the fact that Facebook has been configured
        ## by the login widget in the page header.
        <fb:login-button perms="email"
            onlogin="show_loading_message(); window.location = '${url(controller='home', action='facebook_login', came_from=c.came_from)}'"
         >Connect</fb:login-button>
      </div>

  </%self:portlet>
</%def>
