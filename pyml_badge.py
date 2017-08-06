import ugfx
import badge
import wifi
import network
from time import sleep

import usocket as socket


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
states = [0 for _ in range(14)]

def handle_key(id, pressed):
    states[id] = pressed
    connection.send_key_states(states)

def handle_up(pressed):
    handle_key(state_map['up'], int(pressed))

def handle_down(pressed):
    handle_key(state_map['down'], int(pressed))

def handle_left(pressed):
    handle_key(state_map['left'], int(pressed))

def handle_right(pressed):
    handle_key(state_map['right'], int(pressed))


def connect_to_wifi(ssid='pymlbadge', password='pymlbadge'):
    show_message("Waiting for wifi...")

    wlan = network.WLAN(network.STA_IF)
    if not wlan.active() or not wlan.isconnected():
        wlan.active(True)
        print('connecting to:', ssid)
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            sleep(0.1)

    print('network config:', wlan.ifconfig())
    show_message("Connected")

def init_badge():
    badge.init()
    ugfx.init()

    wifi.init()
    connect_to_wifi()


def show_message(message):
    ugfx.clear(ugfx.WHITE)
    ugfx.string(10, 10, message, "Roboto_Regular12", 0)
    ugfx.flush()


class Connection:

    def __init__(self, listen_port, control_addr, control_port):
        self.uid = None

        self.listen_port = listen_port
        self.listen_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
        self.listen_sock.setblocking(False)
        # self.listen_sock.bind(('0.0.0.0', self.listen_port))
        addr = socket.getaddrinfo('0.0.0.0', listen_port)
        self.listen_sock.bind(addr[0][-1])

        self.control_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
        self.control_dest = []
        while len(self.control_dest) == 0:
            self.control_dest = socket.getaddrinfo(control_addr, control_port)
        self.control_dest = self.control_dest[0][-1]

        print("registering")
        self.register()

    def ready(self):
        return self.uid is not None

    def register(self):
        command = '/controller/new/{port}'.format(port=self.listen_port)
        try:
            self.control_sock.sendto(command.encode('utf-8'), self.control_dest)
        except Exception as ex:
            print("failed to register controller: {}".format(ex))

    def handle_read(self, data):
        data = data.decode('utf-8')
        if '/' not in data:  # bad, malicous data!!
            return

        command, data = data.rsplit('/', 1)
        if command.startswith('/uid'):
            self.handle_uid(data)
        elif command.startswith('/rumble'):
            # self.handle_rumble(data)
            pass
        elif command.startswith('/message'):
            # self.handle_message(data)
            pass
        elif command.startswith('/download'):
            # self.handle_download(data)
            pass
        elif command.startswith('/play'):
            # self.handle_play(data)
            pass

    def handle_uid(self, data):
        self.uid = data
        print("Got UID {}".format(data))
        self.init_inputs()

    def start_listening(self):
        self.listening = True
        self._listener_loop()

    def stop_listening(self):
        self.listening = False

    def _listener_loop(self):
        while self.listening:
            try:
                data, addr = self.listen_sock.recvfrom(1024)
                self.handle_read(data)
            except:
                pass
            sleep(0.01)

    def init_inputs(self):
        print("initializing input callbacks")
        ugfx.input_init()
        ugfx.input_attach(ugfx.JOY_UP, handle_up)
        ugfx.input_attach(ugfx.JOY_DOWN, handle_down)
        ugfx.input_attach(ugfx.JOY_LEFT, handle_left)
        ugfx.input_attach(ugfx.JOY_RIGHT, handle_right)
        ugfx.input_attach(ugfx.BTN_A, handle_up)
        ugfx.input_attach(ugfx.BTN_B, handle_up)
        ugfx.input_attach(ugfx.BTN_SELECT, handle_up)
        ugfx.input_attach(ugfx.BTN_START, handle_up)

    def ping(self):
        command = '/controller/{uid}/ping/{port}'.format(
            uid=self.uid,
            port=self.port
        )
        socket.sendto(command.encode('utf-8'), self.control_dest)

    def send_key_states(self, states):
        command = '/controller/{uid}/states/{states}'.format(
                uid=self.uid, states=''.join(map(str, states)))

        self.listen_sock.sendto(command.encode('utf-8'), self.control_dest)


init_badge()

destination = 'control.ilexlux.xyz'
show_message("Connecting to {}".format(destination))

connection = Connection(1338, destination, 1338)
connection.start_listening()
