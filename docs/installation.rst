Installation
************

Installing on a Computer
========================

Installing the bot on a computer is drag-and-drop and platform independent.

Prerequisites
-------------

You will need:

    - Python 2.7.x (Must be added to PATH)

Recommended for easier use:

    - git
    - pip (to install following required Python modules)
    - Numpy (if using Analysis module)
    - requests (HTTPS communication)
    - pytz (Timezone calculations)

It is possible to install all required Python modules **after downloading** of the bot running:

``pip install -r requirements.txt``

or, if you need to run it as root under Linux:

``sudo pip install -r requirements.txt``

Downloading
-----------

To download the bot you can either:

- (Recommended) Run ``git clone https://github.com/BitBotFactory/poloniexlendingbot`` if you have git installed. Using this method will allow you to do ``git pull`` at any time to grab updates.
- Download the source .zip file from the GitHub repo page or from `this link <https://github.com/BitBotFactory/poloniexlendingbot/archive/master.zip>`_. Extract it into an empty folder you won't accidentally delete.

(Optional) Automatically Run on Startup
---------------------------------------

* Windows using Startup Folder:

    Add a shortcut to ``lendingbot.py`` to the startup folder of the start menu.
    Its location may change with OS version, but for Windows 8/10 is ``C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp``

* Linux using systemd:

    Create the file ``/lib/systemd/system/lendingbot.service`` which contains the following text

    .. code-block:: text

        [Unit]
        Description=LendingBot service
        After=network.target

        [Service]
        Type=simple
        ExecStart=/usr/bin/python <INSTALLATION DIRECTORY>/lendingbot.py
        WorkingDirectory=<INSTALLATION DIRECTORY>
        RestartSec=10
        Restart=on-failure

        [Install]
        WantedBy=multi-user.target

    Credit to GitHub user utdrmac.
    
    
    The permission on the unit file may need to be set to 644 (depending on your OS) :
    
    ```
       sudo chmod 644 /lib/systemd/system/lendingbot.service
    ```

    Modify the ExecStart and WorkingDirectory to match your setup.
    
    First you need to configure systemd (depending on your OS):
    ```
        sudo systemctl daemon-reload
    ```

    Enable the service using the command below:
    ```
        sudo systemctl enable lendingbot.service
    ```

* OSx:

    Help needed! If you have a solution for OSx and would like to share, you can either share it directly with us or make a PR with the edits.

Configuring
-----------

You have to configure the bot, especially choosing the exchange  and api key/secret to use.

To configure the bot with your settings:

    #. Copy ``default.cfg.example`` to ``default.cfg`` (Running lendingbot.py also does this for you if default.cfg doesn't already exist.)
    #. Open ``default.cfg`` and enter your desired settings `(information on settings here) <http://poloniexlendingbot.readthedocs.io/en/latest/configuration.html>`_.
    #. Save ``default.cfg``

You are now ready to run the bot.

Running
-------

To run, either:

    - Double-click lendingbot.py (if you have .py associated with the Python executable)
    - Run ``python lendingbot.py`` in command prompt or terminal.

.. note:: You can use arguments to specify a specific config file ``-cfg`` or to do dry runs ``-dry``. To see these args do: ``python lendingbot.py -h``

Installing on Pythonanywhere.com
================================

`Pythonanywhere.com <https://www.pythonanywhere.com>`_ is a useful website that will host and run Python code for you. 

WARNING: While you should be able to setup the bot on pythonanywhere, there are limitations on running the bot.

Prerequisites
-------------

You will need:

    - A pythonanywhere.com account (Free version works fine)

Downloading the bot's files to Pythonanywhere
---------------------------------------------

#. Start a new ``bash`` console from the "Consoles" tab.
#. Get the source code from git GitHub by running ``git clone https://github.com/Mikadily/poloniexlendingbot``.
#. You should see some output with counters increasing.
#. Change directory to the source code ``cd poloniexlendingbot``
#. You should now see ``~/poloniexlendingbot (master)$`` this means you are looking at the master branch and things are ok to continue.
#. Run the command ``python2.7 lendingbot.py`` once to generate the default.cfg
#. Modify the default.cfg with your settings (See  `Configuration <http://poloniexlendingbot.readthedocs.io/en/latest/configuration.html>`_.) You can do this with a tool called nano.
#. Run ``nano default.cfg``, then use the arrow keys and backspace key to change ``YourAPIKey`` and ``YourSecret``. Make sure the layout of the file stays the same as it was. They should both be on separate lines.
#. Press ``Ctr+x`` to exit, then press ``y`` to save the file, then press enter to accept the file name as ``default.cfg``.
#. Now you can start up the bot. Run ``python2.7 lendingbot.py``
#. If it's working you will see ``Welcome to Poloniex Lending Bot`` displayed in the console.
#. To update the bot just enter its directory, ``cd poloniexlendingbot`` and type, ``git pull``. This will not change the ``default.cfg`` file.

.. note:: If you are running out of CPU time every day: It is recommended to use a high sleeptimeinactive time for this website, as they meter your CPU usage.

Creating the Web App (Optional)
-------------------------------

#. If you would like to use the Webserver to view your bot's status, navigate to the "Web" tab.
#. Add a new web app.
#. Set the working directory to ``/home/<username>/poloniexlendingbot/www/``
#. Set the static files to URL: ``/static/`` Directory: ``/home/<username>/poloniexlendingbot/www``
#. Reload your website with the button at the top of the page.
#. You will be able to access the webapp at ``http://<username>.pythonanywhere.com/static/lendingbot.html`` once it finishes setting up.
#. To have the webserver communicate with your bot, you need to edit your settings (``default.cfg``) and uncomment (remove the ``#`` in front of) the following settings: ``jsonfile`` and ``jsonlogsize``. Make sure that ``startWebServer`` REMAINS commented.


