# Installation

## Requirements

* Git
* Python 3
* NPM (for Javascript & CSS assets)
* PostgreSQL
* Redis (for training & contest)
* texlive (for latexmk, pdflatex, and a few packages).

### Archlinux

```bash
sudo pacman -S --needed git python3 npm postgresql redis texlive-core
```

### Ubuntu / Debian ≥ 10 (buster)

```bash
sudo apt install git python3 python3-venv postgresql redis texlive
```

### Debian ≤ 9 (stretch)

```bash
curl https://deb.nodesource.com/setup_8.x | sudo bash
sudo apt install git python3 python3-venv postgresql redis texlive nodejs
```

## Cloning

You obviously need to clone the website. You will also need the problem
repository, for training/contest to work. `--depth=1` is a convenient flag to
reduce the amount of downloaded data by ignoring the git history. Remove this
flag if you think you will need to work on `problems`.

```bash
# Do this once!
git clone git@github.com:prologin/site
git clone --depth=1 git@github.com:prologin/problems
```

## Python dependencies

It is recommended to use a virtualenv to isolate Prologin Python environment.

```bash
cd site
python3 -m venv .venv # Do this once!
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Web dependencies

Download the web dependencies from NPM:

```bash
( cd assets && npm install )
```

## Configuration

Copy the sample configuration to a file of your choice. I recommend to use
`prod.py` for a production environment and anything else, eg. `dev.py`, for a
development environment:

```bash
# Do this once!
cd /path/to/site
cp prologin/prologin/settings/{conf.sample,dev}.py
```

Then, check the following settings in the file you copied:

1. Uncomment and update `PROLOGIN_EDITION` to the current edition year.
2. Uncomment and update `PROBLEMS_REPOSITORY_PATH` to the directory where you
   cloned the Prologin [`problems`
   repository](https://github.com/prologin/problems).
3. Uncomment and update `DOCUMENTS_REPOSITORY_PATH` to the directory where you
   cloned the Prologin [`documents`
   repository](https://github.com/prologin/documents).
4. Add a local or remote correction VM to `PROBLEMS_CORRECTORS`.
5. Uncomment and update `RECAPTCHA_{PUBLIC,PRIVATE}_KEY`. You can leave them
   empty for most tests.
6. It is required to setup a local Postgres database, the default configuration
   file uses database name *prologin*:
    ```python
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'prologin',
        }
    }
    ```

Now proceed to the sub-section corresponding to your environment for specific
instructions.

### Development setup

* *Django Debug Toolbar* is here to help; you can use it by adding the following
  lines to your settings:
    ```python
    INSTALLED_APPS += ('debug_toolbar',)

    MIDDLEWARE += ('debug_toolbar.middleware.DebugToolbarMiddleware',)
    ```
* You may need to customize the Redis URI. Check the database index (0 by
  default) so it does not clash with your other data if you use this Redis
  instance for other stuff.

### Production setup

* Set `DEBUG = False`.
* Remember you need to start Django from the right virtualenv and with the right
  settings, so you have to set the environment variable
  `DJANGO_SETTINGS_MODULE=prologin.settings.prod`.
* You need to launch one or more Celery workers.
    ```bash
    celery -l warning -A prologin worker
    ```

## Creating the database

```bash
cd prologin && python manage.py migrate
```

On macOS, if you get an `ImportError: MagickWand shared library not found.`, you
can refer to this [StackOverflow answer](
https://stackoverflow.com/questions/37011291/python-wand-image-is-not-recognized/41772062#41772062)
to fix it.

## Creating the minimal context

The website has to display some data about the current Prologin edition,
upcoming events, and the like. That is why it is necessary to setup at least one
`Edition` and the corresponding qualification (a.ka. QCM) `Event`. As the
website crashes intentionally without theses minimal objects, you can not add
them using the admin. Use the `edition` command instead:

```bash
cd prologin && python manage.py edition create
# Answer the questions
```

## Developing the website

Every time you need to work on the website:

1. Enter the virtualenv:
    ```bash
    source .venv/bin/activate
    ```
2. Load the right settings:
    ```bash
    # If you named your settings 'dev.py':
    export DJANGO_SETTINGS_MODULE=prologin.settings.dev
    ```
3. Launch the local dev server:
    ```bash
    make runserver
    ```
4. *If needed*, you can launch a debug SMTP server to check that mails are
   correctly sent with the right content. This will print the outbound mails on
   the console.
    ```bash
    make smtpserver
    ```
5. *If needed* (training & contest submissions), you can launch a debug celery
   worker:
    ```bash
    make celeryworker
    ```

### Translations

The website user-facing strings are internationalized through Django's internal
i18n framework.

You can translate the strings locally by editing the `.po` files in your editor
or using a dedicated software such as [poedit](https://poedit.net/).

To ease the *community* translation process, it is possible to upload the
untranslated (English) strings to Transifex, ask people to translate them (eg.
using the Transifex web app) and download them back to the repository.
To that end, use the provided `make` commands:

```bash
# I've created/update source (English) strings, let's push them
# (we pull before to update local strings just in case)
make tx-pull tx-push
# ... translate on Transifex ...
# Get back the translated strings
make tx-pull
# Commit
git commit prologin/locale -m 'locale: update for <feature>'
```

## Deploying the regional event environment

### Exporting user data from production website

Go to https://prologin.org/docs/ and use the “*Data export*” orange button to
obtain a JSON file you have to copy to the machine hosting the regional event
website.

### Installing the regional event website

Follow the generic how-to, with the following differences:

* create the settings (eg. `prologin/settings/semifinal.py`) using the following
  template:
    ```bash
    cp prologin/prologin/settings/{semifinal.sample,semifinal}.py
    ```
* edit the settings to match your database, edition, correctors etc.
* do *not* create the minimal context;
* don't forget to migrate the database for the next step;
* import the user data you previously exported:
    ```bash
    # activate venv, export DJANGO_SETTINGS_MODULE
    python manage.py semifinal_bootstrap export-semifinal-2016-whatever.json
    ```
* during the initial setup, you may want to set `DEBUG = True` in the settings.
  Do not forget to **set it to `False` during the contest**.

## Tips and tricks

* On old systems using Python 2 as default, replace all `python` invocation by
  `python3` or equivalent. Better: use a virtualenv with python3 by default.
* If the `prologin/settings/conf.example.py` file changed upstream, you may need
  to adapt your local settings consequently.
* Don't put any file in `prologin/static/`. All the static files must be located
  in their application's static folder (eg: `prologin/team/static/team/`). If
  you uses the internal web server everything will work just fine. On production
  servers, use `collectstatic` (see above).
* Namespace template files. When writing the `index.html` template for the `foo`
  app, store it in `prologin/foo/templates/foo/index.html` (note the `foo`
  subfolder).
* Always check your ORM queries for queries-in-a-loop. Use the *Debug Toolbar*
  at this end. Rule of thumb: if the number of queries depends on the number of
  displayed/processed items in your template/view, you are doing it wrong.
  Check [Django database
  optimization](https://docs.djangoproject.com/en/1.8/topics/db/optimization/)
  for more tips.
* Please try to be [PEP8](https://www.python.org/dev/peps/pep-0008/) compliant.
  There are many tools to check and format your code.


# Other tasks

## Assets regeneration

You can regenerate some of the assets committed in the repository, if for
instance you changed the source files or the asset generation process.

### Dependencies

Generating the assets require additional dependencies.

For Debian/Ubuntu:

```bash
sudo apt install inkscape optipng
```

For Archlinux:

```bash
sudo pacman -S inkscape optipng
```

### Generating the assets

Once you have the required image processing dependencies, you can force a
regeneration of all the assets using:

```bash
make -B assets
```

You can then `git add` the modified files that you want to update in the
repository.

### Using Docker

You can also generate the assets using docker instead.

```bash
./docker_assets_builder.sh
```
