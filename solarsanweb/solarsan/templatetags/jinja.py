from django import template
from coffin import shortcuts as jinja_shortcuts

register = template.Library()

class JinjaInclude(template.Node):
    def __init__(self, filename):
        self.filename = filename

    def render(self, context):
        return jinja_shortcuts.render_to_string(self.filename, context)

@register.tag
def jinja_include(parser, token):
    bits = token.contents.split()

    '''''Check if a filename was given'''
    if len(bits) != 2:
        raise template.TemplateSyntaxError('%r tag requires the name of the '
            'template to be included included ' % bits[0])
    filename = bits[1]

    '''''Remove quotes if used'''
    if filename[0] in ('"', "'") and filename[-1] == filename[0]:
        filename = bits[1:-1]

    return JinjaInclude(filename)



