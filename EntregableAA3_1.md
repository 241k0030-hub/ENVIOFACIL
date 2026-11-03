# EntregableAA3_1 — Construcción del software (Arquitectura Limpia)

**Proyecto:** EnvíoFácil — Módulo de Almacén
**Asignatura:** Fundamentos de Ingeniería de Software · **Profesora:** MTI. Paloma Góngora Sabido
**Grupo:** [CONFIRMAR: ISC-5A o ISC-4A]
**Equipo:** Valentina Román Can · Andrés Román Can · Bryant Adrián Cahum Fernández · Jhemner Rafael Ferral Moreno · Santiago Cruz May Acosta
**Stack:** Python 3.10+ con FastAPI (sin contenedores de inyección de dependencias)
**Historia de Usuario implementada:** HU1 — Cancelación de envíos en almacén

---

## 1. Cómo ejecutar el proyecto

```bash
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8080
```

- Servidor: <http://127.0.0.1:8080>
- Documentación interactiva: <http://127.0.0.1:8080/docs>
- Pruebas automáticas: `python -m pytest`
- Verificación de arquitectura: `python verificar_arquitectura.py`

> No hay base de datos: los envíos viven en memoria y se reinician cada vez que se reinicia el servidor.

## 2. Estructura en 3 capas

```
enviofacil/
├── domain/                         # DOMINIO: reglas de negocio (Python puro)
│   └── envio.py                    #   Entidad Envio, estados, transiciones, errores
├── application/                    # APLICACIÓN: casos de uso + puertos
│   ├── ports.py                    #   Interfaz EnvioRepository (puerto)
│   ├── actualizar_estado_envio.py  #   Caso de uso
│   └── errors.py                   #   EnvioNoEncontrado
├── infrastructure/                 # INFRAESTRUCTURA: detalles técnicos
│   ├── api/envio_controller.py     #   Controlador HTTP (FastAPI) = ruta del contrato
│   └── persistence/in_memory_envio_repository.py   # Adaptador en memoria
├── main.py                         # Ensambla las capas a mano (constructor)
├── contrato-enviofacil.yaml        # Contrato OpenAPI (AA2.3 + 404)
├── verificar_arquitectura.py       # Comprueba la regla de dependencias
└── tests/test_endpoint.py          # 10 pruebas del endpoint
```

**Regla de dependencias (las flechas apuntan hacia adentro):**
`infrastructure → application → domain`. El dominio no conoce a nadie.

## 3. Trazabilidad: artefactos de las Unidades 1 y 2 → código

| Artefacto | Qué dice | Dónde está en el código |
|---|---|---|
| Gherkin HU1, Escenario 1 | Cancelar en almacén → estado "Cancelado" | `Envio.cambiar_estado` + prueba `test_200_cancelacion_exitosa_en_almacen` |
| Gherkin HU1, Escenario 2 | En ruta no se puede cancelar: "No se puede cancelar, paquete en tránsito" | `Envio._mensaje_de_rechazo` → HTTP 409 |
| Gherkin HU1, Escenario 3 | No se puede cancelar dos veces | Estados finales sin transiciones → HTTP 409 |
| Gherkin HU2, Escenario 2 | Cancelar exige motivo | `DatosInvalidos` → HTTP 400 |
| Máquina de estados (AA2.1) | Estados y transiciones válidas | `_TRANSICIONES_PERMITIDAS` en `domain/envio.py` |
| Contrato OpenAPI (AA2.3) | `PATCH /api/v1/envios/{id}/estado` | `infrastructure/api/envio_controller.py` |
| Borrado lógico (AA2.1) | Nunca se elimina, solo cambia de estado | El repositorio no tiene método `eliminar` |

### Decisiones tomadas cuando los documentos diferían

Se dio preferencia al documento más reciente (AA2.3, contrato OpenAPI):

| Tema | AA2.1 (anterior) | Usado en el código (AA2.3) |
|---|---|---|
| ID del envío | `EF-#####` | UUID (`idEnvio`) |
| Estados | REGISTRADO, EN_RUTA_DE_ENTREGA, RETORNO_A_ALMACEN, CANCELADO… | RECIBIDO, EN_ALMACEN, EN_TRANSITO, ENTREGADO, CANCELADA, ANULADA |
| Operador | `usuario_id` | `idOperador` |

**Cambios acordados al contrato:** se agregó la respuesta **404** (envío inexistente), porque el contrato original no definía qué responder en ese caso.

