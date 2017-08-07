import appglue
import ugfx
import badge
import wifi
import network
import time

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

def handle_start(pressed):
    show_message("Thank you and Good Bye")
    connection.stop_listening()


def connect_to_wifi(ssid='pymlbadge', password='pymlbadge'):
    show_message("Waiting for wifi...")

    wlan = network.WLAN(network.STA_IF)
    if not wlan.active() or not wlan.isconnected():
        wlan.active(True)
        print('connecting to:', ssid)
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            time.sleep(0.1)

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

    def __init__(self, remote_addr, port):
        self.uid = None

        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
        self.socket.setblocking(False)
        addr = socket.getaddrinfo('0.0.0.0', port)
        self.socket.bind(addr[0][-1])

        self.remote_addr = []
        while len(self.remote_addr) == 0:
            self.remote_addr = socket.getaddrinfo(remote_addr, port)
        self.remote_addr = self.remote_addr[0][-1]

        self.last_ping = 0

        print("registering")
        self.register()

    def ready(self):
        return self.uid is not None

    def register(self):
        command = '/controller/new/{port}'.format(port=self.port)
        try:
            self.socket.sendto(command.encode('utf-8'), self.remote_addr)
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
            # ping every 20 seconds
            if time.time() - self.last_ping >= 20:
                self.ping()
            try:
                data, addr = self.socket.recvfrom(1024)
                self.handle_read(data)
            except:
                pass
            time.sleep(0.01)

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
        ugfx.input_attach(ugfx.BTN_START, handle_start)

    def ping(self):
        command = '/controller/{uid}/ping/{port}'.format(
            uid=self.uid,
            port=self.port
        )
        try:
            self.socket.sendto(command.encode('utf-8'), self.remote_addr)
        except:
            print("warning: ping failed")
        self.last_ping = time.time()

    def send_key_states(self, states):
        command = '/controller/{uid}/states/{states}'.format(
                uid=self.uid, states=''.join(map(str, states)))

        self.socket.sendto(command.encode('utf-8'), self.remote_addr)


init_badge()

destination = 'control.ilexlux.xyz'
show_message("Connecting to {}".format(destination))

connection = Connection(destination, 1338)
connection.start_listening()
appglue.home()
