# Installation

First you need to install the dependencies (example in a debian-like system):

    :::console
    # aptitude install python python-virtualenv unzip
    $ git clone git@bitbucket.org:prologin/site.git && cd site
    $ virtualenv . && source bin/activate
    $ pip install -r requirements.txt

Then follow these steps:

    :::console
    $ cd prologin/static && wget http://www.prologin.org/files/team.zip && unzip team.zip && rm team.zip && cd ../..
