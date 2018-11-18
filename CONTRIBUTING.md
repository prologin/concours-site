# Contributing

## Tips and tricks

* If the `prologin/settings/conf.example.py` file changed upstream, you may
  need to adapt your local settings consequently.
* Don't put any file in `prologin/static/`. All the static files must be
  located in their application's static folder (eg:
  `prologin/team/static/team/`). If you uses the internal web server everything
  will work just fine. On production servers, use `collectstatic` (see above).
* Namespace template files. When writing the `index.html` template for the
  `foo` app, store it in `prologin/foo/templates/foo/index.html` (note the
  `foo` subfolder).
* Always check your ORM queries for queries-in-a-loop. Use the *Debug Toolbar*
  at this end. Rule of thumb: if the number of queries depends on the number of
  displayed/processed items in your template/view, you are doing it wrong.
  Check [Django database
  optimization](https://docs.djangoproject.com/en/1.8/topics/db/optimization/)
  for more tips.
* Please try to be [PEP8](https://www.python.org/dev/peps/pep-0008/) compliant.
  There are many tools to check and format your code.

## Recurring tasks

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
