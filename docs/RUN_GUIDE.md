# Step-by-Step Guide to Run MoneyPal

## 1. Install prerequisites

Install these first:

- Python 3.10 or newer
- MySQL Server 8.0 or newer
- MySQL Workbench or MySQL CLI
- Git, optional but useful

## 2. Open the project folder

Unzip the package and open a terminal inside the extracted folder:

```bash
cd MoneyPal_ACID
```

## 3. Create a virtual environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### macOS/Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

## 4. Install Python dependencies

```bash
pip install -r requirements.txt
```

## 5. Create the MySQL database

Open MySQL Workbench and run:

```sql
SOURCE /full/path/to/MoneyPal_ACID/sql/schema.sql;
```

Or use MySQL CLI:

```bash
mysql -u root -p < sql/schema.sql
```

This creates the `moneypal` database with `users`, `wallet`, and `transactions` tables.

## 6. Configure database credentials

Copy the example environment file:

### Windows

```bash
copy .env.example .env
```

### macOS/Linux

```bash
cp .env.example .env
```

Edit `.env` and set your MySQL credentials:

```env
FLASK_SECRET_KEY=change-this-secret-key
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=moneypal
```

## 7. Run the Flask app

```bash
python app.py
```

Then open this in your browser:

```text
http://127.0.0.1:5000
```

## 8. Test the application

1. Register two users, for example `asha` and `ravi`.
2. Login as `asha`.
3. Deposit money into Asha's wallet.
4. Transfer some money from `asha` to `ravi`.
5. Logout and login as `ravi` to verify the received balance.
6. Open the transaction history page to view all recorded transactions.

## 9. Common errors and fixes

### Access denied for user
Your `.env` MySQL username or password is incorrect.

### Unknown database `moneypal`
The schema was not imported. Run `sql/schema.sql` again.

### Module not found
Activate your virtual environment and run `pip install -r requirements.txt`.

### Port 5000 already in use
Run with another port:

```bash
flask --app app run --port 5001
```
