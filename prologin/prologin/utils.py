from django.template import VariableDoesNotExist, Variable
from django.core.urlresolvers import reverse
from django.utils.html import escape
import unicodedata
import string
import re

def get_slug(name):
    name = unicodedata.normalize('NFKD', name.lower())
    name = ''.join(x for x in name if x in string.ascii_letters + string.digits + ' _-')
    name = re.sub(r'[^a-z0-9\-]', '_', name)
    return name

def real_value(var, context):
    """Return the real value based on the context."""
    if var is None:
        return None
    try:
        if not isinstance(var, Variable):
            var = Variable(var)
        real_var = var.resolve(context)
    except (VariableDoesNotExist):
        real_var = str(var)
    return escape(real_var)
