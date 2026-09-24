import re

from markupsafe import Markup
from flask import request
from flask import url_for

class NavLink:

    def __init__(self, text, endpoint, pattern):
        self.text = text
        self.endpoint = endpoint
        self.pattern = pattern

    def is_current(self):
        return re.match(request.endpoint, self.pattern)

    def render(self):
        html = f'<a href="{url_for(self.endpoint)}"'
        if self.is_current:
            html += f' aria-current="page"'
        html += f'>{self.text}</a>'

        return Markup(html)
