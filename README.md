# Installation


## Requirements

* Python 2
* Django 1.5
* Maybe some stuff listed in requirements.txt


## Installing the website itself

* Clone the repository: `git clone git@bitbucket.org:prologin/site.git`
* Go to the website directory: `cd site/prologin/`
* Create the configuration file and _EDIT IT_: `cp prologin/settings.py.example prologin/settings.py` (tip: search for `CHANGEME`)
* Create the database: `python manage.py syncdb`


## Static files

Don't put any file in `prologin/static/`. All the static files must be located in their application's static folder (eg: `prologin/team/static/team/`). If you uses the internal web server everything will work just fine. On production servers, you should use `python manage.py collectstatic` to populate `prologin/static/` with the static files.


## Loading dummy data

In order to test the website, you can load dummy data using `python manage.py fill_db type [type...]`
`type` can be `all` or n of the following values:

* users
* news
* team

To avoid dependencies issues, you should always specify the type in this order. Using `all` is safer.


## Tips and tricks

* On recent systems using Python 3 as default, replace all `python` invocation by `python2` or equivalent.
* If the `settings.py.example` file changed, you may want to adapt your `settings.py` consequently.
* Retriving some team members pictures: `cd team/static/team/ && wget http://www.prologin.org/files/team.zip && unzip team.zip && rm team.zip && cd ../../`



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
