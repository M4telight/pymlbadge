import ugfx, gc, badge
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


def handle_btn(btn_id, pressed):
    print("button pressed: {}".format(btn_id))
    states[btn_id] = int(pressed)
    send_key_states(uid, states, control_sock, control_dest)


def init_inputs():
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


def init_badge():
    badge.init()
    ugfx.init()


def init_wifi():
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.scan()
    sta_if.connect("SHA2017-insecure")
    sta_if.isconnected()
    sta_if.ifconfig()


def show_message(message):
    ugfx.clear(ugfx.WHITE)
    ugfx.string(10, 10, message, "Roboto_Regular12", 0)
    ugfx.flush()


def ping(uid, port, socket, addr):
    command = '/controller/{uid}/ping/{port}'.format(uid=uid, port=port)
    socket.sendto(command.encode('utf-8'), addr)


def handle_read(data):
    data = data.decode('utf-8')
    if '/' not in data:
        # bad, malicous data!!
        return

    command, data = data.rsplit('/', 1)
    if command.startswith('/uid'):
        handle_uid(data)
        # self.handle_uid(data)
        pass
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


def handle_uid(_uid):
    print("got uid: {}".format(data))
    global uid
    uid = _uid
    init_inputs()


def send_key_states(uid, states, socket, addr):
    command = '/controller/{uid}/states/{states}'.format(
            uid=uid, states=''.join(map(str, states))
    )
    socket.sendto(command.encode('utf-8'), addr)


init_badge()
show_message("Initializing badge...")

show_message("Initializing wifi...")
init_wifi()

# listener = Listener(1339, lambda foo: None)

# listener
listen_port = 1339
listen_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
listen_sock.setblocking(False)
addrinfo = socket.getaddrinfo('0.0.0.0', listen_port)
listen_sock.bind(addrinfo[0][-1])

# controller
control_port = 1338
control_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
control_dest = socket.getaddrinfo('127.0.0.1', control_port)[0][-1]

# register control
command = '/controller/new/{port}'.format(port=listen_port)
control_sock.sendto(command.encode('utf-8'), control_dest)

# main loop
show_message("Entering main loop.")

while True:
    try:
        data, addr = listen_sock.recvfrom(1024)
        handle_read(data)
    except:
        pass
    sleep(0.01)

