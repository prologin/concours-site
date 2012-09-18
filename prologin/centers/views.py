# coding=utf-8
from django.template import Context, loader
from centers.models import Center
from django.http import HttpResponse
from geopy import geocoders
import json

def index(request):
	cities = [_['city'] for _ in Center.objects.filter(is_active=True).values('city').distinct()]
	t = loader.get_template('centers/index.html')
	c = Context({
		'cities': cities,
	})
	return HttpResponse(t.render(c))

def genjson(request, city):
	if city:
		centers = Center.objects.filter(is_active=True, city=city)
	else:
		centers = Center.objects.filter(is_active=True)
	centersList = []
	for center in centers:
		d = center.__dict__
		del d["_state"]
		d["lat"] = str(d["lat"])
		d["lng"] = str(d["lng"])
		centersList.append(d)
	return HttpResponse(json.dumps(centersList), mimetype='application/json')

def geocode(request):
	g = geocoders.Google()
	centers = Center.objects.filter(is_active=True)
	for center in centers:
		if center.lat == 0 and center.lng == 0:
			try:
				_, (lat, lng) = g.geocode("{0} {1}".format(center.address.encode('utf-8'), center.city))
				center.lat = lat
				center.lng = lng
				center.save()
			except:
				print(u'{0} est ambiguë'.format(center.address))
	return HttpResponse("OK")