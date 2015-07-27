# Installation


## Requirements

* Python 3
* Every package from requirements.txt (see recommended procedure below)
* Redis (for training & contest)

## Cloning

You obviously need the site source but also the problem repository, for
training/contest to work. `--depth=1` is a convenient flag to reduce the amount
of downloaded data by ignoring the git history. Remove this flag if you think
you will need to work on `problems`.

    :::console
    # Do this once!
    git clone git@bitbucket.org:prologin/site.git
    git clone --depth=1 git@bitbucket.org:prologin/problems.git

## Using a virtualenv

It is recommended to use a virtualenv to isolate Prologin Python environment.
While you can use the raw `virtualenv` tool, the following procedure makes good
use of the [`pew` tool](https://pypi.python.org/pypi/pew/).

    :::console
    # Do this once!
    cd /path/to/site
    # If Python 3 executable is 'python3'
    pew new -p $(which python3) -r requirements.txt prologin-site
    # If Python 3 executable is 'python' (eg. ArchLinux)
    pew new -r requirements.txt prologin-site
    pew setproject "$PWD"

## Configuration

Copy the sample configuration to a file of your choice. I recommend to use
`prod.py` for a production environment and anything else, eg. `dev.py`, for
a development environment:

    :::console
    # Do this once!
    cd /path/to/site
    cp prologin/prologin/settings/{conf.sample,dev}.py

Then, check the following settings in the file you copied:

1. Uncomment and update `PROLOGIN_EDITION` to the current edition year.
1. Uncomment and update `TRAINING_PROBLEM_REPOSITORY_PATH` to the directory where
   you cloned the Prologin [`problem` repository](https://bitbucket.org/prologin/problems/).
1. Add a local or remote correction VM to `TRAINING_CORRECTORS`.

Now proceed to the sub-section corresponding to your environment for specific
instructions.

### Development setup

* *Django Debug Toolbar* is here to help; use it. If you don't want to, disable
  it to get better performances by commenting/removing the line:

        :::python
        INSTALLED_APPS += ('debug_toolbar',)

* By default a SQLite3 (file based) database is used. Disclaimer: this is
  convenient but *performance is poor*. It is thus recommended to setup a local
  Postgres database and use that instead. If you do choose to use Postgres,
  change `dev.py` accordingly:

        :::python
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql_psycopg2',
                'HOST': 'localhost',
                'NAME': 'prologin',
                'USER': 'prologin',
                'PASSWORD': 'prologin',
            }
        }

* You may need to customize the Redis URI. Check the database index (0 by
  default) so it does not clash with your other data if you use this Redis
  instance for other stuff.

### Production setup

* Set `DEBUG = False`.
* Remember you need to start Django from the right virtualenv and with the right settings,
  so you have to set the environment variable `DJANGO_SETTINGS_MODULE=prologin.settings.prod`.
* You need to launch one or more Celery workers.

        :::console
        celery -l warning -A prologin worker

## Creating the database

    :::console
    cd prologin && python manage.py migrate

## Creating the minimal context

The website has to display some data about the current Prologin edition, upcoming events,
and the like. That is why it is necessary to setup at least one `Edition` and the
corresponding qualification (a.ka. QCM) `Event`. As the website crashes intentionally
without theses minimal objects, you can not add them using the admin. Use the `edition`
command instead:

    :::console
    cd prologin && python manage.py edition
    # Answer the questions

## Importing data from the old website

TODO.

## Developing the website

Every time you need to work on the website:

1. Enter the virtualenv, eg. with pew:

        :::console
        pew workon prologin-site

1. Load the right settings:

        :::console
        # If you named your settings 'dev.py':
        export DJANGO_SETTINGS_MODULE=prologin.settings.dev 

1. Launch the local dev server:

        :::console
        make runserver

1. *If needed*, you can launch a debug SMTP server to check that mails are
   correctly sent with the right content. This will print the outbound mails
   on the console.
   
        :::console
        make smtpserver
    
1. *If needed* (training & contest submissions), you can launch a debug celery
   worker:
    
        :::console
        make celeryworker


## Tips and tricks

* On old systems using Python 2 as default, replace all `python` invocation by `python3` or equivalent. Better: use a virtualenv with python3 by default.
* If the `prologin/settings/conf.example.py` file changed upstream, you may need to adapt your local settings consequently.
* Don't put any file in `prologin/static/`. All the static files must be
  located in their application's static folder
  (eg: `prologin/team/static/team/`). If you uses the internal web server 
  everything will work just fine. On production servers, use `collectstatic`
  (see above).
* Namespace template files. When writing the `index.html` template for the
  `foo` app, store it in `prologin/foo/templates/foo/index.html` (note the
  `foo` subfolder).
* Always check your ORM queries for queries-in-a-loop. Use the *Debug Toolbar*
  at this end. Rule of thumb: if the number of queries depends on the number
  of displayed/processed items in your template/view, you are doing it wrong.
  Check [Django database optimization](https://docs.djangoproject.com/en/1.8/topics/db/optimization/)
  for more tips.
* Please try to be [PEP8](https://www.python.org/dev/peps/pep-0008/) compliant.
  There are many tools to check and format your code.