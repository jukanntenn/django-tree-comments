from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.contrib.sites.models import Site
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.syndication.views import Feed
from django.utils.translation import gettext as _

import tree_comments

if TYPE_CHECKING:
    from datetime import datetime

    from django.db.models import QuerySet
    from django.http.request import HttpRequest
    from django.http.response import HttpResponse

    _FeedBase = Feed[Any, Any]
else:
    _FeedBase = Feed


class LatestCommentFeed(_FeedBase):
    """Feed of latest comments on the current site."""

    site: Site

    def __call__(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        site = get_current_site(request)
        assert isinstance(site, Site)  # noqa: S101 -- type narrowing after get_current_site
        self.site = site
        return super().__call__(request, *args, **kwargs)

    def title(self) -> str:
        return _("%(site_name)s comments") % {"site_name": self.site.name}

    def link(self) -> str:
        return f"http://{self.site.domain}/"

    def description(self) -> str:
        return _("Latest comments on %(site_name)s") % {"site_name": self.site.name}

    def items(self) -> QuerySet[Any]:
        qs = tree_comments.get_comment_model()._default_manager.filter(
            site__pk=self.site.pk,
            is_public=True,
            is_removed=False,
        )
        return qs.order_by("-submit_date")[:40]

    def item_pubdate(self, item: Any) -> datetime | None:
        pubdate: datetime | None = item.submit_date
        return pubdate
