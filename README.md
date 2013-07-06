# Installation

First you need to install the dependencies (example in a debian-like system):

    :::console
    # aptitude install python python-virtualenv unzip
    $ git clone git@bitbucket.org:prologin/site.git && cd site
    $ virtualenv . && source bin/activate
    $ pip install -r requirements.txt

Then follow these steps:

    :::console
    $ cd prologin/team/static/team/ && wget http://www.prologin.org/files/team.zip && unzip team.zip && rm team.zip && cd ../../../

Don't forget to change the configuration in `prologin/prologin/settings.py` (tip: search for `CHANGEME` within the conf).

## Static files

Don't put any file in `prologin/static/`. All the static files must be located in their application's static folder (eg: `prologin/team/static/team/`). If you uses the internal web server everything will work just fine. On production servers, you should use `python manage.py collectstatic` to populate `prologin/static/` with the static files.
