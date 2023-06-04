from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
import socket
import json
import threading

app = Flask(__name__)

# Визначення шляхів до статичних ресурсів
app.static_url_path = '/static'
app.static_folder = 'static'


# Маршрут для головної сторінки
@app.route('/')
def index():
    return render_template('index.html')


# Маршрут для сторінки з формою
@app.route('/message', methods=['GET', 'POST'])
def message():
    if request.method == 'POST':
        username = request.form['username']
        message = request.form['message']
        save_message(username, message)
        send_to_socket_server(username, message)
        return redirect(url_for('index'))
    return render_template('message.html')


# Збереження повідомлення у файлі data.json
def save_message(username, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    data = {
        "username": username,
        "message": message
    }
    with open('storage/data.json', 'r+') as file:
        try:
            messages = json.load(file)
        except json.JSONDecodeError:
            messages = {}
        messages[timestamp] = data
        file.seek(0)
        json.dump(messages, file, indent=2)
        file.truncate()

# Відправка повідомлення на Socket сервер
def send_to_socket_server(username, message):
    data = {
        "username": username,
        "message": message
    }
    json_data = json.dumps(data)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = ('localhost', 5000)
    sock.sendto(json_data.encode('utf-8'), server_address)
    sock.close()


# Маршрут для обробки помилки 404
@app.errorhandler(404)
def not_found(error):
    return render_template('error.html'), 404


# Socket сервер
def socket_server():
    server_address = ('localhost', 5000)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(server_address)
    print('Socket server started')
    while True:
        data, address = sock.recvfrom(4096)
        message = data.decode('utf-8')
        save_message_from_socket_server(message)


# Збереження повідомлення з Socket сервера у файлі data.json
def save_message_from_socket_server(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    data = json.loads(message)
    with open('storage/data.json', 'a') as file:
        json.dump({timestamp: data}, file)
        file.write('\n')


if __name__ == '__main__':
    # Запуск HTTP сервера на порту 3000
    http_thread = threading.Thread(target=app.run, kwargs={'port': 3000, 'threaded': True})
    http_thread.start()

    # Запуск Socket сервера на порту 5000
    socket_thread = threading.Thread(target=socket_server)
    socket_thread.start()

