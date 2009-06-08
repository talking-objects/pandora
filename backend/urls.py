from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

'''
files/find
files/info
files/add
files/remove

movies/find
movies/get
movies/edit?movie_id...

subtitles/list?oshash
subtitles/get?oshash&language
subtitles/add?oshash&language
subtitles/remove?oshash&language
'''

urlpatterns = patterns('oxdata.api.views',
    (r'^files/find', 'find_files'),
    (r'^files/info', 'file_info'),
    (r'^files/add', 'add_file'),
    (r'^files/remove', 'remove_file'),
    (r'^subtitle/get', 'get_subtitle'),

    # Example:
    # (r'^oxdata/', include('oxdata.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/(.*)', admin.site.root),
)
