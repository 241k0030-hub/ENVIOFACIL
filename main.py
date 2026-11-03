"""Raíz de composición: aquí se crean las capas y se pasan las dependencias a mano.

Ejecutar:  uvicorn main:app --host 127.0.0.1 --port 8080
Docs interactivas: http://127.0.0.1:8080/docs
"""
from datetime import datetime, timezone
from uuid import UUID

from application.actualizar_estado_envio import ActualizarEstadoEnvio
from domain.envio import Envio, EstadoOrden
from infrastructure.api.envio_controller import crear_app
from infrastructure.persistence.in_memory_envio_repository import InMemoryEnvioRepository

# Envíos de ejemplo con IDs fijos para poder probar fácil en Postman.
DATOS_DE_PRUEBA = [
    ("11111111-1111-4111-8111-111111111111", EstadoOrden.EN_ALMACEN),
    ("22222222-2222-4222-8222-222222222222", EstadoOrden.RECIBIDO),
    ("33333333-3333-4333-8333-333333333333", EstadoOrden.EN_TRANSITO),
    ("44444444-4444-4444-8444-444444444444", EstadoOrden.ENTREGADO),
    ("55555555-5555-4555-8555-555555555555", EstadoOrden.CANCELADA),
]


def construir_app():
    repositorio = InMemoryEnvioRepository()
    for id_texto, estado in DATOS_DE_PRUEBA:
        repositorio.guardar(
            Envio(
                id_envio=UUID(id_texto),
                estado_orden=estado,
                fecha_actualizacion=datetime.now(timezone.utc),
                id_operador="OP-0001",
                motivo_cancelacion="Seed" if estado is EstadoOrden.CANCELADA else None,
            )
        )
    caso_de_uso = ActualizarEstadoEnvio(repositorio)   # Aplicación recibe el puerto
    return crear_app(caso_de_uso)                       # Infraestructura recibe el caso de uso


app = construir_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8080)
