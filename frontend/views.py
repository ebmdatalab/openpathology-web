from django.shortcuts import render

from frontend.models import Measure
from frontend.models import Practice


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
    urls_with_practices = {}
    ods_codes_for_practices = [
        practice.codes.get(system="ods").code for practice in practices
    ]
    urls = measure.chart_urls_for_all(ods_practice_codes=ods_codes_for_practices)
    context = {"urls": urls, "measure": measure}
    return render(request, "measure.html", context)
