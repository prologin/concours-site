# Prologin website

## Table of Contents

* [Table of Contents](#table-of-contents)
* [Installation](#installation)
* [Hacking on the website](#hacking-on-the-website)
* [Deploying the regional event environment](#deploying-the-regional-event-environment)
* [Troubleshooting](#troubleshooting)

## Installation

### Requirements

Running the Prologin website requires the following dependencies:

* Git
* Python 3
* NPM (for Javascript & CSS assets)
* PostgreSQL
* Redis (for training & contest)
* texlive (for latexmk, pdflatex, and a few packages).

You can use the following commands to install those dependencies:

- For **Archlinux**:

  ```bash
  sudo pacman -S --needed git python3 npm postgresql redis texlive-core
  ```

- For **Ubuntu** and **Debian ≥ 10 (buster)**:

  ```bash
  sudo apt install git python3 python3-venv postgresql redis texlive
  ```

- For **Debian ≤ 9 (stretch)**

  ```bash
  curl https://deb.nodesource.com/setup_8.x | sudo bash
  sudo apt install git python3 python3-venv postgresql redis texlive nodejs
  ```

### PostgreSQL Setup

You need to have access to a running PostgreSQL instance to setup the Prologin
database. If you don't have that already, this section contains information to
setup PostgreSQL for the first time:

- for **Ubuntu** and **Debian**, the previous step (installation) should be
  enough.

- for **Archlinux**, you have to initialize the database cluster and enable
  `postgresql.service`:

  ```bash
  sudo -u postgres initdb -D '/var/lib/postgres/data'
  sudo systemctl enable --now postgresql
  ```

- for **other platforms** and more information, refer to the
  [PostgreSQL installation documentation
  ](https://www.postgresql.org/docs/current/static/tutorial-install.html).

Once PostgreSQL is running, you also need an user that will have access to the
Prologin database. The easiest way to achieve that is simply to create an
account that has the same name as your username and that can create databases:

```bash
sudo -u postgres createuser --createdb $USER
```

### Cloning

Clone the website and, optionally, the other Prologin repositories needed for
the different modules of the website:

```bash
git clone git@github.com:prologin/site
git clone git@github.com:prologin/problems   # Training exercises (private)
git clone git@github.com:prologin/archives   # Edition archives (private)
git clone git@github.com:prologin/documents  # Admin. documents (private)
```

Then, enter the website directory:

```
cd site
```

### Python virtualenv & dependencies

Use a [virtual environment](https://docs.python.org/3/library/venv.html) to
install the Python dependencies of the website:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip -r requirements.txt
```

### Web dependencies

Download the web dependencies from NPM:

```bash
( cd assets && npm install )
```

### Configuration

Copy the sample configuration to a file of your choice. I recommend to use
`dev.py` for a development environment:

```bash
cp prologin/prologin/settings/{conf.sample,dev}.py
```

The default settings should work by default if you are following this guide,
but if needed, you can edit `prologin/prologin/settings/dev.py` to adjust some
settings.

### Creating the database

Create the `prologin` PostgreSQL database, and run the migrations :

```bash
createdb prologin
./manage.py migrate
```

### Creating the minimal context

(**Note**: If you would rather work with an **anonymized database dump** of the
website, ask one of the Prologin roots to provide you one.)

The website has to display some data about the current Prologin edition,
upcoming events, and the like. That is why it is necessary to setup at least
one `Edition` and the corresponding qualification (a.ka. QCM) `Event`. As the
website crashes intentionally without theses minimal objects, you can not add
them using the admin. Use the `edition` command instead:

```bash
cd prologin && ./manage.py edition create
# Answer the questions
```

## Hacking on the website

Every time you need to work on the website:

1. Enter the virtualenv:
    ```bash
    source .venv/bin/activate
    ```
2. Launch the local dev server:
    ```bash
    make runserver
    ```
3. *If needed*, you can launch a debug SMTP server to check that mails are
   correctly sent with the right content. This will print the outbound mails on
   the console.
    ```bash
    make smtpserver
    ```
4. *If needed* (training & contest submissions), you can launch a debug celery
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

Follow the generic installation procedure, with the following differences:

* create the semifinal settings (eg. `prologin/settings/semifinal.py`) using
  the following template:
    ```bash
    cp prologin/prologin/settings/{semifinal.sample,semifinal}.py
    ```
* check that the settings match your database, edition, correctors etc.
* do *not* create the minimal context;
* don't forget to migrate the database for the next step;
* import the user data you previously exported:
    ```bash
    # activate venv, export DJANGO_SETTINGS_MODULE
    ./manage.py semifinal_bootstrap export-semifinal-2016-whatever.json
    ```
* during the initial setup, you may want to set `DEBUG = True` in the settings.
  Do not forget to **set it to `False` during the contest**.

## Troubleshooting

### On macOS, error: "`ImportError: MagickWand shared library not found.`".

You can refer to this
[StackOverflow answer](https://stackoverflow.com/a/41772062/1408435)
to fix the problem.
