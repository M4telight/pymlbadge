import ugfx, gc, wifi, badge
from time import sleep
import urequests as requests

import usocket as socket
import _thread as thread


def init_badge():
    ugfx.init()

    # Make sure WiFi is connected
    wifi.init()
    show_message("Waiting for wifi...")

    # Wait for WiFi connection
    while not wifi.sta_if.isconnected():
        sleep(0.1)
        pass

def show_message(message):
    ugfx.clear(ugfx.WHITE);
    ugfx.string(10, 10, message, "Roboto_Regular12", 0)
    ugfx.flush()


class Communicator:

    def __init__(self, host, port, listener_port):
        self.host = host
        self.port = port
        self.listener_port = listener_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
        self.destination_address = socket.getaddrinfo(self.host, self.port)[0][-1]
        self.uid = None

    def set_uid(self, uid):
        self.uid = uid
        thread.start_new_thread(self.ping, (1,))

    def send_key_states(self, states):
        command = '/controller/{uid}/states/{states}'.format(
            uid=self.uid,
            states=''.join(map(str, states)),
        )
        self.socket.sendto(command.encode('utf-8'), self.destination_address)

    def register(self):
        command = '/controller/new/{port}'.format(
            port=self.listener_port,
        )
        self.socket.sendto(command.encode('utf-8'), self.destination_address)

    def ping(self, arg):
        command = '/controller/{uid}/ping/{port}'.format(
            uid=self.uid,
            port=self.listener_port,
        )
        while True:
            self.socket.sendto(command.encode('utf-8'), self.destination_address)
            sleep(20)


class Listener:

    def __init__(self, port, set_uid_callback):
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
        addrinfo = socket.getaddrinfo('0.0.0.0', port)
        self.socket.bind(addrinfo[0][-1])
        self.uid = None
        self.set_uid_callback = set_uid_callback

    def control_loop(self, arg):
        while True:
            data, addr = self.socket.recvfrom(1024)
            data = data.decode('utf-8')

            if '/' not in data:
                # bad, malicous data!!
                continue

            command, data = data.rsplit('/', 1)
            if command.startswith('/uid'):
                print("got uid")
                self.handle_uid(data)
            elif command.startswith('/rumble'):
                self.handle_rumble(data)
            elif command.startswith('/message'):
                self.handle_message(data)
            elif command.startswith('/download'):
                self.handle_download(data)
            elif command.startswith('/play'):
                self.handle_play(data)

    def handle_uid(self, uid):
        show_message("Got UID: {}".format(uid))
        self.uid = uid
        self.set_uid_callback(uid)

    def handle_rumble(self, duration):
        show_message("'rumble' is not yet implemented")

    def handle_message(self, message):
        show_message(message)

    def handle_download(self, url):
        show_message("'download' is not yet implemented")

    def handle_file(self, file):
        show_message("'file' is not yet implemented")



class InputHandler:

    state_map = {
        'up': 0,
        'down': 1,
        'left': 2,
        'right': 3,
        'a': 4,
        'b': 5,
        'start': 8,
        'select': 9,
    }

    def __init__(self, controller):
        self.states = [0 for _ in range(14)]
        self.controller = controller
        self.shutdown = False
        self.init_inputs(1)

    def init_inputs(self, arg):
        ugfx.input_init()
        ugfx.input_attach(ugfx.JOY_UP, lambda pressed: self.handle_btn(self.state_map['up'], pressed))
        ugfx.input_attach(ugfx.JOY_DOWN, lambda pressed: self.handle_btn(self.state_map['down'], pressed))
        ugfx.input_attach(ugfx.JOY_LEFT, lambda pressed: self.handle_btn(self.state_map['left'], pressed))
        ugfx.input_attach(ugfx.JOY_RIGHT, lambda pressed: self.handle_btn(self.state_map['right'], pressed))
        ugfx.input_attach(ugfx.BTN_A, lambda pressed: self.handle_btn(self.state_map['a'], pressed))
        ugfx.input_attach(ugfx.BTN_B, lambda pressed: self.handle_btn(self.state_map['b'], pressed))
        ugfx.input_attach(ugfx.BTN_SELECT, lambda pressed: self.handle_btn(self.state_map['select'], pressed))
        ugfx.input_attach(ugfx.BTN_START, lambda pressed: self.handle_btn(self.state_map['start'], pressed))
        thread.start_new_thread(self.start_pushing, (1,))

    def start_pushing(self, arg):
        while True:
            if communicator.uid is not None:
                self.controller.send_key_states(self.states)
            if self.shutdown:
                break
            sleep(0.05)


    def handle_btn(self, btn_id, pressed):
        self.states[btn_id] = int(pressed)
        self.controller.send_key_states(self.states)



init_badge()

communicator = Communicator('127.0.0.1', 1338, 1339)
listener = Listener(1339, communicator.set_uid)
communicator.register()
thread.start_new_thread(listener.control_loop, (1,))
input_handler = InputHandler(communicator)

while True:
    sleep(0.01)
