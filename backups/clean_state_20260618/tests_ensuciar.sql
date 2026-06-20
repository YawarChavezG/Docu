-- ============================================================
--  tests_ensuciar.sql
--  Modifica/agrega datos de prueba para validar el restore.
--  Este script NO se commitea al backup dump; es solo de test.
-- ============================================================

-- 1) Modificar una gerencia existente (UPDATE, no requiere conocer todas las cols)
UPDATE gerencias
   SET nombre = 'GERENCIA CONTAMINADA POR TEST ' || NOW()::TEXT
 WHERE id = 1
 RETURNING id, sigla, nombre;

-- 2) Modificar asunto de un email template existente
UPDATE email_templates
   SET asunto = 'ASUNTO CONTAMINADO POR TEST ' || NOW()::TEXT
 WHERE id = 1
 RETURNING id, codigo, asunto;

-- 3) Insertar 2 entradas en audit_log (tabla que ya truncamos)
INSERT INTO audit_log (accion, recurso, recurso_id, descripcion, exitoso, detalles, created_at)
VALUES
    ('TEST_RESTORE_INSERT', 'gerencia', 1, 'Prueba de restore: accion A', true,
     '{"motivo": "validacion de pg_restore --clean"}'::jsonb, NOW()),
    ('TEST_RESTORE_UPDATE', 'email_template', 1, 'Prueba de restore: accion B', true,
     '{"motivo": "validacion de pg_restore --clean"}'::jsonb, NOW())
RETURNING id, accion;