.. warning:: Do not use the built-in Simple Web Server on any host you do not control.

Running the Bot
---------------

To run the bot continuously (Recommended for free accounts):

    #. Navigate to the "Consoles" tab.
    #. Add a new "Custom console," name it "Poloniexlendingbot" and set the path to ``python /home/<username>/poloniexlendingbot/lendingbot.py``
    #. Click this link whenever you want to start the bot, it will run continuously until the website goes down for maintenance or the bot experiences an unexpected error.

To have the bot restart itself every 24 hours, you need to have a `premium pythonanywhere account <https://www.pythonanywhere.com/pricing/>`_. This will make the bot more or less invincible to crashes and resets, but is not necessary.

    #. Navigate to the "Schedule" tab.
    #. Create a new task to run daily (time does not matter) set the path to: ``python /home/<username>/poloniexlendingbot/lendingbot.py``
    #. The bot will start once the time comes (UTC) and run indefinitely.

.. note:: If you are a free user, it will allow you to make the scheduled restart, but then it will only run for one hour and stop for 23.
.. note:: Free users are also limited to the number of output currencies they can use as blockchain.info is blocked from their servers. You can always use the pairs listed on poloniex, BTC, USDT. But will not have access to currencies such as EUR, GBP.

Using Docker Compose
====================

There is a ``docker-compose.yaml`` file in the root of the source that can be used to start the bot via `docker <https://www.docker.com/>`_.  Compose is a tool for defining and running docker applications using a single file to configure the application’s services.

By default this file will start 3 containers:

  - An nginx reverse proxy
    This allows you to have the nginx web server as the main access point for the other bot's web pages.
    It uses `jwilder/nginx-proxy <https://github.com/jwilder/nginx-proxy>`_
  - A python container running the bot on poloniex. 
    This starts a bot running that connects to poloniex and exposes a web interface. 
    It uses `python:2.7-slim <https://hub.docker.com/r/library/python/tags/>`_
  - A python container running the bot on bitfinex. 
    This starts a bot running that connects to bitfinex and exposes a web interface. 
    It uses `python:2.7-slim <https://hub.docker.com/r/library/python/tags/>`_

This allows for simple deployments on a VPS or dedicated server. Each bot will be dynamically assinged a subdomain. 
You can also use it to run the bots locally using subdomains.

To use this file:-

  #. Install and setup `docker <https://www.docker.com/>`_ for your platform, available on linux, mac and windows.
  #. If you are using linux or windows server, you'll need to install docker-compose separately, see `here <https://docs.docker.com/compose/install/>`_.
  #. If you don't already have a ``default.cfg`` created, then copy the example one and change the values as required using the instructions in this document.
  #. Edit the ``docker-compose.yaml`` file and add your ``API_apikey`` and ``API_apisecret`` for each exchange. If you wish to use only one exchange, you can comment out all the lines for the one you don't need.
  #. If you are running locally, you can leave the ``VIRTUAL_HOST`` variable as it is. If you are running on a web server with your won domain, you can set it to something like ``poloniex.mydomain.com``.
  #. If you don't have a domain name, you can use a service such as `duckdns <http://duckdns.org>`_ to get one for free.
  #. You can now start the service with ``docker-compose up -d``. It may take a minute or two on the first run as it has to download the required image and then some packages for that image when it starts.
  #. If all went well you should see something like ``Starting bitbotfactory_bot_1``.
  #. When you see that message it just means that the container was started successfully, we still need to check the application is running as expected. In the yaml file the web service in the container is mapped to localhost. So you can open your web browser at this point and see if you can connect to the serivce. It should be runnning on `<http://127.0.0.1/>`_. You should see an nginx welcome page.
  #. If you don't see anything when connecting to that you can check the logs of the container with ``docker-compose logs``. You should get some useful information from there. Ask on Slack if you're stuck.
  #. If you are running locally you will need to add the subdomains to your hosts file to make sure they are resolved by DNS. You can ignore this step if you're running on a web server. On linux (and recent OSx) you can add these lines to ``/etc/hosts``, on windows you shoud follow this `guide <https://support.rackspace.com/how-to/modify-your-hosts-file/>`_

       .. code-block:: text

          127.0.0.1 poloniex.localhost
          127.0.0.1 bitfinex.localhost

  #. You should now be able to point your browser at `<http://poloniex.localhost>`_ and `<http://bitfinex.localhost/>`_ to see the web pages for each bot.

Extending the file:-

    - Most config values from default.cfg can be overridden in the docker-compose file. You should add them in the enviroment section in the same format as the ones listed. i.e. ``Category_Option``
    - You can add as many extra bots as you want. Each one will need to have a new ``VIRTUAL_HOST`` entry.
    - If you prefer to have everything in config files rather than enviroment variables, you can create a new cfg file for each bot and modify the ``command`` line to use that cfg file instead.

Other info:-

  - Each bot will create a log file in the root of your git checkout.
  - If you are using market analysis, you only need one bot per exchange. Extra bots will be able to share the database.
  - When you change the config values you need to restart the container, this can be done with ``docker-compose stop`` and then after changing configs, ``docker-compose up -d``. You should notice it's significantly quicker than the first run now.
  - The last command to note is ``docker-compose ps`` this will give infomation on all running instances and the ports that are mapped. This can be useful if you plan on running multiple bots, or you just want to know if it's running.
