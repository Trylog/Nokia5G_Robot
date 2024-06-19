import os
import evdev
import numpy as np
import socket
import threading
import time
import sys


HOST = "192.168.248.216"
PORT = 9090

print_data_flag = False
auto_choose_flag = True
auto_choose_number = 1
sending_spped = 1 #second

def convert_table_to_mes(axis_positions, event_table):
    control_tab = ','.join(map(str, [int(value * 255) for value in axis_positions.values()]))
    event_table_str = ','.join(map(str, event_table))
    return "data|" + control_tab + "|" + event_table_str + "|!;"


def receive_messages():
    while True:
        try:
            reply = server.recv(1024).decode("ascii")
            if reply == "NAME":
                server.sendall(name.encode("ascii"))
            else:
                print(reply)
        except:
            print("An error occured!")
            server.close()
            sys.exit(1)
            break     
     
def send_message():
    global mes_tab
    while True:
        time.sleep(sending_spped)
        try:
            mes_tab_lock.acquire()
            print("mes = " + mes_tab[-1])
            server.send(mes_tab[-1].encode("ascii"))
            mes_tab = []
            mes_tab_lock.release()
            send_data()
        except:
            print(mes_tab[-1])
            print("send ERROR mes:" + mes_tab[-1])
            sys.exit(1)
        
    
def update_data(divace_name):
    #os.system('cls' if os.name == 'nt' else 'clear')
    
    # Print button states and axis positions
    if(print_data_flag):
        print("Divace name: " + divace_name)
        print("Button states:")
        for button, state in button_states.items():
            print(f"{button}: {state}")
        print("\nAxis positions:")
        for axis, position in axis_positions.items():
            print(f"{axis}: {position:.2f}")
    send_data()
        
def send_data():
    global mes_tab
    event_table = np.zeros(len(button_states), dtype=np.int8)

    for i, (button, state) in enumerate(button_states.items()):
        if state == "Pressed":
            event_table[i] = 1
        elif state == "Released":
            event_table[i] = 0
        elif state == "Right" or state == "Up":
            event_table[i] = 1
        elif state == "Left" or state == "Down":
            event_table[i] = -1

    new_message = convert_table_to_mes(axis_positions, event_table)
    #time.sleep(0.001)
    mes_tab_lock.acquire()
    mes_tab.append(new_message)
    mes_tab_lock.release()
    #send_message(new_message)
    
    #print(new_message)

# Global variables to store button states and axis positions
button_states = {
    "Button L1": "Released",
    "Button R1": "Released",
    "Triangle" : "Released",
    "Square" : "Released",
    "Circle" : "Released",
    "Cross" : "Released",
    "Start" : "Released",
    "Select" : "Released",
    "UP/DOWN": "Released",
    "LEFT/RIGHT": "Released"
}

axis_positions = {
    "L-OX": 0.0,
    "L-OY": 0.0,
    "L-OZ": 0.0,
    "R-OX": 0.0,
    "R-OY": 0.0,
    "R-OZ": 0.0
}
mes_tab_lock = threading.Lock()
mes_tab = []
send_data()


def find_pad_controller():
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    ps4_devices = []

    for device in devices:
        if "controller" in device.name.lower() or "pad" in device.name.lower():
            ps4_devices.append(device)
            if(not(auto_choose_flag)):
                print(f"{len(ps4_devices)}. Found PS4 Controller (USB):", device.name)

    if not ps4_devices:
        print("No Pad controller found. Make sure it's paired or connected via USB or Bluetooth.")
        return None

    while True:
        try:
            if(not(auto_choose_flag)):
                choice = int(input("Enter the number of the device you want to connect with: "))
            else:
                choice = auto_choose_number
            if 1 <= choice <= len(ps4_devices):
                return ps4_devices[choice - 1]
            else:
                print("Invalid choice. Please enter a number between 1 and", len(ps4_devices))
        except ValueError:
            print("Invalid input. Please enter a number.")

