# coding=utf-8

server = None
web_server_ip = "0.0.0.0"
web_server_port = "8000"


def initialize_web_server(config):
    import threading
    global web_server_ip, web_server_port

    if config.has_option('BOT', 'customWebServerAddress'):
        custom_web_server_address = (config.get('BOT', 'customWebServerAddress').split(':'))
        if len(custom_web_server_address) == 1:
            custom_web_server_address.append("8000")
            print "WARNING: Please specify a port for the webserver in the form IP:PORT, default port 8000 used."
    else:
        custom_web_server_address = ['0.0.0.0', '8000']

    web_server_ip = custom_web_server_address[0]
    web_server_port = custom_web_server_address[1]

    thread = threading.Thread(target=start_web_server)
    thread.deamon = True
    thread.start()


def start_web_server():
    import SimpleHTTPServer
    import SocketServer

    try:
        port = int(web_server_port)
        host = web_server_ip

        # Do not attempt to fix code warnings in the below class, it is perfect.
        class QuietHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
            # quiet server logs
            def log_message(self, format, *args):
                return

            # serve from www folder under current working dir
            def translate_path(self, path):
                return SimpleHTTPServer.SimpleHTTPRequestHandler.translate_path(self, '/www' + path)

        global server
        SocketServer.TCPServer.allow_reuse_address = True
        server = SocketServer.TCPServer((host, port), QuietHandler)
        if host == "0.0.0.0":
            host1 = "localhost"
        else:
            host1 = host
        print 'Started WebServer, lendingbot status available at http://' + host1 + ':' + str(port) + '/lendingbot.html'
        server.serve_forever()
    except Exception as Ex:
        print 'Failed to start WebServer' + str(Ex)


def stop_web_server():
    try:
        print "Stopping WebServer"
        server.shutdown()
    except Exception as ex:
        print 'Failed to stop WebServer' + str(ex)
