import os

from django.conf.urls import include, url
import django.views.static

from django.contrib import admin
admin.autodiscover()

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^knowledge/', include('knowledge.urls')),
    url(r'^static/(?P<path>.*)$', django.views.static.serve,
        {'document_root': os.path.join(
                os.path.dirname(__file__), '../knowledge/static'
            ).replace('\\','/')}),
]
