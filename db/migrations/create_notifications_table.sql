CREATE TABLE notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    telegram_id BIGINT NOT NULL,
    appointment_id INT NOT NULL,
    message_id BIGINT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    sent_at DATETIME NOT NULL,
    responded_at DATETIME NULL,
    cancel_reason VARCHAR(255) NULL,
    
    -- Создание внешнего ключа для связи с таблицей users
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Создание индексов для оптимизации запросов
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_telegram_id ON notifications(telegram_id);
CREATE INDEX idx_notifications_appointment_id ON notifications(appointment_id);
CREATE INDEX idx_notifications_status ON notifications(status);
