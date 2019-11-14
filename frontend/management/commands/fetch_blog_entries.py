import yaml
import os
import re
import requests
import subprocess
from urllib.parse import urlparse
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from lxml import html
from lxml.html.clean import Cleaner
from lxml.html import tostring
from django.template import defaultfilters as filters
from django.conf import settings

VANILLA_TEMPLATE = """{{% extends "_base.html" %}}
{{% load static %}}
{{% block content %}}
{content}
{{% endblock %}}
"""

BLOG_LINK_TEMPLATE = '<li class="nav-item"><h3><a href="/blog/{url}">{title}</a></h3><small class="text-muted">{date}</small><p>{summary} <a href="{url}">[Read More...]</a></p></li>'


def make_internal_link_replacements(pages):
    """Internal links in the source blogs may have different URLs from our
    imported links. For example, in a source blog we may link to
    `/myblog/a.html`, but that link target in our destination blog
    should be `/a.html`. Build an array of regex replacements to
    rewrite internal links so they work in the destination blog.

    """
    replacements = []
    for page in pages:
        from_path = urlparse(page["url"]).path
        if from_path[-1] == "/":
            from_path = from_path[:-1]
        from_regex = r"(href=.).*{}/?(\b)".format(from_path)
        replacements.append((from_regex, r"\1/{}\2".format(page["slug"])))
    return replacements


class Command(BaseCommand):
    """Fetches a content from a list of URLs and saves them as templates in a blog folder
    """

    args = ""
    help = __doc__

    def handle(self, *args, **options):
        this_dir = os.path.dirname(os.path.abspath(__file__))
        template_dir = os.path.join(settings.BASE_DIR, "frontend", "templates")
        blog_dir = os.path.join(template_dir, "blog")
        os.makedirs(blog_dir, exist_ok=True)
        blog_entries_yaml_path = os.path.join(this_dir, "blog_entries.yaml")
        blog_index = []
        with open(blog_entries_yaml_path) as f:
            pages = sorted(
                yaml.load_all(f, Loader=yaml.FullLoader),
                key=lambda x: x["date"],
                reverse=True,
            )
            link_replacements = make_internal_link_replacements(pages)
            for page in pages:
                response = requests.get(page["url"])
                tree = html.fromstring(response.text)
                date = page["date"].strftime("%d %b, %Y")
                node = tree.xpath(page["xpath"])[0]
                cleaner = Cleaner(safe_attrs_only=False, safe_attrs=[])
                content = cleaner.clean_html(tostring(node, encoding="unicode"))
                for from_regex, to in link_replacements:
                    content = re.sub(from_regex, to, content)
                content += "<hr><p><a href='{% url 'blog' %}'>Read more OpenPathology blogs</a></p>"
                summary = filters.truncatewords(node.text_content(), 35)
                content = (
                    "<h1>{title}</h1><small class='text-muted'>{date}</small>".format(
                        date=date, title=page["title"]
                    )
                    + content
                )
                # Replace any links in the content
                blog_index.append(
                    BLOG_LINK_TEMPLATE.format(
                        url=page["slug"],
                        title=page["title"],
                        date=date,
                        summary=summary,
                    )
                )
                with open(
                    os.path.join(blog_dir, page["slug"] + ".html"), "w"
                ) as blog_file:
                    blog_file.write(VANILLA_TEMPLATE.format(content=content))
            with open(os.path.join(template_dir, "blog.html"), "w") as blog_index_file:
                content = (
                    "<h1>Latest blogs</h1>"
                    + "<ul class='nav'>"
                    + "\n".join(blog_index)
                    + "</ul>"
                )
                blog_index_file.write(VANILLA_TEMPLATE.format(content=content))
        print(
            subprocess.check_output(
                ["git", "status", "-s", "--", "frontend/templates/blog"]
            ).decode("ascii")
        )
        print("Finished. Now commit any new content listed above, and deploy")