### Transiciones permitidas

| Estado actual | Puede pasar a |
|---|---|
| RECIBIDO | EN_ALMACEN, CANCELADA, ANULADA |
| EN_ALMACEN | EN_TRANSITO, CANCELADA, ANULADA |
| EN_TRANSITO | ENTREGADO |
| ENTREGADO, CANCELADA, ANULADA | *(estados finales)* |

`ANULADA` se trata igual que `CANCELADA` (exige motivo y es estado final).

## 4. Validación de la IA (Regla de Inversión de Dependencias)

Se revisó que ninguna librería de infraestructura se haya colado en Dominio o Aplicación.

| Revisión | Resultado |
|---|---|
| `domain/` importa FastAPI, Pydantic, BD u otras capas | No |
| `application/` importa FastAPI, Pydantic, BD o `infrastructure` | No |
| Persistencia accedida solo mediante el puerto `EnvioRepository` | Sí |
| Dependencias pasadas por constructor, sin contenedor de DI | Sí (`main.py`) |

Evidencia automática (`python verificar_arquitectura.py`):

```
[ok] domain/envio.py
[ok] application/actualizar_estado_envio.py
[ok] application/errors.py
[ok] application/ports.py
Arquitectura limpia verificada: Dominio y Aplicación sin dependencias de infraestructura.
```

También se comprobó que el verificador **sí detecta** la violación: al agregar `import fastapi` en `domain/envio.py` reportó `[X] domain/envio.py importa 'fastapi' (prohibido en domain)`.

**Correcciones manuales realizadas por el equipo:** [COMPLETAR: describir qué revisaron o corrigieron a mano; si no hubo cambios, indicarlo]

Detalle de diseño: FastAPI responde 422 por defecto en errores de validación; el contrato exige 400, por eso el controlador (capa de Infraestructura) convierte esos errores a 400 con el formato `ErrorResponse`.

## 5. Peticiones para Postman / Thunder Client

Base: `http://127.0.0.1:8080/api/v1/envios/{id}/estado` · Método: **PATCH** · Header: `Content-Type: application/json`

IDs de prueba cargados al iniciar el servidor:

| ID | Estado inicial |
|---|---|
| `11111111-1111-4111-8111-111111111111` | EN_ALMACEN |
| `22222222-2222-4222-8222-222222222222` | RECIBIDO |
| `33333333-3333-4333-8333-333333333333` | EN_TRANSITO |
| `44444444-4444-4444-8444-444444444444` | ENTREGADO |
| `55555555-5555-4555-8555-555555555555` | CANCELADA |

| # | Caso | ID | Body | Esperado |
|---|---|---|---|---|
| 1 | 400 sin motivo | `1111…` | `{"estadoOrden":"CANCELADA","idOperador":"OP-9876"}` | **400** |
| 2 | 400 id inválido | `abc` | cualquier body válido | **400** |
| 3 | 200 cancelar (flujo feliz HU1) | `1111…` | `{"estadoOrden":"CANCELADA","idOperador":"OP-9876","motivoCancelacion":"Cliente solicitó la cancelación previa al envío."}` | **200** |
| 4 | 200 avanzar estado | `2222…` | `{"estadoOrden":"EN_ALMACEN","idOperador":"OP-9876"}` | **200** |
| 5 | 409 cancelar en tránsito (HU1 esc. 2) | `3333…` | body del caso 3 | **409** |
| 6 | 409 modificar entregado | `4444…` | body del caso 3 | **409** |
| 7 | 409 cancelar dos veces (HU1 esc. 3) | `1111…` (después del caso 3) | body del caso 3 | **409** |
| 8 | 404 no existe | `99999999-9999-4999-8999-999999999999` | body del caso 3 | **404** |

> Orden recomendado: 1 → 2 → 3 → 7 (el caso 7 solo da 409 después de haber ejecutado el 3). Para repetir las pruebas, reinicia el servidor.

Respuesta real del caso 3 (200):

```json
{
  "idEnvio": "11111111-1111-4111-8111-111111111111",
  "estadoOrden": "CANCELADA",
  "fechaActualizacion": "2026-11-02T04:36:28.000010Z",
  "idOperador": "OP-9876",
  "motivoCancelacion": "Cliente solicitó la cancelación previa al envío."
}
```

## 6. Repositorio

Enlace: [COMPLETAR: URL del repositorio en GitHub]
