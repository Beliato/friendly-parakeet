# Tasks: Página pública de celebración

Deriva de [plan.md](./plan.md). Conventional Commits, un commit por tarea.

## Fase 1 — Backend

- [ ] P001 `RegaloPublicoOut` y `recibidos` en `GET /w/{share_token}`
      (solo `origen = REGALO` con persona, foto de Julia o de referencia,
      más recientes primero)
- [ ] P002 Tests: el muro lista los recibidos, excluye compras propias, y
      una reserva pendiente no aparece ni filtra el nombre

## Fase 2 — Identidad visual

- [ ] P003 Paleta nueva en `tailwind.config.ts` (escalas `pink` y
      `neutral` del plan)
- [ ] P004 Fondos de `bg-pink-*` a `bg-neutral-*` en layout y páginas
- [ ] P005 [P] Fuente serif para los títulos de la página pública

## Fase 3 — La página

- [ ] P006 Hero con nombre, frase e ilustración (degrada al ícono si el
      archivo no está)
- [ ] P007 Muro de regalos recibidos
- [ ] P008 Wishlist con el estilo nuevo, sin RSVP

## Fase 4 — Cierre

- [ ] P009 Verificación en navegador: login, catálogo, regalos, ajustes y
      pública, en claro y oscuro
- [ ] P010 [P] Tests frontend afectados por el cambio
- [ ] P011 README y specs actualizados
