from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    
    url(r'^$', 'conector.views.home', name='home'),
    url(r'^producto/(?P<id>\d+)/$', 'conector.views.producto', name='producto'),
    url(r'^productos/$', 'conector.views.productos', name='productos'),
    url(r'^crear_productos/$', 'conector.views.crear_producto', name='crear'),
    
    url(r'^abrir/(?P<id>\d+)/$', 'conector.views.abrir', name='abrir'),
    url(r'^procesar/(?P<id>\d+)/$', 'conector.views.procesar', name='procesar'),
    url(r'^finalizar/(?P<id>\d+)/$', 'conector.views.finalizar', name='finalizar'),
    # url(r'^algamarapp/', include('algamarapp.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
