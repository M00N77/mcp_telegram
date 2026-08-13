-- Сообщения. Составной ключ: message_id уникален только ВНУТРИ чата.
CREATE TABLE IF NOT EXISTS messages (
    chat_id      INTEGER NOT NULL,
    message_id   INTEGER NOT NULL,
    sender_id    INTEGER,
    sender_name  TEXT,
    time         INTEGER NOT NULL,      -- Unix timestamp (message.date)
    message_text TEXT,
    PRIMARY KEY (chat_id, message_id)
);

-- Индекс для мгновенной выборки последних сообщений.
CREATE INDEX IF NOT EXISTS idx_chat_time ON messages (chat_id, time DESC, message_id DESC);

-- Справочник чатов.
CREATE TABLE IF NOT EXISTS chats (
    chat_id   INTEGER PRIMARY KEY,
    chat_name TEXT
);

-- Состояние сервера (offset и пр.).
CREATE TABLE IF NOT EXISTS state (
    key   TEXT PRIMARY KEY,
    value INTEGER
);
