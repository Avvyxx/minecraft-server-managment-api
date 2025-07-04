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

def startServer(server_name):
    if server_name.lower() in [name.lower() for name in getAvailableMinecraftServers()]:
        # start server if not started
        if server_name.lower() in getRunningMinecraftServers():
            ...
        else:
            return 1
    else:
        return 0


class MinecraftAPI(BaseHTTPRequestHandler):
    def do_GET(self):
        path = pathlib.Path(self.path)

        self.protocol_version = 'HTTP/1.0'
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')

        if len(path.parts) < 2:
            self.end_headers()
            self.wfile.write(json.dumps(['fail'].encode()))

        if path.parts[1] == 'list':
            response_data = []

            all_servers = getAvailableMinecraftServers()
            running_servers = getRunningMinecraftServers()

            for server in all_servers:
                server_data = {
                    'name': server,
                    'domain': server.lower() + '.avyx.home'
                }

                if server in running_servers:
                    server_data['state'] = 'running'
                else: # is stopped
                    server_data['state'] = 'stopped'

                response_data.append(server_data)

            response_json = json.dumps(response_data).encode()

            self.send_header('Content-Length', str(len(response_json)))
            self.end_headers()
            self.wfile.write(response_json)

        else:
            self.end_headers()
            self.wfile.write(json.dumps(['Unkown path']).encode())
            self.send_response(200)

server = HTTPServer(('0.0.0.0', 8000), MinecraftAPI)
server.serve_forever()
