"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
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

# =====================================================================
# File: config/urls.py
# Purpose: The site's main address book. Each line hands a group of
#          addresses over to one app's own urls.py.
# Contains:
#   admin/                   -> Django admin site
#   (root) accounts.urls     -> landing page, register, login, logout
#   (root) destinations.urls -> destination search, map and weather API
# THIS IS A SHARED FILE PLEASE DON'T REMOVE OTHERS CODE
# =====================================================================

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),       #Nafisa
    path('', include('destinations.urls')),   #Raidah's feature
]