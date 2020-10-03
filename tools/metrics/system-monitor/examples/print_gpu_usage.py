import zmq

monitor_port = "5560"

context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect("tcp://localhost:%s" % monitor_port)
socket.subscribe(b'')
while 1:
    string = socket.recv()
    print(string)
