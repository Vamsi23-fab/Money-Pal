# MoneyPal: ACID-Safe Digital Wallet Application

MoneyPal is a Flask + MySQL DBMS project that demonstrates a digital wallet with user registration, login, deposits, withdrawals, user-to-user transfers, and transaction history.


## Main Features

- User registration and secure password hashing
- Login/logout using Flask sessions
- Wallet table created automatically for each new user through a MySQL trigger
- Deposit, withdraw, and transfer pages
- Full transaction history
- Parameterized SQL queries for all database access
- ACID-preserving transaction logic with commit/rollback
- MySQL InnoDB schema with primary keys, foreign keys, checks, and indexes

## How MoneyPal Preserves ACID Properties

### Atomicity
Deposit, withdrawal, transfer, registration, and account deletion are executed inside explicit database transactions. If any query fails, the code calls `rollback()`, so partial wallet updates do not remain.

### Consistency
The database uses primary keys, unique usernames, foreign keys, positive amount checks, and non-negative wallet balance checks. The application also validates amounts before database writes.

### Isolation
Money operations lock wallet rows using `SELECT ... FOR UPDATE`, preventing concurrent requests from reading/updating the same wallet balance incorrectly.

### Durability
The schema uses MySQL InnoDB. After `commit()`, completed transactions are written durably by the database engine.

## Folder Structure

```text
MoneyPal_ACID/
├── app.py
├── requirements.txt
├── .env.example
├── README.md
├── sql/
│   └── schema.sql
├── docs/
│   ├── RUN_GUIDE.md
│   ├── ACID_EXPLANATION.md
│   └── PROJECT_REPORT.md
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── transactions.html
│   └── partials_transaction_table.html
└── static/
    ├── css/style.css
    └── js/app.js
```
