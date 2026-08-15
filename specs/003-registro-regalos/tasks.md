# Tasks: Registro de regalos

Deriva de [plan.md](./plan.md). Orden = dependencia. `[P]` = paralelizable
dentro de su bloque. Conventional Commits, un commit por tarea.

## Fase 1 — Modelo y migración

- [ ] R001 Modelos `Regalo` y `FotoRegalo` + enum `Etapa`
- [ ] R002 Campo `items.etapa`
- [ ] R003 Migración: tablas nuevas, backfill de `gifter_name` y de las
      reservas reveladas, drop de `gifter_name`, downgrade que
      reconstruye y borra los ENUM
- [ ] R004 `cantidad_recibida` derivado de los regalos en
      `services/items.py`

## Fase 2 — Backend: registro

- [ ] R005 `POST /regalos` con alta de objeto al vuelo
- [ ] R006 `GET /regalos` con filtros
- [ ] R007 [P] `GET /regalos/personas` (autocompletado)
- [ ] R008 [P] `GET /regalos/por-persona` (agrupado, con pendientes de
      agradecer)
- [ ] R009 `PATCH /regalos/{id}` — incluye marcar agradecido
- [ ] R010 `DELETE /regalos/{id}` con recálculo del objeto
- [ ] R011 `recibir` de una reserva crea el regalo con nombre y mensaje
- [ ] R012 `/adquirir` crea el regalo en vez de tocar `gifter_name`

## Fase 3 — Backend: fotos y etapas

- [ ] R013 Fotos de regalo en R2 (presign, confirmar, borrar) reusando
      `storage_r2` con prefijo `regalos/`
- [ ] R014 [P] `etapa` en crear/editar item y en las salidas
- [ ] R015 Búsqueda devuelve caja, etapa y quiénes regalaron

## Fase 4 — Tests backend

- [ ] R016 Tests de registro: objeto existente, alta al vuelo, varias
      unidades, compra propia
- [ ] R017 [P] Tests de agrupación por persona y agradecimientos
- [ ] R018 [P] Tests de que recibir una reserva crea el regalo y respeta
      la sorpresa hasta ese momento
- [ ] R019 [P] Tests de fotos de regalo (R2 mockeado)
- [ ] R020 Tests de `cantidad_recibida` derivado (alta y baja de regalos)
- [ ] R021 Adaptar los tests afectados por la baja de `gifter_name`

## Fase 5 — Frontend

- [ ] R022 Tipos y store de regalos
- [ ] R023 Modal "Registrar regalo" con autocompletado de persona y alta
      de objeto al vuelo
- [ ] R024 Sección "Regalos": lista con filtros
- [ ] R025 Vista agrupada por persona con marcar agradecido
- [ ] R026 Fotos de Julia por regalo (subida y descarga)
- [ ] R027 Filtro por etapa en el catálogo
- [ ] R028 Búsqueda con caja, etapa y personas

## Fase 6 — Cierre

- [ ] R029 [P] Tests frontend del store de regalos
- [ ] R030 [P] Verificación en navegador de los flujos nuevos
- [ ] R031 README y specs actualizados
