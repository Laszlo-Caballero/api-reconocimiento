-- Habilitar extensión vector si no existe (ya debería estar en initial.sql)
CREATE EXTENSION IF NOT EXISTS vector;

-- Tabla de Usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    usuarioId SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'USER' NOT NULL
);

-- Tabla de Historial de Búsquedas
CREATE TABLE IF NOT EXISTS historial_busquedas (
    id SERIAL PRIMARY KEY,
    usuarioId INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    time VARCHAR(100) NOT NULL,
    description TEXT,
    tags jsonb,
    image VARCHAR(255),
    category VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuarioId) REFERENCES usuarios(usuarioId) ON DELETE CASCADE
);

-- Tabla de Tokens de Notificación FCM
CREATE TABLE IF NOT EXISTS fcm_tokens (
    id SERIAL PRIMARY KEY,
    usuarioId INTEGER NOT NULL,
    token TEXT UNIQUE NOT NULL,
    platform VARCHAR(50) NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuarioId) REFERENCES usuarios(usuarioId) ON DELETE CASCADE
);
