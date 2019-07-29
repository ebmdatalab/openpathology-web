from django.shortcuts import render
from django.db.models import Count
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
    context = {"urls": urls, "measure": measure, "groups": groups}
    return render(request, "measure.html", context)


def practice(request, practice):
    """Show all measures by practice
    """
    practice = Practice.objects.get(pk=practice)
    groups = Group.objects.annotate(Count("practice")).filter(practice=practice)
    urls = chart_urls(ods_practice_codes=[practice.ods_code().code])
    context = {"urls": urls, "measure": None, "groups": groups}
    return render(request, "measure.html", context)
