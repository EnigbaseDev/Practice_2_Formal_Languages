#!/usr/bin/env python3
"""
Módulo de ejecución rápida para Visual Studio Code (▶ Run).
Alimenta 'input.txt', imprime la tabla en terminal y genera 'output.html'.
"""

from pathlib import Path
import sys
import conversor_afn_afd as motor


def principal():
    base_dir = Path(__file__).parent
    
    # Determinar ruta del archivo de entrada
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        archivo_in = Path(sys.argv[1])
    else:
        archivo_in = base_dir / "input.txt"

    archivo_out = base_dir / "output.html"
    if len(sys.argv) > 2 and not sys.argv[2].startswith("-"):
        archivo_out = Path(sys.argv[2])

    if not archivo_in.exists():
        print(f"Error: No se encontró el archivo '{archivo_in.name}'.", file=sys.stderr)
        sys.exit(1)

    texto_contenido = archivo_in.read_text(encoding="utf-8")
    afns = motor.LectorAutomata.procesar_texto(texto_contenido)
    afds = []
    for afn in afns:
        afd = afn.compilar_a_afd()
        afds.append(afd)
        print("\n".join(afd.generar_lineas_consola()))

    archivo_out.write_text(motor.generar_reporte_completo(afds), encoding="utf-8")
    print(f"\n[Reporte visual SVG generado exitosamente en: {archivo_out.name}]")


if __name__ == "__main__":
    principal()
