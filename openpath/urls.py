"""openpath URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView

from frontend import views


urlpatterns = [
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path("blog/", TemplateView.as_view(template_name="blog.html"), name="blog"),
    path("blog/<slug:template>", views.DynamicTemplateView.as_view(), name="blog_page"),
    path("measures/", views.measures, name="measures"),
    path("measure/<slug:measure>", views.measure, name="measure"),
    path("practice/<path:practice>", views.practice, name="practice"),
    path("about/", TemplateView.as_view(template_name="about.html"), name="about"),
    path(
        "get_involved/",
        TemplateView.as_view(template_name="get_involved.html"),
        name="get_involved",
    ),
    path(
        "data_format/",
        TemplateView.as_view(template_name="data_format.html"),
        name="data_format",
    ),
    path("api/", RedirectView.as_view(pattern_name="data_format"), name="api"),
    path("admin/", admin.site.urls),
]
