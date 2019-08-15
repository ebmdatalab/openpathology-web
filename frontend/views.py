from django.shortcuts import render
from django.db.models import Count
from django.views.generic import TemplateView

from frontend.models import Group
from frontend.models import Measure
from frontend.models import Practice
from frontend.models import chart_urls


def _get_filtered_practices(request):
    code_filter = request.GET.get("filter", None)
    if code_filter:
        return Practice.objects.filter_by_entity_code(code_filter)
    else:
        practices = Practice.objects.all()
    return practices


def measures(request):
    measures = Measure.objects.all()
    context = {"measures": measures}
    return render(request, "measures.html", context)


def measure(request, measure):
    # Initially this allows us to show all practices for one measure.
    # Longer term, it would be good to support:
    #  * group by practice, filter by CCG
    #  * Group by PCT, filter by CCG
    #  * Group by STP, no filter
    #
    # Via URLs like:
    #  * /liver_tests/?filter=ods/08H&group_by=practice
    #  * /liver_tests/?filter&group_by=lab
    measure = Measure.objects.get(pk=measure)
    practices = _get_filtered_practices(request)
    ods_codes_for_practices = [
        practice.codes.get(system="ods").code for practice in practices
    ]
    groups = Group.objects.annotate(Count("practice")).filter(practice__count__gt=0)
    for g in groups:
        g.active = str(g.codes.first()) == request.GET.get("filter", None)
    urls = measure.chart_urls(ods_practice_codes=ods_codes_for_practices)
    codes = [x.split("_")[1] for x in urls]
    urls_and_codes = [
        {"measure_id": None, "practice_code": "ods/{}".format(x[0]), "url": x[1]}
        for x in zip(codes, urls)
    ]
    context = {"urls_and_codes": urls_and_codes, "measure": measure, "groups": groups}
    return render(request, "measure.html", context)


def practice(request, practice):
    """Show all measures by practice
    """
    practice = Practice.objects.get_by_entity_code(practice)
    groups = Group.objects.annotate(Count("practice")).filter(practice=practice)
    urls = chart_urls(ods_practice_codes=[practice.ods_code().code])
    measures = [x.split("_")[0] for x in urls]
    urls_and_codes = [
        {"measure_id": x[0], "practice_code": None, "url": x[1]}
        for x in zip(measures, urls)
    ]
    context = {"urls_and_codes": urls_and_codes, "measure": None, "groups": groups}
    return render(request, "measure.html", context)


class DynamicTemplateView(TemplateView):
    def get_template_names(self):
        return ["blog/%s.html" % self.kwargs["template"]]
