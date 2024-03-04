### Create the initial database role and database for the django app

Login to the postgresql container `docker compose exec db /bin/bash` and then connect to the database `psql -U postgres` and run the following SQL statements:

```
create role coffee_run superuser createdb login;
alter role coffee_run password 'caffeine';
create database coffee_run_db;
```

### Run the setup steps for django

Login to the django app container `docker compose exec app /bin/bash` and then run the following commands from the shell

```
cd coffee_run
python manage.py createsuperuser
python manage.py migrate
```