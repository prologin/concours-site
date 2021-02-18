# Hacking on the website using Docker

## Requirements

You need **Docker** and **Docker Compose**.

## Getting started

The first time you want to run the website in a container, you should only
run `docker_init.sh`. The script will build the image *prologin_site* and run
four services (containers):
* prologin_site (Django website)
* prologin_site_db (**postgresql** database)
* prologin_celery_worker (celery worker for jobs queuing)
* prologin_redis (**redis** databse for the celery worker)

It will then build the assets for the website, apply database migrations and
collect static files.

Finally, it will ask you to create a Django superuser (for access to Django
admin) and a Prologin edition.

## Run the website

After the containers have been created, every time you want to run the
website, you should run `docker-compose up` in this directory.

*Note:* You don't need to run all services (*prologin_celery_worker* is
optional) so you can simply run `docker-compose up prologin_site`. However if
you do not run the celery worker, some features will be unavailable such as
submitting code to camisole.

## Configuration tips

Django settings file used in this setup is `docker_dev.py`.

### Using OAuth

If you want to be able to log in the GCC! website using [django-proloauth-client](https://github.com/prologin/django-proloauth-client) (that will be replaced by a new OIDC authentication in the future), you will probably need to change `AUTH_TOKEN_CLIENTS` to match the IP of your GCC! website.

*Tip:* To get the IPs of a running Docker container, run the following command:
```bash
docker inspect --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' <container>
```

If you are running Prologin and GCC! websites in container and using OAuth, you need to access them using their own IP (instead of `localhost`).