# Main function to read pressed buttons and axis positions
def read_ps4_controller_events(device):
    try:
        sensitivity = 0.25
        update_data(device.name)
        axis_max_val = 1
        axis_min_val = -1
        axis_positive_mode = True
                
        axis = 0
        axis_info = device.absinfo(axis)
        if axis_info:
            axis_max_val = (axis_info.max)
            axis_min_val = (axis_info.min)
            
            if axis_min_val == 0:
                axis_positive_mode = True
                axis_max_val = (axis_max_val + 1)/2
            else:
                axis_positive_mode = False                
        
        for event in device.read_loop():
            if event.type == evdev.ecodes.EV_ABS:
                if axis_positive_mode:
                    axis_value = (event.value - axis_max_val) / axis_max_val
                else:
                    axis_value = (event.value) / axis_max_val
                if (axis_value > sensitivity or axis_value < -sensitivity) and event.code != evdev.ecodes.ABS_HAT0Y:
                    update = True
                    if event.code == evdev.ecodes.ABS_X:
                        axis_positions["L-OX"] = axis_value
                    elif event.code == evdev.ecodes.ABS_Y:
                        axis_positions["L-OY"] = axis_value
                    elif event.code == evdev.ecodes.ABS_RX:
                        axis_positions["R-OX"] = axis_value
                    elif event.code == evdev.ecodes.ABS_RY:
                        axis_positions["R-OY"] = axis_value
                        
                    elif event.code == evdev.ecodes.ABS_Z:
                        axis_value = (axis_value+1)/2
                        if(axis_value>sensitivity):
                            axis_positions["L-OZ"] = axis_value
                        else:
                            if(axis_positions["L-OZ"] != 0):
                                axis_positions["L-OZ"] = 0
                            else:
                                axis_positions["L-OZ"] = 0
                                update = False
                    elif event.code == evdev.ecodes.ABS_RZ:
                        axis_value = (axis_value+1)/2
                        if(axis_value>sensitivity):
                            axis_positions["R-OZ"] = axis_value
                        else:
                            if(axis_positions["R-OZ"] != 0):
                                axis_positions["R-OZ"] = 0
                            else:
                                axis_positions["R-OZ"] = 0
                                update = False
                            
                    elif event.code == 16:
                        if event.value == -1:
                            button_states["LEFT/RIGHT"] = "Left"
                        elif event.value == 1:
                            button_states["LEFT/RIGHT"] = "Right"
                        else:
                            button_states["LEFT/RIGHT"] = "Released"
                    if(update):
                        update_data(device.name)

                        
                else:
                    if event.code == evdev.ecodes.ABS_X:
                        if axis_positions["L-OX"] != 0:
                            axis_positions["L-OX"] = 0
                            update_data(device.name)
                    elif event.code == evdev.ecodes.ABS_Y:
                        if axis_positions["L-OY"] != 0:
                            axis_positions["L-OY"] = 0
                            update_data(device.name)
                    elif event.code == evdev.ecodes.ABS_RX:
                        if axis_positions["R-OX"] != 0:
                            axis_positions["R-OX"] = 0
                            update_data(device.name)
                    elif event.code == evdev.ecodes.ABS_RY:
                        if axis_positions["R-OY"] != 0:
                            axis_positions["R-OY"] = 0
                            update_data(device.name)
                            
                    if event.code == evdev.ecodes.ABS_HAT0Y:
                        if event.value == -1:
                            button_states["UP/DOWN"] = "Up"
                        elif event.value == 1:
                            button_states["UP/DOWN"] = "Down"
                        else:
                            button_states["UP/DOWN"] = "Released"
                        update_data(device.name)
                    
            elif event.type == evdev.ecodes.EV_KEY:
                button_map = {
                    evdev.ecodes.BTN_TL: "Button L1",
            evdev.ecodes.BTN_TR: "Button R1",
            evdev.ecodes.BTN_NORTH: "Triangle", 
            evdev.ecodes.BTN_WEST: "Square",     
            evdev.ecodes.BTN_SOUTH: "Cross",    
            evdev.ecodes.BTN_EAST: "Circle", 
            evdev.ecodes.BTN_START: "Start", 
            evdev.ecodes.BTN_SELECT: "Select", 
                }
                button_name = button_map.get(event.code)
                if button_name is not None:
                    button_states[button_name] = "Pressed" if event.value == 1 else "Released"
                    update_data(device.name)
                        
    except KeyboardInterrupt:
        print("\nProgram terminated.")

if __name__ == "__main__":
    ps4_controller = find_pad_controller()
    name = ps4_controller.name
    
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("Wait for conection")
        #server.settimeout(10)
        server.connect((HOST, PORT))
        print("Conected")
    except Exception as e:
        print("Conect Faill")
        sys.exit(1)
        
    receive_thread = threading.Thread(target=receive_messages)
    receive_thread.start()

    send_thread = threading.Thread(target=send_message)
    send_thread.start()
    
    if ps4_controller:
        print("Starting event reading...")
        read_ps4_controller_events(ps4_controller)
