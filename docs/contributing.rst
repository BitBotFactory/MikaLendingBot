3. Contributing
***************

3.1 How to format Python Code
=============================

If you want to make a successful pull request, `here are some suggestions. <http://blog.ploeh.dk/2015/01/15/10-tips-for-better-pull-requests/>`_

Recommended IDE: `PyCharm <https://www.jetbrains.com/pycharm/>`_

3.1.1 PEP8
----------

Poloniex lending bot follows `PEP8 styling guidelines <https://www.python.org/dev/peps/pep-0008/>`_ to maximize code readability and maintenance.

To help out users and automate much of the process, `the Hound Continuous Integration bot <https://houndci.com/configuration#python>`_ will comment on pull requests to alert you to any changes you need to make.
Hound follows ``flake8`` standards, which may extend past PEP8 conventions. We recommend you follow its suggestions as much as possible. 

To make following PEP8 as painless as possible, we strongly recommend using an Integrated Development Environment that features PEP8 suggestions, such as `PyCharm <https://www.jetbrains.com/pycharm/>`_.

3.1.2 Indent Style
------------------

You may have your own preference, it does not matter because *spaces and tabs do not mix.*

Poloniexlendingbot uses *spaces* to conform with PEP8 standards. Please use an IDE that can help you with this.

3.1.3 Commenting Code
---------------------

Many coders learned to code without commenting their logic.
That works if you are the only person working on the project, but quickly becomes a problem when it is your job to decipher what someone else was thinking when coding.

You will probably be relieved to read that code comments are not mandatory, because `code comments are an apology. <http://butunclebob.com/ArticleS.TimOttinger.ApologizeIncode>`_

Only comment your code if you are apologizing for writing confusing code or need to leave a note. (We won't judge you for it.)

3.1.4 Variable or Option Naming
-------------------------------

Whenever you create a variable or configuration option, we follow PEP8 standards, they are as follows:

Do not make global single-letter variable names, those do not help anybody. Using them within a function for a few lines in context is okay, but calling it much later should require it be given a proper name.

Functions are named like ``create_new_offer()`` and variables are named similarly, like ``amount_of_lends``.

3.1.5 Line Length
-----------------

To make it simple to review code in a diff viewer (and several other reasons) line length is limited to 128 characters in Python code.

Python allows plenty of features for one line to be split into multiple lines, those are permitted.
