# Tasks: Mejoras al catálogo y wishlist

Deriva de [plan.md](./plan.md). Orden = dependencia. `[P]` = paralelizable
dentro de su bloque. Conventional Commits, un commit por tarea.

## Fase 1 — Modelo y migración

- [ ] M001 Modelo `Categoria` + enums `Prioridad` y `RangoPrecio`
- [ ] M002 Campos nuevos en `Item` (`cantidad`, `cantidad_recibida`,
      `categoria_id`, `prioridad`, `rango_precio`) con sus CHECK
- [ ] M003 Campos nuevos en `Reserva` (`unidad`, `mensaje`)
- [ ] M004 Migración única: crear tabla, columnas, backfill de cantidad y
      unidad, swap del índice parcial, y downgrade que borra los ENUM
- [ ] M005 Helper `recalcular_estado(item)` en el service/router de items

## Fase 2 — Backend: cantidad y reservas por unidad

Depende de Fase 1.

- [ ] M006 `reservar` con `SELECT ... FOR UPDATE`, asignación de unidad
      libre y `mensaje` opcional
- [ ] M007 `GET /items/{id}/reservas` (sin nombres, con
      `dias_desde_reserva`)
- [ ] M008 `POST /items/{id}/reservas/{id}/recibir` — revela nombre y
      mensaje de esa unidad
- [ ] M009 `POST /items/{id}/reservas/{id}/liberar` — reemplaza a
      `/liberar-reserva`
- [ ] M010 `PATCH /items/{id}/adquirir` recibe las unidades restantes
- [ ] M011 Validación al bajar `cantidad` por debajo de lo comprometido

## Fase 3 — Backend: organización y búsqueda

- [ ] M012 [P] `GET`/`POST /categorias`
- [ ] M013 [P] `cantidad`, `categoria_id`, `prioridad`, `rango_precio` en
      crear/editar item
- [ ] M014 `GET /items/buscar?q=` insensible a acentos, con caja
- [ ] M015 `GET /w/{token}` con disponibles, categoría, prioridad, precio
      y orden por prioridad

## Fase 4 — Tests backend

- [ ] M016 Tests de cantidad: reserva parcial, item visible hasta
      completarse, capacidad respetada
- [ ] M017 Tests de concurrencia sobre la última unidad
- [ ] M018 [P] Tests de recibir/liberar por unidad y revelación
      individual (las otras reservas siguen ocultas)
- [ ] M019 [P] Tests de categorías, prioridad y rango de precio
- [ ] M020 [P] Tests del buscador (parcial, sin acentos, con caja)
- [ ] M021 Revisar y adaptar los tests de la v1 afectados por el cambio
      de semántica de `/adquirir`

## Fase 5 — Frontend admin

- [ ] M022 Tipos y stores actualizados (items, categorías)
- [ ] M023 Formulario con cantidad, categoría, prioridad y rango
- [ ] M024 Tarjeta con contador `recibidas/cantidad` y badges nuevos
- [ ] M025 Panel de reservas por item: antigüedad, recibir y liberar
- [ ] M026 Buscador con la caja en el resultado

## Fase 6 — Frontend público

- [ ] M027 Agrupación por categoría con urgentes primero
- [ ] M028 Badges de prioridad y precio, contador "quedan N de M"
- [ ] M029 Campo de mensaje opcional en el modal de reserva

## Fase 7 — PWA y cierre

- [ ] M030 [P] `@vite-pwa/nuxt` con ícono y nombre de la app
- [ ] M031 [P] Tests frontend de los stores nuevos
- [ ] M032 Verificación en navegador de los flujos nuevos
- [ ] M033 README y specs actualizados
