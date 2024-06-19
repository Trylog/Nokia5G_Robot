import time

from pymycobot import MyCobot as cobot
from pymycobot import PI_PORT, PI_BAUD
import numpy as np
import socket
import threading


class Communication:
    control_table = np.array([0, 0, 0, 0, 0, 0], np.int16)  # prędkości dla każdej osi
    # analogowe przełączniki przyjmują wartości od -255 do 255 - jeśli jest wychylony w lewo lub dół to ujemne, a przeciwnie dodatnie
    # lewy analog lewo prawo -> 0; #lewy analog dół góra -> 1; lewy analog lewo prawo -> 4; lewy analog dół góra -> 3;
    # L2 (wartości ujemnie), R2 (wartości dodatnie) (powinny być analogowe) -> 5;
    # L1 (wartości ujemne), R1 (wartości dodatnie) -> 2 - L1 i R2 nie są analogowe więc naciśnięcie przyjmuje wartość -255 albo 255
    event_table = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], np.int8)
    # kolejno kwadrat, trójkąt, kółko, krzyżyk

    robotId = 0
    server = None
    robotInstance = None

    # (str(self.robotId) + np.array2string(self.control_table, precision=1, separator=',', suppress_small=True)
    #            + ";" + np.array2string(self.event_table, precision=1, separator=',', suppress_small=True))10.42.0.197

    new_event = False 

    def __init__(self, robotId, host="192.168.248.216", port=9090):
        self.robotId = robotId
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.connect((host, port))
        self.server.send("RoboticArm".encode("ascii"))
        receive_thread = threading.Thread(target=self.receive_messages)
        receive_thread.start()

        send_thread = threading.Thread(target=self.send_message)
        send_thread.start()

    def receive_messages(self):
        temp = ""
        while True:
            reply = self.server.recv(1024).decode("ascii")
            if reply != temp:
                temp = reply
                if reply == "NAME":
                    pass
                    # self.send_message("Robot")

                elif reply != "":
                    message = reply.split("|")
                    if message[0] == "data":
                        self.control_table, self.event_table = self.convert_mes_to_table(reply)
                        # temp = message.split(';', 1)
                        print("control: ")
                        print(self.event_table)
                        # self.control_table = np.array(map((a) : int(a)),temp.split(','))
                        # self.event_table = np.fromstring(temp[1][1:-1], dtype=np.int16, sep=',')
                        print("event:")
                        print(self.control_table)
                        # print(self.event_table)
                        # print(message)
                        # temp = message.split(';', 1)
                        # if temp[0] == str(self.robotId):

    def send_message(self, message=""):
        while True:
            # message = str(self.robotId) + ";"  # + self.robotInstance.get_status()
            self.server.send(message.encode("ascii"))

    def convert_mes_to_table(self, input_string):
        # Split the input string into messages
        messages = input_string.split(';')

        # Initialize output lists
        event_table_out = []
        control_table_out = []

        for message in messages:
            if message:
                # Split each message into tables
                tables = message.split('|')

                # Convert each table into a list of integers
                if len(tables) == 4 and tables[0] == "data" and tables[3] == "!":
                    event_table = list(map(int, tables[1].split(',')))
                    control_table = list(map(int, tables[2].split(',')))

                    # Append to the output lists
                    event_table_out.append(event_table)
                    control_table_out.append(control_table)
                else:
                    pass

        return event_table_out[-1], control_table_out[-1]

    def get_new_msg(self, message):

        if message == "NAME":
            self.send_message("Robot")

        else:
            self.event_table, self.control_table = self.convert_mes_to_table(message)
            # temp = message.split(';', 1)
            print("control: ")
            print(self.event_table)
            # self.control_table = np.array(map((a) : int(a)),temp.split(','))
            # self.event_table = np.fromstring(temp[1][1:-1], dtype=np.int16, sep=',')
            print("event:")
            print(self.control_table)
            # print(self.event_table)
            # print(message)
            # temp = message.split(';', 1)
            # if temp[0] == str(self.robotId):


class RoboticArm:
    robotId = 0
    coords = None

    def __init__(self, robotId):
        self.robotId = robotId
        self.mc = cobot(PI_PORT, PI_BAUD)
        self.max_angles = np.array([])
        self.min_angles = np.array([])
        for i in range(1, 7):
            self.max_angles = np.append(self.max_angles, self.mc.get_joint_max_angle(i))
            print(self.mc.get_joint_max_angle(i))
        for i in range(1, 7):
            self.min_angles = np.append(self.min_angles, self.mc.get_joint_min_angle(i))
            print(self.mc.get_joint_min_angle(i))
        self.mc.set_color(0, 255, 0)
        if cobot.is_controller_connected(self.mc):
            # cobot.power_on(self.mc)
            self.coords = self.mc.get_coords()
            print(self.mc.get_coords())
            # self.com.send_new_msg("status", 1)
            print("status: ready")
            self.mc.set_color(255, 0, 255)

        else:
            # self.com.send_new_msg("status", -1)
            self.mc.set_color(255, 0, 0)
            print("status: not connected")

        self.mc.release_all_servos()
        self.com = Communication(robotId)

    def get_status(self):
        return cobot.get_angles(self.mc)

    def action_loop(self):
        for _ in range(3):
            self.coords = self.mc.get_angles()
            time.sleep(0.2)
        if self.coords is None:
            print("Didn't get coords")
        print(self.coords)
        print("max_angles: ")
        print(self.max_angles)
        # self.mc.set_color(0, 0, 255)
        while True:
            # self.coords = self.mc.get_angles()
            if self.com.event_table[3]:
                self.mc.stop()
                self.mc.release_all_servos()
                self.mc.set_color(255, 0, 128)
                time.sleep(0.5)
                continue

            else:
                self.mc.set_color(0, 0, 255)
                # coords = self.mc.get_angles()
                # time.sleep(1)
                # print("inMain: ")
                # print(self.com.control_table)
                # time.sleep(0.02)
            if self.com.event_table[2]:
                self.mc.pause()
                continue
            self.coords = self.mc.get_angles()
            for i in range(6):
                if self.com.control_table[i] > 0:
                    # self.mc.jog_angle(i + 1, 1, abs(self.com.control_table[i]))
                    self.mc.send_angle(i + 1, self.coords[i] + 1, abs(int((self.com.control_table[i] / 255) * 100)))
                    self.coords[i] += 1
                    time.sleep(0.01)
                elif self.com.control_table[i] < 0:
                    # self.mc.jog_angle(i + 1, -1, abs(self.com.control_table[i]))
                    self.mc.send_angle(i + 1, self.coords[i] - 1, abs(int((self.com.control_table[i] / 255) * 100)))
                    self.coords[i] -= 1
                    time.sleep(0.01)
                elif self.com.control_table[i] == 0:
                    pass


if __name__ == "__main__":
    roboticArm = RoboticArm(1)
    # roboticArm.mc.release_all_servos()
    roboticArm.action_loop()
    # robot = threading.Thread(target=roboticArm.action_loop())
