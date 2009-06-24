<%def name="title()">
${_('student information online')}
</%def>

<%def name="head_tags()">
</%def>

<%def name="personal_block()">
</%def>

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
  <head>
    <script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jquery/1.3.2/jquery.min.js"></script>
    ${h.stylesheet_link('/stylesheets/style.css')|n}
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    ${self.head_tags()}
    <title>
      ${_('UTUTI')} - ${self.title()}
    </title>
  </head>

  <body>
    <div id="container">
      <div id="header">
        <div id="personal-box" class="rounded-block">
          <div class="rounding rounded-header">
            <div class="rounded-right"></div>
          </div>
          <div class="content">
            ${self.personal_block()}
          </div>
          <div class="rounding rounded-footer">
            <div class="rounded-right"></div>
          </div>
        </div>

        %if c.breadcrumbs:
        <a href="/" title="home" id="ulogo">
          ${h.image('/images/logo_small.png', alt='logo')|n}
        </a>
        <div id="breadcrumbs">
          <%
             first = false
          %>
          %for breadcrumb in c.breadcrumbs:
          <a class="breadcrumb" title="${breadcrumb.get('title')}" href="${breadcrumb.get('link')}">
             ${breadcrumb.get('title') | h.ellipsis}
          </a>
          %if not first:
          <%
             first = true
          %>
          <img src="bullet_orange.png"/>
          %endif
          %endfor
        </div>
        %else:
        <a href="/" title="home" id="ulogo">
          ${h.image('/images/logo.png', alt='logo')|n}
        </a>
        %endif

        <div id="content-top">
          <div></div>
        </div>
      </div>

      <div id="content">
        <div class="inside" id="page-content">
          ${self.body()}
        </div>

      </div>

      <div id="footer">
        <div id="content-bottom">
          <div></div>
        </div>

        Copyright <a href="#">UAB „Nous“</a>
        <div id="footer-links">
          <a href="#">aaaaa</a> |
          <a href="#">aaasdfasdaa</a> |
          <a href="#">aaa dasfaa</a>
        </div>

      </div>
    </div>

  </body>
</html>
