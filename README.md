# Installation


## Requirements

* Python 3
* Every package from requirements.txt

## Installing the website

* Clone the repository: `git clone git@bitbucket.org:prologin/site.git`
* Go to the website directory: `cd site/prologin/`
* Create the configuration file and _EDIT IT_: `cp prologin/settings.py.example prologin/settings.py` (tip: search for `CHANGEME`)
* Create the database: `python manage.py syncdb --noinput`
* (optional) Loading some dummy data: `python manage.py fill_db all`


### Default users

Users created using `fill_db` are set as super-users and have the default password `plop`.


## Static files

Don't put any file in `prologin/static/`. All the static files must be located in their application's static folder (eg: `prologin/team/static/team/`). If you uses the internal web server everything will work just fine. On production servers, you should use `python manage.py collectstatic` to populate `prologin/static/` with the static files.


## Tips and tricks

* On old systems using Python 2 as default, replace all `python` invocation by `python3` or equivalent. Better: use a virtualenv with python3 by default.
* If the `settings.py.example` file changed, you may want to adapt your `settings.py` consequently.


# Work status

## Functional modules

* prologin
* team
* users

## Modules to rewrite

* centers
* contest
* documents
* forum
* pages
* problems

# Old readme

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
