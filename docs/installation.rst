.. highlight:: javascript

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
    - pip (to install Numpy)
    - Numpy (if using Analysis module)

Downloading
-----------

To download the bot you can either:

- (Recommended) Run ``git clone https://github.com/Mikadily/poloniexlendingbot`` if you have git installed. Using this method will allow you to do ``git pull`` at any time to grab updates.
- Download the source .zip file from the GitHub repo page or from `this link <https://github.com/Mikadily/poloniexlendingbot/archive/master.zip>`_. Extract it into an empty folder you won't accidentally delete.

(Optional) Automatically Run on Startup
---------------------------------------

* Windows using Startup Folder:

    Add a shortcut to ``lendingbot.py`` to the startup folder of the start menu.
    Its location may change with OS version, but for Windows 8/10 is ``C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp``

* Linux using systemd:

    Create the file ``/lib/systemd/system/lendingbot.service`` which contains the following text::

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

    Modify the ExecStart and WorkingDirectory to match your setup.
    
    Enable the service using ``sudo systemctl enable lendingbot.service``

* OSx:

    Help needed! If you have a solution for OSx and would like to share, you can either share it directly with us or make a PR with the edits.

Configuring
-----------

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

`Pythonanywhere.com <https://www.pythonanywhere.com>`_ is a useful website that will host and run Python code for you. This is perfect for our bot.

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
