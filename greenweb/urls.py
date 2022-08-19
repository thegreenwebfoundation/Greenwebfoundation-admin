"""Greenweb foundation URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/dev/topics/http/urls/
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

from django.conf import settings
from django.urls import path, include, reverse_lazy
from django.views.generic.base import RedirectView
from rest_framework.routers import DefaultRouter


from apps.greencheck.viewsets import (
    IPRangeViewSet,
    ASNViewSet,
    GreenDomainViewset,
    GreenDomainBatchView,
)

from apps.greencheck.swagger import TGWFSwaggerView

from apps.greencheck.api import legacy_views
from apps.greencheck.api import views as api_views


from apps.accounts.admin_site import greenweb_admin as admin
from apps.accounts.admin import LabelAutocompleteView

from apps.accounts import urls as accounts_urls
from rest_framework.authtoken import views

from apps.greencheck import urls as greencheck_urls


urlpatterns = []

router = DefaultRouter()
router.register(r"ip-ranges", IPRangeViewSet, basename="ip-range")
router.register(r"asns", ASNViewSet, basename="asn")

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]


urlpatterns += [
    # admin views
    path("", include(accounts_urls)),
    path("accounts/", include("django.contrib.auth.urls")),
    path(
        "green-urls",
        RedirectView.as_view(url=reverse_lazy("greenweb_admin:green_urls")),
        name="green_urls_redirect",
    ),
    path("admin/", admin.urls),
    path(
        "label-autocomplete",
        LabelAutocompleteView.as_view(),
        name="label-autocomplete",
    ),
    # API
    path("api/v3/", include(router.urls)),
    path(
        "api/v3/greencheck/",
        GreenDomainViewset.as_view({"get": "list"}),
        name="green-domain-list",
    ),
    path(
        "api/v3/greencheck/<url>",
        GreenDomainViewset.as_view({"get": "retrieve"}),
        name="green-domain-detail",
    ),
    path(
        "api/v3/batch/greencheck",
        GreenDomainBatchView.as_view(),
        name="green-domain-batch",
    ),
    path(
        "api/v3/ip-to-co2intensity/",
        api_views.IPCO2Intensity.as_view(),
        name="ip-to-co2intensity",
    ),
    path(
        "api/v3/ip-to-co2intensity/<ip_to_check>",
        api_views.IPCO2Intensity.as_view(),
        name="ip-to-co2intensity",
    ),
    path("api-token-auth/", views.obtain_auth_token, name="api-obtain-token"),
    path(
        "api-docs/",
        TGWFSwaggerView.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    # replicate the PHP API, at the same url, so we can also put
    # it behind the reverse proxy
    path(
        "greencheck/<url>",
        GreenDomainViewset.as_view({"get": "retrieve"}),
        name="green-domain-detail",
    ),
    path(
        "checks/latest/",
        legacy_views.latest_greenchecks,
        name="legacy-latest-greenchecks",
    ),
    path("data/directory/", legacy_views.directory, name="legacy-directory-listing",),
    path(
        "data/hostingprovider/<id>",
        legacy_views.directory_provider,
        name="legacy-directory-detail",
    ),
    path(
        "greencheckimage/<url>",
        legacy_views.legacy_greencheck_image,
        name="legacy-greencheck-image",
    ),
    path(
        "v2/greencheckmulti/<url_list>",
        legacy_views.greencheck_multi,
        name="legacy-greencheck-multi",
    ),
    path("stats/", include(greencheck_urls)),
]
