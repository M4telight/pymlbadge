import ugfx, gc, wifi, badge
import urequests as requests

import usocket as socket
import _thread as thread


def init_badge():
	ugfx.init()

	# Make sure WiFi is connected
	wifi.init()

	ugfx.clear(ugfx.WHITE);
	ugfx.string(10,10,"Waiting for wifi...","Roboto_Regular12", 0)
	ugfx.flush()

	# Wait for WiFi connection
	while not wifi.sta_if.isconnected():
	    sleep(0.1)
	    pass


class Listener:

	def __init__(self, port):
		self.port = port
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
		addrinfo = socket.getaddrinfo('0.0.0.0', port)
		self.socket.bind(addrinfo[0][-1])

	def control_loop(self, arg):
		ugfx.clear(ugfx.WHITE)
		ugfx.string(10, 10, "Waiting for message on  {}".format(self.port), "Roboto_Regular12", 0)
		ugfx.flush()

		while True:
			data, addr = self.socket.recvfrom(1024)
			ugfx.clear(ugfx.WHITE)
			ugfx.string(10, 10, "Got message of length {}".format(data.decode('utf-8')), "Roboto_Regular12", 0)
			ugfx.flush()



if __name__ == "__main__":
	init_badge()

	listener = Listener(1336)
	# listener.control_loop()
	thread.start_new_thread(listener.control_loop, (1,))

	i=0
	while True:
		sleep(0.5)
		ugfx.string(10, 25, "Counting {}".format(i), "Roboto_Regular12", 0)
		i += 1
