<%inherit file="/user/teacher_base.mako" />

<div class="section events">
  <div class="title">${_("Teacher's activity:")}</div>
  %if c.events:
    <div class="wall">
      ${wall.wall_entries(c.events)}
    </div>
  %else:
    ${_("No activity yet.")}
  %endif
</div>
