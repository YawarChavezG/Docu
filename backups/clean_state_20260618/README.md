# Clean State Backup — 2026-06-18

> Snapshot físico de la BD en estado "limpio" (audit_log truncado).
> Para volver a este estado tras hacer pruebas destructivas.

## Contenido

| Archivo | Tamaño | Función |
|---|---|---|
| `clean_state.dump` | 134 KB | Backup físico `pg_dump -Fc` (formato custom comprimido) |
| `verify_clean_state.sql` | 1.5 KB | Crea función PL/pgSQL `verify_clean_state()` que cuenta filas por tabla |
| `tests_ensuciar.sql` | 0.6 KB | Script de SUCIADO (de prueba) para validar el restore end-to-end |

## Estado capturado (snapshot limpio)

```
archivos_adjuntos       | 0
areas                   | 50
audit_log               | 0   ← truncado
configuracion_global    | 7
documento_flujo         | 10
documentos              | 10
email_templates         | 11
estados                 | 12
feriados                | 20
firmas_digitales        | 0
gerencias               | 10
log_sincronizacion_ad   | 0
matriz_enrutamiento_eto | 10
tipos_documento         | 13
usuarios                | 763
```

## Cómo restaurar (volver al estado limpio)

```powershell
# Desde la raíz del repo (C:\Users\ychavez\PROYECTOS-DOCKER\SGD-DES)
scripts\restore_clean_state.bat
```

El script:
1. Lee credenciales del `.env` (POSTGRES_USER, POSTGRES_PASSWORD, etc.)
2. Detiene `sgd-backend`, `sgd-celery-worker`, `sgd-celery-beat` (libera conexiones a la BD)
3. `docker cp` del dump al container `sgd-postgres`
4. `pg_restore --clean --if-exists --single-transaction` (drop + recreate)
5. Levanta de nuevo backend y celery
6. Imprime verificación final con `verify_clean_state()`

**Tiempo total**: ~30 segundos.

## Cómo verificar manualmente (sin restaurar)

```bash
docker exec sgd-postgres psql -U sgd -d sgd -c "SELECT * FROM verify_clean_state();"
```

## Flujo recomendado de uso

1. **Inicio del día** (BD en estado limpio): corre `verify_clean_state()` → confirma que `audit_log=0` y los conteos coinciden.
2. **Haces pruebas** (CRUDs, inserts, deletes, etc.).
3. **Al terminar el día / antes de commit**: corre `scripts\restore_clean_state.bat` → vuelve al estado limpio.
4. **Opcional**: corre `verify_clean_state()` para confirmar.

## Flujo de validación ejecutado (2026-06-18)

1. Truncamos `audit_log` → 0.
2. `pg_dump -Fc` → 134 KB.
3. Cargamos función `verify_clean_state()`.
4. Ensuciamos la BD con `tests_ensuciar.sql`:
   - UPDATE gerencia id=1: nombre "CONTAMINADA"
   - INSERT 2 audit_log de prueba
5. `verify_clean_state()` → audit_log=2, gerencia=10 (correcto, sucio).
6. Ejecutamos `restore_clean_state.bat`.
7. `verify_clean_state()` → audit_log=0, gerencia=10, gerencia id=1 nombre "CALIDAD" (correcto, limpio).
8. **VALIDADO** ✅

## Próximas sesiones

- Si en futuras sesiones la BD se desvía del snapshot, regenerar el backup:
  1. `TRUNCATE audit_log` (o lo que se decida)
  2. `pg_dump -Fc ... > backups/clean_state_YYYYMMDD/clean_state.dump`
  3. Actualizar este README con la nueva fecha.
- ADR-065 documenta la decisión de usar `pg_dump -Fc` + `pg_restore --clean` como mecanismo de restore.
