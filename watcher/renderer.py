from markupsafe import Markup
from markupsafe import escape

def mailto(email_address):
    return Markup(f'<a href="mailto:{email_address}">{email_address}</a>')

def render_attrs(**kwargs):
    """
    Render html element attributes.
    """
    parts = []
    for k, v in kwargs.items():
        if v is True:
            parts.append(k)  # boolean attr
        elif v is False or v is None:
            continue
        else:
            parts.append(f'{k}="{escape(v)}"')
    return Markup(" ".join(parts))

def render_form(form):

    html = [form.hidden_tag()]

    for field in form:
        if field.type not in ('SubmitField', 'CSRFTokenField'):
            html.append('<fieldset class="group">')
            html.append(str(field.label))
            html.append(str(field))
            if field.errors:
                for error in field.errors:
                    html.append(f'<small class="error">{ escape(error) }</small>')
            html.append('</fieldset>')

    for field in form:
        if field.type == 'SubmitField':
            html.append(str(field))

    return Markup(''.join(html))

def init_app(app):
    """
    Add jinja template filters and globals.
    """
    app.jinja_env.globals['render_form'] = render_form
