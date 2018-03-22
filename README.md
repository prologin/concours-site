# Installation

## Requirements

* Python 3
* Every package from requirements.txt (see recommended procedure below)
* Redis (for training & contest)
* optipng (used for assets generation)
* jq (used for assets generation)
* texlive (for latexmk, pdflatex, and a few packages).

## Cloning

You obviously need the site source and its submodules, thus you have to clone
this repository using the `--recursive` flag. You will also need the problem
repository, for training/contest to work. `--depth=1` is a convenient flag to
reduce the amount of downloaded data by ignoring the git history. Remove this
flag if you think you will need to work on `problems`.

    :::console
    # Do this once!
    git clone git@github.com:prologin/site
    git clone --depth=1 git@github.com:prologin/problems

## Using a virtualenv

It is recommended to use a virtualenv to isolate Prologin Python environment.

    :::console
    cd site
    # Do this once!
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

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
1. Uncomment and update `PROBLEMS_REPOSITORY_PATH` to the directory where
   you cloned the Prologin [`problems` repository](https://bitbucket.org/prologin/problems/).
1. Uncomment and update `DOCUMENTS_REPOSITORY_PATH` to the directory where
   you cloned the Prologin [`documents` repository](https://bitbucket.org/prologin/documents/).
1. Add a local or remote correction VM to `PROBLEMS_CORRECTORS`.
1. Uncomment and update `RECAPTCHA_{PUBLIC,PRIVATE}_KEY`. You can leave them
   empty for most tests.

Now proceed to the sub-section corresponding to your environment for specific
instructions.

## Asset generation

Some assets of the website do not live inside the repository to reduce its size.
We have to fetch them or generate them using scripts. To do that, run:

    :::console
    # Generate the static assets
    make assets

This is broken at the moment (see
[#65](https://bitbucket.org/prologin/site/issues/65/assets-zopieux-must-fix-his-shit)
), so you'll have to do without the assets. The emojis are required for
the migrations, so the current workaround is

	:::console
	# Set an empty emoji list
	echo 'EMOJIS = {}' > prologin/prologin/utils/markdown/emoji_list.py

If you really need the assets, ask Zopieux.

> <seirl> n'oublie pas de le reping à chaque fois que make assets marche pas


### Development setup

* *Django Debug Toolbar* is here to help; you can use it by adding the
  following line to your settings:

        :::python
        INSTALLED_APPS += ('debug_toolbar',)
   
  You also need to add a middleware:

        :::python
        MIDDLEWARE += ('debug_toolbar.middleware.DebugToolbarMiddleware',)
   

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
    cd prologin && python manage.py edition create
    # Answer the questions


## Developing the website

Every time you need to work on the website:

1. Enter the virtualenv:

        :::console
        source .venv/bin/activate

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

### Translations

The website user-facing strings are internationalized through Django's internal
i18n framework.

You can translate the strings locally by editing the `.po` files in your editor
or using a dedicated software such as [poedit](https://poedit.net/).

To ease the *community* translation process, it is possible to upload the untranslated
(English) strings to Transifex, ask people to translate them (eg. using the
Transifex web app) and download them back to the repository.
To that end, use the provided `make` commands:

    :::console
    # I've created/update source (English) strings, let's push them
    # (we pull before to update local strings just in case)
    make tx-pull tx-push
    # ... translate on Transifex ...
    # Get back the translated strings
    make tx-pull
    # Commit
    git commit prologin/locale -m 'locale: update for <feature>'


## Deploying the regional event environment

### Exporting user data from production website

Go to <https://prologin.org/docs/> and use the “*Data export*” orange button to obtain a JSON file you have to copy
to the machine hosting the regional event website.

### Installing the regional event website

Follow the generic how-to, with the following differences:

* create the settings (eg. `prologin/settings/semifinal.py`) using the following template:

    cp prologin/prologin/settings/{semifinal.sample,semifinal}.py

* edit the settings to match your database, edition, correctors etc.
* do *not* create the minimal context;
* don't forget to migrate the database for the next step;
* import the user data you previously exported:

        # activate venv, export DJANGO_SETTINGS_MODULE
        $ python manage.py semifinal_bootstrap export-semifinal-2016-whatever.json

* during the initial setup, you may want to set `DEBUG = True` in the settings. Do not forget to **set it to `False`
  during the contest**.


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
