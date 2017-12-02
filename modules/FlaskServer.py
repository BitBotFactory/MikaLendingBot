from flask import Flask, send_file
import pandas as pd
import threading

app = Flask(__name__, static_url_path='', static_folder="../www")


class FlaskServer(object):
    def __init__(self, botConf):
        '''
        Setup the web server, retrieving the configuration parameters
        and starting the web server thread
        '''
        self.botConf = botConf
        # Check for custom web server address
        compositeWebServerAddress = botConf.get('BOT', 'customWebServerAddress', '0.0.0.0').split(":")

        # associate web server ip address
        self.web_server_ip = compositeWebServerAddress[0]

        # check for IP:PORT legacy format
        if (len(compositeWebServerAddress) > 1):
            # associate web server port
            self.web_server_port = compositeWebServerAddress[1]
        else:
            # Check for custom web server port
            self.web_server_port = botConf.get('BOT', 'customWebServerPort', '8000')

        # Check for custom web server template
        self.web_server_template = botConf.get('BOT', 'customWebServerTemplate', 'www')

        print('Starting WebServer at {0} on port {1} with template {2}'
              .format(self.web_server_ip, self.web_server_port, self.web_server_template))

        app.add_url_rule('/config', 'config', self.config)

    def run_web_server(self):
        self.thread_stop = threading.Event()
        thread = threading.Thread(target=self.main, args=(self.thread_stop, ))
        thread.deamon = True
        thread.start()

    def stop_web_server(self):
        self.thread_stop.set()

    @app.route('/')
    def root():
        return send_file('../www/lendingbot.html')

    def config(self):
        df = pd.DataFrame(data=self.botConf.config.items('BOT'))
        df = df.fillna(' ').T
        df = df.transpose()
        df.columns = ['Option', 'Value']
        return df.to_html()

    def main(self, stop_event):
        while not stop_event.is_set():
            app.run(debug=False,
                    threaded=True,
                    use_reloader=False,
                    port=self.web_server_port,
                    host=self.web_server_ip)
