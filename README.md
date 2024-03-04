### Installation

Check out the repository and from the project root run `docker compose up --build --detach`

### Create the initial database role and database for the django app

Login to the postgresql container `docker compose exec db /bin/bash` and then connect to the database `psql -U postgres` and run the following SQL statements:

```
create role coffee_run superuser createdb login;
alter role coffee_run password 'caffeine';
create database coffee_run_db;
```

It's also possible to connect directly to the database container without going into a shell inside the container. The `psql` client (or some other database client) is needed for this but it should be possible to connect to the container. The host is `localhost` and the port is `5432`. The default database superuser is named `postgres` and has password `postgres`.

### Run the setup steps for django

Login to the django app container `docker compose exec app /bin/bash` and then run the following commands from the shell. Creating a system superuser isn't strictly necessary but it does allow access to the Django admin site, which is nice sometimes. Running the migrations is required though. 

```
cd coffee_run
python manage.py createsuperuser
python manage.py migrate
```

### Running the tests

Login to the django app container `docker compose exec app /bin/bash` and then run the following commands from the shell.

```
cd coffee_run
python manage.py test
```

### Setting Up the System with initial data

The only data that must be created in order to start placing group orders is user data. This can be done through the main web UI by navigating to the create user page `http://localhost:8000/users/create/`. As an alternative, this can be done using the Django admin site, which has a prettier interface. The admin page for this is here `http://localhost:8000/admin/payments/user/`. Be sure to select the `payments/user` as opposed to the `auth/user` if you're using the Django admin page. 

### Accessing the web site in your browser

Navigate to `localhost:8000` to get the index page. 

### Some Discussion about my assumptions and some design decisions

First and foremost, I considered the use case for an app like this in terms of what would the human users of the system benefit from and find useful. I determined that a web interface was well suited to the problem the users are trying to solve, so this ruled out a CLI tool or other kind of backend-only system. I chose to use Django to streamline the development of the web app. I have deliberately chosen an ultra-minimalistic UI using only plain HTML and vanilla JS. This made my development process easier and it guarantees that the site will be able to run on any modern browser.

Second, I considered what kind of definition of fairness might be agreeable to the human users of the system as well as easy to implement in a way that could be tested against a reasonable metric. I settled on the definition where the system is fair if the average net credit of any user in the system is never far from zero, where the acceptable distance from zero is a function of the maximum price of an order in the system. The fairness algorithm is designed such that as the number of group orders approaches LARGE_NUMBER the average net credit approaches zero. In real money terms, this means that the more a user participants in the system the more fair it becomes. The system is also approximately fair at SMALL_NUMBER of group orders, but the variance is higher for smaller numbers. 

A summary of how the algorithm works: when a group order is placed, the system finds the user participating in the order with the highest net credit, representing the user who has up to this point paid in the least. The system selects this user as the payer for the group order and adjusts the net credit of every user in the order to reflect the order, including the payer, who's net credit is reduced by the cost of the order. When there is a tie for net credit the payer is chosen as the user who has least recently paid for a group order. I like this definition of fairness because it prevents any user from accumulating too much credit or debit over time, trying to keep each user's net credit close to zero. It also fairly selects payers on the basis of the price of their preferred order items. A user who habitually orders expensive items will accumulate net credit faster, and will be chosen as the payer more frequently because of this. A user who habitually orders cheap items will accumulate net credit slowly and will be chosen as the payer less frequently. 

Finally, I wanted the system to be flexible in two respects. 

First, I wanted the system to be flexible with respect to users participating in a group order. It would be inconvenient or even useless if the system could only serve a fixed set of users. What do you do if someone doesn't come along on a coffee run one day? Or what if a user wants to order multiple items? Or to gift an item to someone? So to satisfy these requirements I created a system where a group order can have 1 or more order items, and there are no restrictions on how many order items a user can put in an order. 

Second, I wanted to be as flexible as possible about what items a user can order. A fixed menu would be very annoying to deal with. Every time the group went to a different cafe, or even if the usual cafe changed their menu, that would require someone to manually reconfigure the system to match it. Very annoying. Instead, the system only requires the most basic information about an order item: who bought it, the name of it, and how much it costs. No configuration is required. Order items are persisted in the system for record keeping purposes, but this is immutable data in the system. New order items are created for each new group order. This means there is a bit of denormalization in the database, but that's the tradeoff made for this kind of flexibility. 

