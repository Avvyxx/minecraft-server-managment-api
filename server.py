from http.server import BaseHTTPRequestHandler, HTTPServer
import pathlib, psutil, os, subprocess, json

# Gets java runtimes running as a list
def getJavaProcesses():
    java_processes = []

    for process in psutil.process_iter():
        if 'java' in process.name().lower():
            java_processes.append(process)

    return java_processes

# Gets Minecraft Servers running as a list
def getRunningMinecraftServers():
    minecraft_processes = []

    for java_process in getJavaProcesses():
        for arg in java_process.cmdline():
            if 'Minecraft-Servers' in arg:
                server_name = getServerNameFromArg(arg)
                minecraft_processes.append(server_name)
                break

    return minecraft_processes

def getServerNameFromArg(javaProcessArg):
    path = pathlib.Path(javaProcessArg)

    for i in range(len(path.parts)):
        if path.parts[i] == 'Minecraft-Servers':
            return path.parts[i + 1]

# Returns list
def getAvailableMinecraftServers():
    servers = filter(lambda s: s[0] != '.', os.listdir('/home/avvy/Minecraft-Servers/'))

    return list(servers)

class MinecraftAPI(BaseHTTPRequestHandler):
    def do_GET(self):
        path = pathlib.Path(self.path)

        self.protocol_version = 'HTTP/1.0'
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')

        if len(path.parts) < 2:
            json_response = json.dumps(['fail']).encode()
            self.send_header('Content-Length', str(len(json_response)))
            self.end_headers()
            self.wfile.write(json_response)
            return

        if path.parts[1] == 'list':
            response_data = []

            all_servers = getAvailableMinecraftServers()
            running_servers = getRunningMinecraftServers()

            for server in all_servers:
                server_data = {
                    'name': server,
                    'domain': server.lower() + '.avyx.home',
                    'state': 'running' if server in running_servers else 'stopped'
                }

                response_data.append(server_data)

            response_json = json.dumps(response_data).encode()

            self.send_header('Content-Length', str(len(response_json)))
            self.end_headers()
            self.wfile.write(response_json)

        elif path.parts[1] == 'ping':
            json_response = json.dumps(['pong']).encode()
            self.send_header('Content-Length', str(len(json_response)))
            self.end_headers()
            self.wfile.write(json_response)

        else:
            # invalid path
            json_response = json.dumps(['Unkown path']).encode()
            self.send_header('Content-Length', str(len(json_response)))
            self.end_headers()
            self.wfile.write(json_response)
            self.send_response(200)

    def do_POST(self):
        path = pathlib.Path(self.path)

        self.protocol_version = 'HTTP/1.0'
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')

        if len(path.parts) < 3:
            json_response = json.dumps(['fail']).encode()
            self.send_header('Content-Length', str(len(json_response)))
            self.end_headers()
            self.wfile.write(json_response)

        if path.parts[1] == 'start':
            # check if server is available
            # check that its not running
            # start with tmux detached session

            server = path.parts[2]

            if server in getAvailableMinecraftServers():
                if server in getRunningMinecraftServers():
                    # server is already running
                    json_response = json.dumps(['Server already started']).encode()
                    self.send_header('Content-Length', str(len(json_response)))
                    self.end_headers()
                    self.wfile.write(json_response)
                else:
                    # for now each server will run in a new session
                    command = ['tmux', 'new-session', '-d', '-s', server + '-Minecraft-Server', f'/home/avvy/Minecraft-Servers/{server}/start.sh']

                    result = subprocess.run(command, check=True)

                    message = 'Server started' if result.returncode == 0 else 'Server startup failed'
                    json_response = json.dumps([message]).encode()

                    self.send_header('Content-Length', str(len(json_response)))
                    self.end_headers()
                    self.wfile.write(json_response)
            else:
                # invalid server
                json_response = json.dumps(['Server doesnt exist']).encode()
                self.send_header('Content-Length', str(len(json_response)))
                self.end_headers()
                self.wfile(json_response)

        elif path.parts[1] == 'stop':
            server = path.parts[2]

            if server in getAvailableMinecraftServers():
                if server in getRunningMinecraftServers():
                    # stop running server
                    command = ['tmux', 'send-keys', '-t', server + '-Minecraft-Server', 'stop', 'ENTER']

                    result = subprocess.run(command, check=True)

                    message = 'Server stopped' if result.returncode == 0 else 'Server stop failed'
                    json_response = json.dumps([message]).encode()

                    self.send_header('Content-Length', str(len(json_response)))
                    self.end_headers()
                    self.wfile.write(json_response)

                else:
                    json_response = json.dumps(['Server already stopped']).encode()
                    self.send_header('Content-Length', str(len(json_response)))
                    self.end_headers()
                    self.wfile.write(json_response)
            else:
                # invalid server
                json_response = json.dumps(['Server does not exist']).encode()
                self.send_header('Content-Length', str(len(json_response)))
                self.end_headers()
                self.wfile.write(json_response)

        else:
            # invalid path
            json_response = json.dumps(['Uknown path']).encode()
            self.send_header('Content-Length', str(len(json_response)))
            self.end_headers()
            self.wfile.write(json_response)

server = HTTPServer(('0.0.0.0', 8000), MinecraftAPI)
server.serve_forever()
