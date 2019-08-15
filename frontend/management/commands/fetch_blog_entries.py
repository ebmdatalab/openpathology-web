import yaml
import os
import requests
import subprocess
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
            for page in pages:
                response = requests.get(page["url"])
                tree = html.fromstring(response.text)
                date = page["date"].strftime("%d %b, %Y")
                node = tree.xpath(page["xpath"])[0]
                cleaner = Cleaner(safe_attrs_only=False, safe_attrs=[])
                content = cleaner.clean_html(tostring(node, encoding="unicode"))
                content += "<hr><p><a href='{% url 'blog' %}'>Read more OpenPathology blogs</a></p>"
                summary = filters.truncatewords(node.text_content(), 35)
                content = (
                    "<h1>{title}</h1><small class='text-muted'>{date}</small>".format(
                        date=date, title=page["title"]
                    )
                    + content
                )

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
