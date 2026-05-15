# ACID Explanation for MoneyPal

MoneyPal demonstrates DBMS transaction management through a digital wallet application. The critical operation is money movement, especially user-to-user transfer, where the sender balance, receiver balance, and transaction record must stay synchronized.

## Atomicity

MoneyPal wraps each money operation inside a database transaction:

```python
conn.start_transaction(isolation_level="READ COMMITTED")
# perform wallet update and transaction insert
conn.commit()
```

If an error occurs, MoneyPal executes:

```python
conn.rollback()
```

This means a transfer cannot debit the sender without crediting the receiver, and a transaction log cannot be written without the matching wallet updates.

## Consistency

The schema enforces valid data:

- `users.username` is unique.
- `wallet.wallet_id` is a foreign key to `users.user_id`.
- `transactions.sender_id` and `transactions.receiver_id` reference valid users.
- `wallet.bal >= 0` prevents negative balances.
- `transactions.amount > 0` prevents zero or negative transactions.
- `ON DELETE CASCADE` removes wallets when users are deleted.

Application logic also checks for sufficient balance before withdrawals and transfers.

## Isolation

Concurrent requests can cause incorrect balances if two transfers read the same old balance. MoneyPal prevents this using row-level locks:

```sql
SELECT bal FROM wallet WHERE wallet_id = %s FOR UPDATE;
```

For user-to-user transfers, both wallet rows are locked in sorted order to reduce deadlock risk.

## Durability

MoneyPal uses MySQL InnoDB tables. InnoDB supports durable committed transactions. After `commit()`, the database stores the result permanently unless another valid transaction changes it later.

## Where ACID Is Implemented

- `deposit()` route in `app.py`
- `withdraw()` route in `app.py`
- `transfer()` route in `app.py`
- `register()` route in `app.py`
- `delete_account()` route in `app.py`
- `sql/schema.sql` table definitions and trigger
