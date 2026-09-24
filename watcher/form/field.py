from markupsafe import Markup
from wtforms import Field

class ElementWidget:

    def __init__(self, tagname):
        self.tagname = tagname

    def __call__(self, field, **kwargs):
        return Markup(f'<{self.tagname}>{field.data}</{self.tagname}>')


class DisplayField(Field):
    widget = ElementWidget('div')

    def _value(self):
        if self.data is not None:
            return str(self.data)
        else:
            return ''
