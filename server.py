import socket
import threading
import time

HOST = ("192.168.100.88")
PORT = 9090
clients = []
names = []

def broadcast(message, client_):
    print(message)
    for client in clients:

        if client is not client_:
            client.send(message.encode("ascii"))
def handle_client(client):
    while True:
        try:
            message = client.recv(1028).decode("ascii")
            broadcast(message, client)
        except:
            index = clients.index(client)
            clients.remove(client)
            client.close()
            name = names[index]
            names.remove(name)
            break

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
    server.bind((HOST, PORT))
    server.listen()

    while True:
        client, addr = server.accept()
        print(f"{str(addr)} connected successfully")
        clients.append(client)

        client.send("NAME".encode("ascii"))

        name = client.recv(1028).decode("ascii")
        names.append(name)

        thread = threading.Thread(target=handle_client, args=(client,))
        thread.start()

