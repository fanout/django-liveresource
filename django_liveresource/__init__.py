import json
from gripcontrol import Channel
from django.http import HttpResponse, HttpResponseBadRequest
from django_grip import set_hold_longpoll, publish

# FIXME: prev_id on channels

WAIT_MAX = 60 * 10

# hijack requests and be able to make internal requests
class LiveResourceMiddleware(object):
	def process_view(self, request, view_func, view_args, view_kwargs):
		# require grip middleware
		assert hasattr(request, 'grip_proxied'), 'GripMiddleware must run before LiveResourceMiddleware'

		# parse wait header
		wait = request.META.get('HTTP_WAIT')
		if wait is not None:
			try:
				wait = int(wait)
			except:
				return HttpResponseBadRequest('Invalid Wait header specified.\n')

			del request.META['HTTP_WAIT']
			if wait < 1:
				wait = None
			elif wait > WAIT_MAX:
				wait = WAIT_MAX

		resp = view_func(*view_args, **view_kwargs)

		if wait:
			if not request.grip_proxied:
				return HttpResponse('Error: Realtime request not supported. Set up Pushpin or Fanout.\n', status=501)

			if hasattr(resp, 'multi_uris'):
				empty = True # TODO: check resp to make sure it is empty
				if empty:
					# FIXME: channel schema
					channels = list()
					for uri in resp.multi_uris:
						channels.append(Channel('multi-' + uri))
					set_hold_longpoll(resp, channels)
			else:
				changes = None # TODO: check resp for Link rel=changes
				empty = False
				if changes:
					items = json.loads(resp.content)
					empty = (len(items) == 0)

				if resp.status_code == 304 or (resp.status_code == 200 and empty):
					# FIXME: channel schema. use different channel for object vs collection
					set_hold_longpoll(resp, Channel(request.path))

		return resp

def updated(uri, prev_etag=None, prev_changes_link=None, query=None, get_items=None):
	# TODO: use internal request to retrieve changes, if any
	# TODO: publish on relevant channels, with HttpResponseFormat and WebSocketMessageFormat
	pass
