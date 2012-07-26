from django.views.generic.list_detail import object_detail
from contest.models import Contestant
from django.contrib.auth.models import User

def get_profile(request, object_id):
	return object_detail(
		request,
		object_id=object_id,
		queryset=User.objects,
		template_object_name='contestant',
		extra_context={'participations': Contestant.objects.filter(user=object_id)},
		template_name='contest/index.html'
	)
