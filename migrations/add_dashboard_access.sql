-- Agregar columna has_dashboard_access a la tabla de usuarios
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS has_dashboard_access BOOLEAN DEFAULT FALSE NOT NULL;

-- Asignar acceso al dashboard a los usuarios administradores existentes
UPDATE usuarios SET has_dashboard_access = TRUE WHERE role = 'ADMIN';
