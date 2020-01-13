from hashlib import md5

from django import template
from django.utils.six.moves.urllib.parse import urlencode

register = template.Library()


@register.simple_tag
def get_gravatar(email, size=60, rating='g', default=None):
    """ Return url for a Gravatar. From Zinnia blog. """
    url = 'https://secure.gravatar.com/avatar/{0}.jpg'.format(
        md5(email.strip().lower().encode('utf-8')).hexdigest()
    )
    options = {'s': size, 'r': rating}
    if default:
        options['d'] = default

    url = '%s?%s' % (url, urlencode(options))
    return url.replace('&', '&amp;')


@register.simple_tag
def page_query(request, page_num):
    qs = request.GET.copy()
    qs['page'] = str(page_num)
    return qs.urlencode().replace('&', '&amp;')
