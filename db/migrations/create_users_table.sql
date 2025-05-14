CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    amocrm_id INT,
    mis_id INT,
    phone_number VARCHAR(20),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    third_name VARCHAR(100),
    birth_date DATE,
    consent_notifications BOOLEAN DEFAULT FALSE,
    consent_marketing BOOLEAN DEFAULT FALSE,
    registration_date DATETIME NOT NULL,
    last_activity DATETIME NOT NULL,
    bot_state VARCHAR(50) DEFAULT 'new'
);

-- Создание индексов для оптимизации запросов
CREATE INDEX idx_phone_number ON users(phone_number);
CREATE INDEX idx_amocrm_id ON users(amocrm_id);
CREATE INDEX idx_mis_id ON users(mis_id);
CREATE INDEX idx_telegram_id ON users(telegram_id);
