# coding=utf-8
from django.template import Context, loader
from centers.models import Center
from django.http import HttpResponse
from geopy import geocoders
import json

def index(request):
	villes = [_['ville'] for _ in Center.objects.values('ville').distinct()]
	t = loader.get_template('centers/index.html')
	c = Context({
		'villes': villes,
	})
	return HttpResponse(t.render(c))

def genjson(request, ville):
	if ville:
		centers = Center.objects.filter(ville = ville)
	else:
		centers = Center.objects.all()
	centersList = []
	for center in centers:
		d = center.__dict__
		del d["_state"]
		d["lat"] = str(d["lat"])
		d["lng"] = str(d["lng"])
		centersList.append(d)
	return HttpResponse(json.dumps(centersList), mimetype = 'application/json')

def geocode(request):
	g = geocoders.Google()
	centers = Center.objects.all()
	for center in centers:
		if center.lat == 0 and center.lng == 0:
			_, (lat, lng) = g.geocode("{} {}".format(center.adresse.encode('utf-8'), center.ville))
			center.lat = lat
			center.lng = lng
			center.save()
	return HttpResponse("OK")