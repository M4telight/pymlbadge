import ugfx
import badge
import wifi
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


def init_badge():
    badge.init()
    ugfx.init()

    wifi.init()
    show_message("Waiting for wifi...")

    # Wait for WiFi connection
    i = 0
    while not wifi.sta_if.isconnected():
        show_message('Waiting: {}'.format(i))
        sleep(0.3)
        i += 1
    show_message("Connected")


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
        self.control_dest = socket.getaddrinfo(control_addr, control_port)[0][-1]

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

    def handle_btn(self, btn_id, pressed):
        print("button pressed: {}".format(btn_id))
        states[btn_id] = int(pressed)
        self.send_key_states(states)

    def init_inputs(self):
        print("initializing input callbacks")
        ugfx.input_init()
        ugfx.input_attach(ugfx.JOY_UP, lambda pressed: handle_btn(state_map['up'], pressed))
        ugfx.input_attach(ugfx.JOY_DOWN, lambda pressed: handle_btn(state_map['down'], pressed))
        ugfx.input_attach(ugfx.JOY_LEFT, lambda pressed: handle_btn(state_map['left'], pressed))
        ugfx.input_attach(ugfx.JOY_RIGHT, lambda pressed: handle_btn(state_map['right'], pressed))
        ugfx.input_attach(ugfx.BTN_A, lambda pressed: handle_btn(state_map['a'], pressed))
        ugfx.input_attach(ugfx.BTN_B, lambda pressed: handle_btn(state_map['b'], pressed))
        ugfx.input_attach(ugfx.BTN_SELECT, lambda pressed: handle_btn(state_map['select'], pressed))
        ugfx.input_attach(ugfx.BTN_START, lambda pressed: handle_btn(state_map['start'], pressed))

    def ping(self):
        command = '/controller/{uid}/ping/{port}'.format(uid=self.uid,
                                                         port=self.port)
        socket.sendto(command.encode('utf-8'), self.control_dest)

    def send_key_states(self, states):
        command = '/controller/{uid}/states/{states}'.format(
                uid=self.uid, states=''.join(map(str, states)))
        try:
            self.control_sock.sendto(command.encode('utf-8'), self.control_dest)
        except Exception as e:
            print(str(e))


def main():
    init_badge()

    destination = 'control.ilexlux.xyz'
    show_message("Connecting to {}".format(destination))

    connection = Connection(1339, destination, 1338)
    connection.start_listening()

    while not connection.ready():
        sleep(0.2)

    show_message("Got uid: {}\nInitializing inputs...".format(connection.uid))
    connection.init_inputs()


main()
