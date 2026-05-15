# MoneyPal: A Digital Wallet Application

## Project Overview

MoneyPal is a DBMS project developed using Python, Flask, and MySQL. It demonstrates how a digital wallet system can store users, wallets, and transactions in a relational database while preserving data integrity.

This application is a portfolio/academic project and is not a real financial wallet.

## Technology Stack

- Frontend: HTML, CSS, JavaScript
- Backend: Python Flask
- Database: MySQL
- Database Engine: InnoDB
- Security: Werkzeug password hashing and parameterized SQL queries

## Database Architecture

The database contains three main tables.

### users

Stores user account data:

- `user_id`: Primary key
- `first_name`
- `last_name`
- `username`: Unique login name
- `password_hash`: Hashed password
- `created_at`

### wallet

Stores wallet balance for each user:

- `wallet_id`: Primary key and foreign key to `users.user_id`
- `bal`: Current wallet balance
- `last_transaction_type`
- `last_receiver_id`
- `updated_at`

A trigger automatically creates a wallet record when a new user registers.

### transactions

Stores the transaction ledger:

- `transaction_id`: Primary key
- `sender_id`
- `receiver_id`
- `amount`
- `transaction_type`
- `status`
- `note`
- `created_at`

## CRUD Operations

MoneyPal uses parameterized SQL queries for all database interactions.

- Create: Register users, create wallet through trigger, insert transactions
- Read: Login validation, dashboard balance, transaction history
- Update: Deposit, withdraw, transfer wallet balance updates
- Delete: Account deletion with wallet cascade

## Transaction Workflow

### Deposit

1. Lock current user's wallet row.
2. Increase wallet balance.
3. Insert deposit transaction record.
4. Commit all changes together.

### Withdraw

1. Lock current user's wallet row.
2. Verify sufficient balance.
3. Decrease wallet balance.
4. Insert withdrawal transaction record.
5. Commit all changes together.

### User-to-User Transfer

1. Find receiver by username.
2. Lock sender and receiver wallet rows.
3. Check sender balance.
4. Debit sender.
5. Credit receiver.
6. Insert one transaction ledger record.
7. Commit all changes together.

## Security and Integrity

- Passwords are not stored in plain text.
- SQL injection is reduced using parameterized SQL queries.
- Foreign keys preserve relational integrity.
- Check constraints prevent invalid amounts and negative balances.
- Explicit commit/rollback prevents partial updates.

## Future Enhancements

- Admin panel
- Email verification
- Pagination and export for transaction history
- REST API endpoints
- Unit tests with a test database
- Two-factor authentication
