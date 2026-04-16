from markupsafe import Markup

from watcher.utils import deep_getattr

class TableColumn:
    """
    Given an instance of a model provide header and value text for html.
    """

    def __init__(self, header, attr, cast=None):
        self.header = header
        self.attr = attr
        self.cast = cast

    def valueof(self, instance):
        value = deep_getattr(instance, self.attr)
        if self.cast:
            value = self.cast(value)
        return value


class Table:

    def __init__(self, columns, model, row_endpoint=None):
        self.columns = columns
        self.model = model
        self.row_endpoint = row_endpoint


def render_object(obj, html=None):
    if html is None:
        html = []
    if isinstance(obj, dict):
        html.append('<dl>')
        for key, value in obj.items():
            html.append(f'<dt>{key}</dt>')
            html.append(f'<dd>{render_object(value, html=html)}</dd>')
        html.append('</dl>')
    elif isinstance(obj, list):
        html.append(f'<ul>')
        for item in obj:
            html.append(f'<li>{render_object(item, html=html)}</li>')
        html.append(f'</ul>')
    else:
        return str(obj)
    return Markup(''.join(html))

def yesno(value):
    if value is True:
        return Markup('<span class="boolean-yes">Yes</span>')
    else:
        return Markup('<span class="boolean-no">No</span>')

def unordered_list(iterable):
    """
    Return items in iterable as html <ul>.
    """
    html = ['<ul>']
    for item in iterable:
        html.append(f'<li>{item}</li>')
    html.append('</ul>')
    return Markup(''.join(html))
