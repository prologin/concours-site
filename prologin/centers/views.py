from django.http import JsonResponse
from django.shortcuts import render
import centers.models


def center_map(request):
    center_list = centers.models.Center.objects.filter(
        type=centers.models.Center.CenterType.centre.value, is_active=True)
    return render(request, "centers/map.html", {'centers': center_list})


def center_list_json(request, city=None):
    center_qs = centers.models.Center.objects.filter(is_active=True)
    if city:
        center_qs = center_qs.filter(city__icontains=city)
    center_list = [{'name': c.name, 'lat': c.lat, 'lng': c.lng} for c in center_qs]
    return JsonResponse(center_list, safe=False)
