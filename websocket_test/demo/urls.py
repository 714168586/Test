
from django.conf.urls import url,include
from django.contrib import admin
from demo.views import demo,echo_once

urlpatterns = [
    url(r'^$', echo_once ),
    url(r'^demo/$',demo),

]
