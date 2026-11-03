"""Revisa la Regla de Dependencias: Dominio y Aplicación NO pueden importar infraestructura.

Uso:  python verificar_arquitectura.py
"""
import ast
import sys
from pathlib import Path

LIBRERIAS_DE_INFRAESTRUCTURA = {"fastapi", "pydantic", "starlette", "uvicorn",
                                "sqlalchemy", "flask", "django"}
REGLAS = {
    # Dominio: no puede depender de nadie más.
    "domain": LIBRERIAS_DE_INFRAESTRUCTURA | {"application", "infrastructure"},
    # Aplicación: puede usar Dominio, pero no Infraestructura ni frameworks.
    "application": LIBRERIAS_DE_INFRAESTRUCTURA | {"infrastructure"},
}


def modulos_importados(ruta: Path):
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            for alias in nodo.names:
                yield alias.name.split(".")[0]
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            yield nodo.module.split(".")[0]


def main() -> int:
    errores = []
    for capa, prohibidos in REGLAS.items():
        for archivo in sorted(Path(capa).rglob("*.py")):
            for modulo in set(modulos_importados(archivo)):
                if modulo in prohibidos:
                    errores.append(f"[X] {archivo} importa '{modulo}' (prohibido en {capa})")
            print(f"[ok] {archivo}")
    if errores:
        print("\n".join(errores))
        return 1
    print("\nArquitectura limpia verificada: Dominio y Aplicación sin dependencias de infraestructura.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
