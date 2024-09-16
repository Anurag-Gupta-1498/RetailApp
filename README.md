# RetailApp
Django app for retail app

# Project Documentation :wave::wave:

## Python Requirements :memo:

- Python 3.8+

## Project Setup :wrench:

### Cloning the repo
1. Clone the repository using```git clone https://github.com/Anurag-Gupta-1498/RetailApp```
2. Switch to branch master using ```git checkout master```

### Creating a virtual environment
1. Create virtual environment using ```python3 -m virtualenv env```

2. Activate virtual env using ```source env/bin/activate (ubuntu)```

### Installing requirements
1. Install requirements.txt file using  - ```pip install -r requirements.txt```
2. Install Redis - sudo apt-get install redis (For Ubuntu)
3. Install Postgres and run the following commands - 
- sudo -u postgres psql (To enter the postgres shell)
- CREATE DATABASE retail_store_db;
- CREATE USER 'username' WITH PASSWORD 'password';
- GRANT ALL PRIVILEGES ON DATABASE retail_store_db TO username;

### Django project setup
1. Create .env file and add :key: ```DJANGO_SECRET_KEY = <YOUR_SECRET_KEY>```
2. Add username and password of the user of postgres in the .env file ```POSTGRES_USERNAME = <USERNAME> and POSTGRES_PASSWORD = <PASSWORD>```
3. Use python manage.py migrate
4. Use```python manage.py collectstatic --noinput```
5. Create superuser - python manage.py createsuperuser
6. To load data into database postgres, open python manage shell using ```python manage.py shell```and write the following script
7. For populating dummy data please run the following command - python populate_data.py 

## Testing :hourglass:

For testing run command ```python manage.py test transaction_system/```

## Running the project :running:

Now run the app using command ```python manage.py runserver```


### API testing

For api testing try the following commands

1. **To open Django Administration** :link: [Admin Pannel](http://127.0.0.1:8000/admin/ "Django Administration")

   Credentials
   username: Your superuser credentials

_**Here you would be able to see different tables of users, transactions, items and billitems**_

2. **For testing different apis:**
    
- **Authorization** :arrow_right: For using basic authorization use your superuser credentials
- **Get item Details Api** :arrow_right: Send a `GET` request from Postman using endpoint `/items/<item_code>` with basic authorization
   Example, http://127.0.0.1:8000/items/P001
- **Add Sales Data Api** :arrow_right: Send a `POST` request from Postman using endpoint `/add-sales` with basic authorization

   Example, http://127.0.0.1:8000/add-sales and body data={
  "items": [
    {
      "item_code": "P001",
      "quantity": "5"
    },
    {
      "item_code": "B001",
      "quantity": 5
    },
    {
      "item_code": "D001",
      "quantity": "10"
    },
    {
      "item_code": "D002",
      "quantity": 5
    }
  ]
}

- **Fetch Sales Summary Data Api** :arrow_right: Send a `GET` request from Postman using endpoint `/sales-summary` with basic authorization

   Example, http://127.0.0.1:8000/sales-summary

- **Fetch Average Sales Data Api** :arrow_right: Send a `GET` request from Postman using endpoint `/average-sales-summary` with basic authorization

   Example, http://127.0.0.1:8000/average-sales-summary?start_date=2024-09-5&end_date=2024-09-16

- **Generate Sales Report Api** :arrow_right: Send a `GET` request from Postman using endpoint `/sales-report` with basic authorization

   Example, http://127.0.0.1:8000/sales-report?start_date=2024-09-5&end_date=2024-09-16

- **Trend Analysis Data Api** :arrow_right: Send a `GET` request from Postman using endpoint `/trend-analysis` with basic authorization

   Example, http://127.0.0.1:8000/trend-analysis?start_date=2024-09-5&end_date=2024-09-16

- **Sales Comparison Data Api** :arrow_right: Send a `GET` request from Postman using endpoint `/sales-comparison` with basic authorization

   Example, http://127.0.0.1:8000/sales-comparison?start_date_1=2024-09-5&end_date_1=2024-09-16&start_date_2=2024-09-13&end_date_2=2024-09-14








