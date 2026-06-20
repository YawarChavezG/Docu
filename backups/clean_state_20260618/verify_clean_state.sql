-- ============================================================
--  verify_clean_state.sql
--  Funcion PL/pgSQL que retorna los conteos de las tablas
--  mutables del sistema. Util para:
--   (a) Documentar el estado "limpio" (post-restore).
--   (b) Comparar contra el estado "sucio" (post-pruebas).
--  Uso:
--    SELECT * FROM verify_clean_state();
-- ============================================================

CREATE OR REPLACE FUNCTION verify_clean_state()
RETURNS TABLE(tabla TEXT, filas BIGINT)
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
    RETURN QUERY
    SELECT 'audit_log'::TEXT,                 COUNT(*)::BIGINT FROM audit_log
    UNION ALL SELECT 'firmas_digitales',      COUNT(*)::BIGINT FROM firmas_digitales
    UNION ALL SELECT 'log_sincronizacion_ad',  COUNT(*)::BIGINT FROM log_sincronizacion_ad
    UNION ALL SELECT 'documentos',             COUNT(*)::BIGINT FROM documentos
    UNION ALL SELECT 'documento_flujo',        COUNT(*)::BIGINT FROM documento_flujo
    UNION ALL SELECT 'archivos_adjuntos',      COUNT(*)::BIGINT FROM archivos_adjuntos
    UNION ALL SELECT 'usuarios',               COUNT(*)::BIGINT FROM usuarios
    UNION ALL SELECT 'gerencias',              COUNT(*)::BIGINT FROM gerencias
    UNION ALL SELECT 'areas',                  COUNT(*)::BIGINT FROM areas
    UNION ALL SELECT 'email_templates',        COUNT(*)::BIGINT FROM email_templates
    UNION ALL SELECT 'matriz_enrutamiento_eto',COUNT(*)::BIGINT FROM matriz_enrutamiento_eto
    UNION ALL SELECT 'tipos_documento',        COUNT(*)::BIGINT FROM tipos_documento
    UNION ALL SELECT 'estados',                COUNT(*)::BIGINT FROM estados
    UNION ALL SELECT 'configuracion_global',   COUNT(*)::BIGINT FROM configuracion_global
    UNION ALL SELECT 'feriados',               COUNT(*)::BIGINT FROM feriados
    ORDER BY 1;
END;
$$;

COMMENT ON FUNCTION verify_clean_state() IS
'Retorna conteo de filas por tabla. Util para verificar el estado de la BD despues de un restore o despues de pruebas. Esperado post-restore (snapshot 2026-06-18): audit_log=0, documentos=10, documento_flujo=10, archivos_adjuntos=0, firmas_digitales=0, log_sincronizacion_ad=0, gerencias=10, areas=50, usuarios=763, email_templates=11, matriz_enrutamiento_eto=10, tipos_documento=13, estados=12, configuracion_global=7, feriados=20.';
