${subject}

%for section in sections:
${section['title']}

%for event in section['events']:
- ${event['text_item']}
%endfor
%endfor

${_('If you want to stop getting these emails - you can change your subscription settings in your watched subject page (%(url)s).') % dict(
    url=url(controller='profile', action='subjects', qualified=True)) }
