from urlparse import urlparse
import json
import django.test.client
from gripcontrol import Channel
from django.http import HttpResponse, HttpResponseBadRequest
from django_grip import set_hold_longpoll, publish

# FIXME: prev_id on channels

WAIT_MAX = 60 * 5

# TODO: @live decorator

# GET request only. meta must contain headers using "HTTP_{header.upper}" format
def internal_request(path, meta):
	client = django.test.client.Client()
	kwargs = dict()
	for k, v in meta.iteritems():
		if k.startswith('HTTP_'):
			kwargs[k] = v
	kwargs['HTTP_INTERNAL'] = '1'
	return client.get(path, {}, **kwargs)

def canonical_uri(uri):
	result = urlparse(uri)
	return result.path

def parse_header_params(value):
	parts = value.split(';')
	first = parts.pop(0)
	params = dict()
	for part in parts:
		k, v = part.lstrip().split('=', 1)
		params[k] = v
	return (first, params)

def is_response_empty(response):
	pass

# modes: value, changes, value-multi, changes-multi
def channel_for_uri(uri, mode):
	pass

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

			if wait < 1:
				wait = None
			elif wait > WAIT_MAX:
				wait = WAIT_MAX

		resp = view_func(*view_args, **view_kwargs)

		if wait:
			if not request.grip_proxied:
				return HttpResponse('Error: Realtime request not supported. Set up Pushpin or Fanout.\n', status=501)

			if hasattr(resp, 'multi_uris'):
				if resp.multi_empty:
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
