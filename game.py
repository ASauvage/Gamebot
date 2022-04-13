import socket
from pyboy import PyBoy, WindowEvent

tcpport = 5555

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(("127.0.0.1", tcpport))
s.listen()

inputList = [
    WindowEvent.PRESS_ARROW_UP,
    WindowEvent.PRESS_ARROW_DOWN,
    WindowEvent.PRESS_ARROW_LEFT,
    WindowEvent.PRESS_ARROW_RIGHT,
    WindowEvent.PRESS_BUTTON_A,
    WindowEvent.PRESS_BUTTON_B,
    WindowEvent.PRESS_BUTTON_SELECT,
    WindowEvent.PRESS_BUTTON_START,
    WindowEvent.RELEASE_ARROW_UP,
    WindowEvent.RELEASE_ARROW_DOWN,
    WindowEvent.RELEASE_ARROW_LEFT,
    WindowEvent.RELEASE_ARROW_RIGHT,
    WindowEvent.RELEASE_BUTTON_A,
    WindowEvent.RELEASE_BUTTON_B,
    WindowEvent.RELEASE_BUTTON_SELECT,
    WindowEvent.RELEASE_BUTTON_START
]


def run():
    conn, addr = s.accept()
    print("Connected by ", addr)
    conn.settimeout(0.0001)
    while True:
        try:
            message = conn.recv(255)

            message = message.decode('UTF-8')
            print(message)
            if message.startswith("gamestart."):
                name = message[10::]

                pyboy = PyBoy(f"roms/{name}.gb", window_type="headless", sound=False)
                pyboybot = pyboy.botsupport_manager().screen()
                pyboy.set_emulation_speed(2)

                while not pyboy.tick():
                    try:
                        packet = conn.recv(255).decode('UTF-8')

                        if packet == "stop":
                            pyboy.stop(save=False)
                            conn.sendall(b"done")
                            break
                        elif packet == "save":
                            f = open(f"roms/saves/{name}.state", "wb")
                            pyboy.save_state(f)
                            conn.sendall(b"done")
                        elif packet == "load":
                            f = open(f"roms/saves/{name}.state", "rb")
                            pyboy.load_state(f)

                            pyboy.tick()

                            screenshot = pyboybot.screen_image()
                            screenshot = screenshot.resize((480, 432))
                            screenshot.save(f"screenshot/{name}.png")

                            conn.sendall(b"done")
                        elif packet.startswith("but_"):
                            button = packet[-1]
                            pyboy.send_input(inputList[int(button)])
                            for x in range(5):
                                pyboy.tick()
                            pyboy.send_input(inputList[int(button) + 8])
                            for x in range(150):
                                pyboy.tick()
                            screenshot = pyboybot.screen_image()
                            screenshot = screenshot.resize((480, 432))
                            screenshot.save(f"screenshot/{name}.png")

                            print(f"[game.py] screnshot/{name}.png saved")

                            conn.sendall(b"done")
                    except socket.error:
                        pass
        except socket.error:
            pass


run()
