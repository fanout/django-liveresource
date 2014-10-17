import json
from django_grip import websocket_only

def multi(request):
	# TODO: make internal requests and respond normally. middleware will handle grip stuff.
	#  set resp.multi_uris to a list of uris being serviced by this request
	pass

@websocket_only
def updates(request):
	ws = request.wscontext

	# accept all incoming connections
	if ws.is_opening():
		ws.accept()

	while ws.can_recv():
		message = ws.recv()
		if message is None:
			ws.close()
			break

		# FIXME: robust parsing
		# FIXME: channel schema
		req = json.loads(message)
		if req['type'] == 'subscribe':
			ws.subscribe(req['uri'])
			resp = {'id': req['id'], 'type': 'subscribed'}
		elif req['type'] == 'subscribe':
			ws.unsubscribe(req['uri'])
			resp = {'id': req['id'], 'type': 'unsubscribed'}
		else:
			resp = {'id': req['id'], 'type': 'error'}

		ws.send(json.dumps(resp))
