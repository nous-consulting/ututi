<%inherit file="/ubase.mako" />

<%def name="body_class()">registration</%def>
<%def name="pagetitle()">${_("Registration")}</%def>

<%def name="css()">
  ${parent.css()}
  #registration-page-container {
    width: 845px !important;
    margin: auto;
  }
  #registration-page-container h1 {
    border-bottom: 1px solid #ff9900;
  }
  button.next {
    margin-top: 20px;
  }
  ul#registration-steps {
    width: 845px !important;
    height: 40px !important;
    background: url('/img/registration_steps_bg.png') no-repeat top center;
    list-style: none;
  }
  ul#registration-steps li {
    width: 211px !important;
    height: 35px !important;
    overflow: hidden;
    float: left;
    margin-top: 5px;
    text-align: center;
  }
  ul#registration-steps li span {
    display: block;
  }
  ul#registration-steps li span.step-number {
    font-weight: bold;
  }
  ul#registration-steps li span.step-title {
    font-size: 10px;
  }
</%def>

<div id="registration-page-container">

  %if hasattr(c, 'steps') and hasattr(c, 'active_step') and c.active_step:
  <ul id="registration-steps">
    %for n, step in enumerate(c.steps, 1):
      <% id, title = step %>
      %if id == c.active_step:
      <li class="active">
      %else:
      <li>
      %endif
        <span class="step-number">${_("Step %(step_num)s") % dict(step_num=n)}</span>
        <span class="step-title">${title}</span>
      </li>
    %endfor
  </ul>
  %endif

  <h1 class="page-title registration">${self.pagetitle()}</h1>

  ${next.body()}

</div>
