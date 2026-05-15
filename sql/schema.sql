-- MoneyPal ACID-safe schema
-- Run this file in MySQL Workbench or mysql CLI before starting the app.

CREATE DATABASE IF NOT EXISTS moneypal
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
USE moneypal;

-- InnoDB is used because it supports ACID transactions, row-level locking,
-- foreign keys, rollback, and crash-safe commit behavior.
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS wallet;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(60) NOT NULL,
    last_name VARCHAR(60) NOT NULL,
    username VARCHAR(60) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE wallet (
    wallet_id INT PRIMARY KEY,
    bal DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    last_transaction_type ENUM('REGISTER','DEPOSIT','WITHDRAW','TRANSFER_SENT','TRANSFER_RECEIVED') DEFAULT 'REGISTER',
    last_receiver_id INT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_wallet_user FOREIGN KEY (wallet_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE,
    CONSTRAINT chk_wallet_balance_nonnegative CHECK (bal >= 0)
) ENGINE=InnoDB;

CREATE TABLE transactions (
    transaction_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    sender_id INT NULL,
    receiver_id INT NULL,
    amount DECIMAL(12,2) NOT NULL,
    transaction_type ENUM('DEPOSIT','WITHDRAW','USER_TO_USER') NOT NULL,
    status ENUM('SUCCESS','FAILED') NOT NULL DEFAULT 'SUCCESS',
    note VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_tx_sender FOREIGN KEY (sender_id)
        REFERENCES users(user_id)
        ON DELETE SET NULL,
    CONSTRAINT fk_tx_receiver FOREIGN KEY (receiver_id)
        REFERENCES users(user_id)
        ON DELETE SET NULL,
    CONSTRAINT chk_tx_amount_positive CHECK (amount > 0)
) ENGINE=InnoDB;

DELIMITER $$
CREATE TRIGGER userwallettrigger
AFTER INSERT ON users
FOR EACH ROW
BEGIN
    INSERT INTO wallet(wallet_id, bal, last_transaction_type)
    VALUES (NEW.user_id, 0.00, 'REGISTER');
END$$
DELIMITER ;

CREATE INDEX idx_transactions_sender ON transactions(sender_id, created_at);
CREATE INDEX idx_transactions_receiver ON transactions(receiver_id, created_at);
CREATE INDEX idx_users_username ON users(username);


