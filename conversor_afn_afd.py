#!/usr/bin/env python3
"""
Motor de Conversión de Autómatas: AFN a AFD
===========================================
Asignación 2 — SI2002 Lenguajes Formales
Universidad EAFIT

Implementación orientada a objetos de la Construcción de Subconjuntos
(Dexter Kozen, Automata and Computability, 1997, Lecture 6).

"""

from collections import deque
from dataclasses import dataclass
import html
import json
import math
from pathlib import Path
import re
import sys
from typing import Dict, FrozenSet, List, Set, Tuple



# 1. Modelo de dominio & Estructura de datos

@dataclass(frozen=True)
class EstadoSubconjunto:
    """Encapsula un subconjunto de estados del AFN que conforma un macro-estado del AFD."""
    elementos: FrozenSet[int]

    @property
    def es_vacio(self) -> bool:
        return len(self.elementos) == 0

    def formato_consola(self) -> str:
        """Representación requerida para la salida estándar: '{1 2 4 5}' o '0'."""
        if self.es_vacio:
            return "0"
        return "{" + " ".join(str(n) for n in sorted(self.elementos)) + "}"

    def formato_simbolico(self) -> str:
        """Representación visual matemática ('∅' para el conjunto vacío)."""
        if self.es_vacio:
            return "∅"
        return "{" + " ".join(str(n) for n in sorted(self.elementos)) + "}"

    def __repr__(self) -> str:
        return self.formato_consola()


class AutomataNoDeterminista:
    """Entidad que modela la 5-tupla N = (Q, Sigma, Delta, S, F)."""

    def __init__(self,
                 cardinalidad_q: int,
                 estados_iniciales: Set[int],
                 alfabeto: List[str],
                 estados_finales: Set[int],
                 delta_transiciones: Dict[Tuple[int, str], Set[int]]):
        self.num_estados = cardinalidad_q
        self.alfabeto = alfabeto
        self.iniciales = frozenset(estados_iniciales)
        self.finales = frozenset(estados_finales)
        self.delta = delta_transiciones

    def clausura_transicion(self, origen: EstadoSubconjunto, simbolo: str) -> EstadoSubconjunto:
        """Calcula Delta(origen, simbolo) = Union_{q in origen} delta(q, simbolo)."""
        acumulador: Set[int] = set()
        for q in origen.elementos:
            destinos = self.delta.get((q, simbolo))
            if destinos:
                acumulador.update(destinos)
        return EstadoSubconjunto(frozenset(acumulador))

    def compilar_a_afd(self) -> 'AutomataDeterminista':
        """Aplica la Construcción de Subconjuntos mediante exploración por anchura (BFS)."""
        nodo_raiz = EstadoSubconjunto(self.iniciales)
        secuencia_estados: List[EstadoSubconjunto] = [nodo_raiz]
        registrados: Set[EstadoSubconjunto] = {nodo_raiz}
        tabla_delta: Dict[Tuple[EstadoSubconjunto, str], EstadoSubconjunto] = {}

        cola_bfs: deque[EstadoSubconjunto] = deque([nodo_raiz])
        while cola_bfs:
            macro_actual = cola_bfs.popleft()
            for simbolo in self.alfabeto:
                macro_destino = self.clausura_transicion(macro_actual, simbolo)
                tabla_delta[(macro_actual, simbolo)] = macro_destino

                if macro_destino not in registrados:
                    registrados.add(macro_destino)
                    secuencia_estados.append(macro_destino)
                    cola_bfs.append(macro_destino)

        macro_finales = {
            s for s in secuencia_estados
            if not s.elementos.isdisjoint(self.finales)
        }

        return AutomataDeterminista(
            afn_fuente=self,
            estado_inicial=nodo_raiz,
            estados_ordenados=secuencia_estados,
            alfabeto=self.alfabeto,
            estados_aceptacion=macro_finales,
            tabla_transiciones=tabla_delta
        )


class AutomataDeterminista:
    """Clase que modela el AFD equivalente M = (Q_D, Sigma, delta_D, s_0, F_D)."""

    def __init__(self,
                 afn_fuente: AutomataNoDeterminista,
                 estado_inicial: EstadoSubconjunto,
                 estados_ordenados: List[EstadoSubconjunto],
                 alfabeto: List[str],
                 estados_aceptacion: Set[EstadoSubconjunto],
                 tabla_transiciones: Dict[Tuple[EstadoSubconjunto, str], EstadoSubconjunto]):
        self.afn = afn_fuente
        self.inicio = estado_inicial
        self.estados = estados_ordenados
        self.alfabeto = alfabeto
        self.finales = estados_aceptacion
        self.transiciones = tabla_transiciones

    def generar_lineas_consola(self) -> List[str]:
        """Produce la matriz de texto tabular para la consola."""
        filas: List[Tuple[str, ...]] = [("", "") + tuple(self.alfabeto)]

        for estado in self.estados:
            etiqueta_direccion = ""
            if estado == self.inicio:
                etiqueta_direccion += "->"
            if estado in self.finales:
                etiqueta_direccion += "<-"

            destinos = tuple(
                self.transiciones[(estado, simb)].formato_consola()
                for simb in self.alfabeto
            )
            filas.append((etiqueta_direccion, estado.formato_consola()) + destinos)

        anchuras = [max(len(fila[c]) for fila in filas) for c in range(len(filas[0]))]
        lineas_formateadas = []
        for fila in filas:
            trozos = [val.ljust(ancho) for val, ancho in zip(fila, anchuras)]
            lineas_formateadas.append(" ".join(trozos).rstrip())
        return lineas_formateadas



# 2. Analizador sintatico

class LectorAutomata:
    """Parsea el flujo de texto de entrada sin heurísticas frágiles ni iteradores directos."""

    @staticmethod
    def _extraer_enteros(segmento: str) -> Set[int]:
        tokens = re.findall(r"\d+", segmento)
        return {int(tk) for tk in tokens if tk != "0"}

    @classmethod
    def procesar_texto(cls, texto_crudo: str) -> List[AutomataNoDeterminista]:
        lineas = [l.strip() for l in texto_crudo.splitlines() if l.strip()]
        if not lineas:
            return []

        cursor = 0
        total_casos = int(lineas[cursor])
        cursor += 1

        lista_afn: List[AutomataNoDeterminista] = []
        for _ in range(total_casos):
            n_estados = int(lineas[cursor])
            cursor += 1

            s_iniciales = cls._extraer_enteros(lineas[cursor])
            cursor += 1

            simbolos = lineas[cursor].split()
            if len(simbolos) == 1 and len(simbolos[0]) > 1:
                simbolos = list(simbolos[0])
            cursor += 1

            f_finales = cls._extraer_enteros(lineas[cursor])
            cursor += 1

            delta: Dict[Tuple[int, str], Set[int]] = {}
            for _ in range(n_estados):
                elementos = re.findall(r"\{[^}]*\}|\S+", lineas[cursor])
                cursor += 1

                id_estado = int(elementos[0])
                celdas = elementos[1:]

                for simb, celda in zip(simbolos, celdas):
                    delta[(id_estado, simb)] = cls._extraer_enteros(celda)

            afn = AutomataNoDeterminista(
                cardinalidad_q=n_estados,
                estados_iniciales=s_iniciales,
                alfabeto=simbolos,
                estados_finales=f_finales,
                delta_transiciones=delta
            )
            lista_afn.append(afn)

        return lista_afn



# 3. Renderizador SVG (pildoras y arcos)


class DiagramadorSVG:
    """
    Construye diagramas de autómatas vectoriales SVG usando un esquema visual
    basado en píldoras redondeadas (<rect rx="...">) y conectores bezier/arcos.
    Totalmente independiente y desacoplado de implementaciones ajenas.
    """

    ALTO_NODO = 38
    ESPACIO_NIVEL_X = 125
    ESPACIO_FILA_Y = 105

    @classmethod
    def crear_svg(cls, caso_num: int, afd: AutomataDeterminista) -> str:
        distancia: Dict[EstadoSubconjunto, int] = {afd.inicio: 0}
        cola = deque([afd.inicio])
        while cola:
            curr = cola.popleft()
            for a in afd.alfabeto:
                nxt = afd.transiciones[(curr, a)]
                if nxt not in distancia:
                    distancia[nxt] = distancia[curr] + 1
                    cola.append(nxt)

        capas: Dict[int, List[EstadoSubconjunto]] = {}
        for s in afd.estados:
            capas.setdefault(distancia[s], []).append(s)

        ancho_nodo: Dict[EstadoSubconjunto, float] = {
            s: max(72.0, len(s.formato_simbolico()) * 9.5 + 24.0)
            for s in afd.estados
        }

        max_filas = max(len(items) for items in capas.values())
        alto_lienzo = max(420.0, max_filas * cls.ESPACIO_FILA_Y + 160.0)

        pos_centro: Dict[EstadoSubconjunto, Tuple[float, float]] = {}
        offset_x = 75.0

        for nivel in sorted(capas.keys()):
            nodos_nivel = capas[nivel]
            max_w = max(ancho_nodo[s] for s in nodos_nivel)
            offset_x += max_w / 2.0

            total_en_capa = len(nodos_nivel)
            y_inicio = (alto_lienzo / 2.0) - ((total_en_capa - 1) * cls.ESPACIO_FILA_Y / 2.0)

            for i, s in enumerate(nodos_nivel):
                pos_centro[s] = (offset_x, y_inicio + i * cls.ESPACIO_FILA_Y)

            offset_x += max_w / 2.0 + cls.ESPACIO_NIVEL_X

        ancho_lienzo = offset_x + 60.0

        trans_agrupadas: Dict[Tuple[EstadoSubconjunto, EstadoSubconjunto], List[str]] = {}
        for s in afd.estados:
            for a in afd.alfabeto:
                destino = afd.transiciones[(s, a)]
                trans_agrupadas.setdefault((s, destino), []).append(a)

        arrow_id = f"mk-flecha-{caso_num}"
        init_id = f"mk-init-{caso_num}"

        fragmentos = [
            f'<svg id="grafo-afd-{caso_num}" xmlns="http://www.w3.org/2000/svg" '
            f'width="{round(ancho_lienzo)}" height="{round(alto_lienzo)}" '
            f'viewBox="0 0 {round(ancho_lienzo)} {round(alto_lienzo)}" role="img">',
            f'<defs>',
            f'<marker id="{arrow_id}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
            f'<path d="M 0 1 L 9 5 L 0 9 z" class="puntero-arista"/>'
            f'</marker>',
            f'<marker id="{init_id}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto">'
            f'<polygon points="0,1 9,5 0,9" class="puntero-inicio"/>'
            f'</marker>'
            f'</defs>'
        ]

        for (u, v), letras in trans_agrupadas.items():
            texto_arista = html.escape(",".join(letras))
            x1, y1 = pos_centro[u]
            x2, y2 = pos_centro[v]
            w1 = ancho_nodo[u]
            w2 = ancho_nodo[v]

            if u == v:
                top_y = y1 - cls.ALTO_NODO / 2.0
                fragmentos.append(
                    f'<path d="M {x1 - 15:.1f} {top_y:.1f} A 18 18 0 1 1 {x1 + 15:.1f} {top_y:.1f}" '
                    f'class="trazo-arista" marker-end="url(#{arrow_id})"/>'
                )
                fragmentos.append(f'<text x="{x1:.1f}" y="{top_y - 35:.1f}" class="texto-etiqueta">{texto_arista}</text>')
                continue

            dx = x2 - x1
            dy = y2 - y1

            # Nodos en la misma columna vertical: curvar hacia la DERECHA por fuera
            if abs(dx) < 2.0:
                sx = x1 + w1 / 2.0
                sy = y1
                tx = x2 + w2 / 2.0
                ty = y2
                dist_filas = abs(y1 - y2) / cls.ESPACIO_FILA_Y
                offset_curva = 35.0 + dist_filas * 24.0
                c_x = max(sx, tx) + offset_curva
                path_d = f"M {sx:.1f} {sy:.1f} C {c_x:.1f} {sy:.1f}, {c_x:.1f} {ty:.1f}, {tx:.1f} {ty:.1f}"
                apex_x = 0.25 * max(sx, tx) + 0.75 * c_x
                lbl_x = apex_x + 9.0
                lbl_y = (sy + ty) / 2.0
                fragmentos.append(f'<path d="{path_d}" class="trazo-arista" marker-end="url(#{arrow_id})"/>')
                fragmentos.append(f'<text x="{lbl_x:.1f}" y="{lbl_y:.1f}" class="texto-etiqueta">{texto_arista}</text>')

            # Transiciones hacia adelante (capas crecientes)
            elif dx > 0:
                sx = x1 + w1 / 2.0
                sy = y1
                tx = x2 - w2 / 2.0
                ty = y2
                dx_dist = tx - sx
                c1x = sx + dx_dist * 0.45
                c1y = sy
                c2x = tx - dx_dist * 0.45
                c2y = ty
                path_d = f"M {sx:.1f} {sy:.1f} C {c1x:.1f} {c1y:.1f}, {c2x:.1f} {c2y:.1f}, {tx:.1f} {ty:.1f}"
                lbl_x = sx + dx_dist * 0.42
                lbl_y = sy + (ty - sy) * 0.42 - 10.0
                fragmentos.append(f'<path d="{path_d}" class="trazo-arista" marker-end="url(#{arrow_id})"/>')
                fragmentos.append(f'<text x="{lbl_x:.1f}" y="{lbl_y:.1f}" class="texto-etiqueta">{texto_arista}</text>')

            # Transiciones hacia atrás (retorno a capa previa)
            else:
                if y1 > alto_lienzo / 2.0 and y2 >= alto_lienzo / 2.0:
                    # Origen y destino en la mitad inferior: curvar por debajo de las píldoras
                    sx = x1
                    sy = y1 + cls.ALTO_NODO / 2.0
                    tx = x2
                    ty = y2 + cls.ALTO_NODO / 2.0
                    curva_y = max(sy, ty) + 42.0
                    mid_x = (sx + tx) / 2.0
                    path_d = f"M {sx:.1f} {sy:.1f} Q {mid_x:.1f} {curva_y:.1f} {tx:.1f} {ty:.1f}"
                    mid_y = 0.25 * sy + 0.5 * curva_y + 0.25 * ty
                    lbl_x = mid_x
                    lbl_y = mid_y + 11.0
                else:
                    # Usar el pasillo central libre entre capas
                    sx = x1 - w1 / 2.0
                    sy = y1
                    tx = x2 + w2 / 2.0
                    ty = y2
                    corredor_x = (sx + tx) / 2.0
                    path_d = f"M {sx:.1f} {sy:.1f} C {corredor_x:.1f} {sy:.1f}, {corredor_x:.1f} {ty:.1f}, {tx:.1f} {ty:.1f}"
                    lbl_x = corredor_x - 12.0
                    lbl_y = (sy + ty) / 2.0 - 10.0

                fragmentos.append(f'<path d="{path_d}" class="trazo-arista" marker-end="url(#{arrow_id})"/>')
                fragmentos.append(f'<text x="{lbl_x:.1f}" y="{lbl_y:.1f}" class="texto-etiqueta">{texto_arista}</text>')

        # 6. Flecha de entrada al estado inicial
        ix, iy = pos_centro[afd.inicio]
        iw = ancho_nodo[afd.inicio]
        fragmentos.append(
            f'<line x1="{ix - iw / 2.0 - 44:.1f}" y1="{iy:.1f}" '
            f'x2="{ix - iw / 2.0 - 2:.1f}" y2="{iy:.1f}" '
            f'class="linea-inicio" marker-end="url(#{init_id})"/>'
        )

        # 7. Dibujar Nodos en forma de píldoras estilizadas
        for s in afd.estados:
            cx, cy = pos_centro[s]
            w = ancho_nodo[s]
            h = cls.ALTO_NODO
            rx_pill = h / 2.0

            clases_nodo = ["nodo-afd"]
            if s == afd.inicio:
                clases_nodo.append("nodo-es-inicio")
            if s in afd.finales:
                clases_nodo.append("nodo-es-final")
            if s.es_vacio:
                clases_nodo.append("nodo-es-trampa")

            txt_nodo = html.escape(s.formato_simbolico())
            c_str = " ".join(clases_nodo)

            fragmentos.append(f'<g class="{c_str}" data-state="{txt_nodo}">')
            # Fondo de la píldora
            fragmentos.append(
                f'<rect x="{cx - w/2.0:.1f}" y="{cy - h/2.0:.1f}" width="{w:.1f}" height="{h:.1f}" '
                f'rx="{rx_pill:.1f}" class="fondo-pildora"/>'
            )
            # Anillo concéntrico interno para estados de aceptación
            if s in afd.finales:
                fragmentos.append(
                    f'<rect x="{cx - w/2.0 + 3.5:.1f}" y="{cy - h/2.0 + 3.5:.1f}" '
                    f'width="{w - 7.0:.1f}" height="{h - 7.0:.1f}" rx="{rx_pill - 3.5:.1f}" '
                    f'class="borde-aceptacion"/>'
                )
            fragmentos.append(f'<text x="{cx:.1f}" y="{cy:.1f}" class="texto-nodo">{txt_nodo}</text>')
            fragmentos.append('</g>')

        fragmentos.append('</svg>')
        return "".join(fragmentos)



# 4. Generador del reporte web


ESTILOS_REPORT = """
:root {
  --bg-app: #f8fafc;
  --panel-card: #ffffff;
  --ink-primary: #0f172a;
  --ink-secondary: #475569;
  --border-line: #e2e8f0;
  --accent-cyan: #0284c7;
  --accent-blue: #2563eb;
  --accent-emerald: #059669;
  --subtle-blue: #eff6ff;
  --subtle-cyan: #f0f9ff;
  --subtle-emerald: #ecfdf5;
  --shadow-box: 0 4px 16px -2px rgba(15, 23, 42, 0.06);
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg-app: #090d16;
    --panel-card: #111827;
    --ink-primary: #f8fafc;
    --ink-secondary: #94a3b8;
    --border-line: #1e293b;
    --accent-cyan: #38bdf8;
    --accent-blue: #3b82f6;
    --accent-emerald: #10b981;
    --subtle-blue: #172554;
    --subtle-cyan: #082f49;
    --subtle-emerald: #064e3b;
    --shadow-box: none;
  }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg-app); color: var(--ink-primary); font: 15px/1.6 system-ui,-apple-system,sans-serif; }
.hero-header { background: #0b1329; color: #fff; padding: 48px 24px 64px; border-bottom: 3px solid var(--accent-blue); }
.hero-content { max-width: 1120px; margin: 0 auto; }
.badge-course { display: inline-block; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.15); border-radius: 6px; padding: 3px 10px; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 12px; }
.hero-header h1 { margin: 0 0 6px; font-size: 28px; letter-spacing: -0.02em; }
.hero-header p { margin: 0; color: #94a3b8; font-size: 15px; }
.page-container { max-width: 1120px; margin: -32px auto 60px; padding: 0 20px; }
.card-section { background: var(--panel-card); border: 1px solid var(--border-line); border-radius: 14px; box-shadow: var(--shadow-box); padding: 26px; margin-bottom: 28px; }
.card-section h2 { margin: 0 0 16px; font-size: 20px; }
.summary-bar { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px; }
.pill-stat { background: var(--bg-app); border: 1px solid var(--border-line); border-radius: 8px; padding: 5px 12px; font-size: 13px; color: var(--ink-secondary); }
.pill-stat b { color: var(--ink-primary); margin-left: 4px; }
.diagram-frame { overflow-x: auto; border: 1px solid var(--border-line); border-radius: 12px; padding: 14px; background: var(--bg-app); }
svg { display: block; margin: 0 auto; }

/* SVG Styles */
.trazo-arista { fill: none; stroke: var(--ink-secondary); stroke-width: 1.8; }
.puntero-arista { fill: var(--ink-secondary); }
.linea-inicio { stroke: var(--accent-blue); stroke-width: 2.4; }
.puntero-inicio { fill: var(--accent-blue); }
.texto-etiqueta { font: 700 13px ui-monospace,monospace; fill: var(--accent-blue); text-anchor: middle; dominant-baseline: central; stroke: var(--panel-card); stroke-width: 4; paint-order: stroke; stroke-linejoin: round; }
.fondo-pildora { fill: var(--panel-card); stroke: var(--accent-blue); stroke-width: 2; transition: all 0.2s ease; }
.nodo-es-inicio .fondo-pildora { fill: var(--subtle-cyan); stroke: var(--accent-cyan); }
.borde-aceptacion { fill: none; stroke: var(--accent-emerald); stroke-width: 2; }
.nodo-es-final .fondo-pildora { stroke: var(--accent-emerald); }
.nodo-es-final .borde-aceptacion { fill: var(--subtle-emerald); }
.nodo-es-trampa .fondo-pildora { stroke: var(--ink-secondary); stroke-dasharray: 4 4; }
.texto-nodo { font: 600 13px ui-monospace,monospace; fill: var(--ink-primary); text-anchor: middle; dominant-baseline: central; }
.nodo-resaltado .fondo-pildora { stroke: #f59e0b !important; stroke-width: 3.5px !important; fill: #fef3c7 !important; }
@media (prefers-color-scheme: dark) {
  .nodo-resaltado .fondo-pildora { stroke: #fbbf24 !important; stroke-width: 3.5px !important; fill: #451a03 !important; }
}

/* Legend */
.legend-panel { display: flex; flex-wrap: wrap; gap: 18px; margin-top: 12px; font-size: 13px; color: var(--ink-secondary); }
.lg-item { display: flex; align-items: center; gap: 6px; }
.circle-mark { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.c-start { background: var(--accent-cyan); }
.c-final { background: var(--accent-emerald); }
.c-trap { background: var(--ink-secondary); }

/* Tables */
.table-box { overflow-x: auto; border: 1px solid var(--border-line); border-radius: 10px; margin-top: 12px; }
table.matriz { width: 100%; border-collapse: collapse; font-size: 14px; text-align: left; }
table.matriz th, table.matriz td { padding: 10px 14px; border-bottom: 1px solid var(--border-line); }
table.matriz th { background: var(--bg-app); color: var(--ink-secondary); font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; }
table.matriz tr:last-child td { border-bottom: none; }
table.matriz tbody tr:hover { background: var(--subtle-blue); }
td.w-fit { width: 1%; white-space: nowrap; }
.cell-mono { font-family: ui-monospace,monospace; }
.cell-empty { color: var(--ink-secondary); opacity: 0.6; }
.tag { display: inline-block; border-radius: 6px; padding: 2px 7px; margin-right: 4px; font-size: 11px; font-weight: 700; text-transform: uppercase; }
.tag-start { background: var(--subtle-cyan); color: var(--accent-cyan); }
.tag-final { background: var(--subtle-emerald); color: var(--accent-emerald); }

/* Interactive Simulator */
.simulator-panel { background: var(--bg-app); border: 1px solid var(--border-line); border-radius: 12px; padding: 16px; margin: 20px 0 10px; }
.sim-controls { display: flex; gap: 10px; align-items: center; margin-top: 10px; flex-wrap: wrap; }
.sim-textbox { padding: 9px 14px; border-radius: 8px; border: 1px solid var(--border-line); background: var(--panel-card); color: var(--ink-primary); font-family: ui-monospace,monospace; font-size: 14px; min-width: 280px; outline: none; }
.sim-textbox:focus { border-color: var(--accent-blue); }
.btn-run { padding: 9px 18px; background: var(--accent-blue); color: #fff; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; transition: opacity 0.15s; }
.btn-run:hover { opacity: 0.9; }
.btn-reset { padding: 9px 14px; background: transparent; color: var(--ink-secondary); border: 1px solid var(--border-line); border-radius: 8px; font-weight: 600; cursor: pointer; }
.sim-display { margin-top: 12px; font-size: 13px; }
.verdict-pass { background: #dcfce7; color: #15803d; padding: 4px 10px; border-radius: 6px; font-weight: 700; }
.verdict-fail { background: #fee2e2; color: #b91c1c; padding: 4px 10px; border-radius: 6px; font-weight: 700; }
@media (prefers-color-scheme: dark) {
  .verdict-pass { background: #064e3b; color: #6ee7b7; }
  .verdict-fail { background: #450a0a; color: #fca5a5; }
}
footer { text-align: center; color: var(--ink-secondary); font-size: 13px; padding: 10px 0 40px; }
"""


def _construir_seccion_html(indice: int, afd: AutomataDeterminista) -> str:
    afn = afd.afn
    th_cols = "".join(f"<th>{html.escape(s)}</th>" for s in afd.alfabeto)

    # Filas de tabla AFD
    filas_afd = []
    for s in afd.estados:
        etiquetas = ""
        if s == afd.inicio:
            etiquetas += '<span class="tag tag-start">start</span>'
        if s in afd.finales:
            etiquetas += '<span class="tag tag-final">final</span>'

        celdas_simb = "".join(
            f'<td class="cell-mono{"" if not afd.transiciones[(s, a)].es_vacio else " cell-empty"}">'
            f'{html.escape(afd.transiciones[(s, a)].formato_simbolico())}</td>'
            for a in afd.alfabeto
        )
        filas_afd.append(
            f'<tr><td class="w-fit">{etiquetas}</td>'
            f'<td class="cell-mono"><b>{html.escape(s.formato_simbolico())}</b></td>'
            f'{celdas_simb}</tr>'
        )

    # Filas de tabla AFN fuente
    filas_afn = []
    for q in range(1, afn.num_estados + 1):
        etiquetas = ""
        if q in afn.iniciales:
            etiquetas += '<span class="tag tag-start">start</span>'
        if q in afn.finales:
            etiquetas += '<span class="tag tag-final">final</span>'

        celdas_simb = []
        for a in afn.alfabeto:
            dest = afn.delta.get((q, a), set())
            txt = "{" + " ".join(map(str, sorted(dest))) + "}" if dest else "∅"
            celdas_simb.append(f'<td class="cell-mono{"" if dest else " cell-empty"}">{html.escape(txt)}</td>')

        filas_afn.append(
            f'<tr><td class="w-fit">{etiquetas}</td>'
            f'<td class="cell-mono"><b>{q}</b></td>'
            f'{"".join(celdas_simb)}</tr>'
        )

    svg_markup = DiagramadorSVG.crear_svg(indice, afd)

    pildoras = "".join(
        f'<div class="pill-stat">{lbl}: <b>{html.escape(val)}</b></div>'
        for lbl, val in [
            ("NFA States", str(afn.num_estados)),
            ("Alphabet", " ".join(afd.alfabeto)),
            ("DFA States", str(len(afd.estados))),
            ("Accepting States", str(len(afd.finales))),
            ("Initial State", afd.inicio.formato_simbolico())
        ]
    )

    return f"""<section class="card-section">
<h2>Case {indice}</h2>
<div class="summary-bar">{pildoras}</div>

<div style="font-size:12px;font-weight:700;text-transform:uppercase;color:var(--ink-secondary);margin:16px 0 8px;">DFA State Diagram</div>
<div class="diagram-frame">{svg_markup}</div>
<div class="legend-panel">
  <div class="lg-item"><span class="circle-mark c-start"></span> Initial state (entry arrow)</div>
  <div class="lg-item"><span class="circle-mark c-final"></span> Double border = Accepting state</div>
  <div class="lg-item"><span class="circle-mark c-trap"></span> Dashed = Trap/Empty state ∅ (0 in console)</div>
</div>

<div class="simulator-panel">
  <strong>Interactive String Simulator:</strong> Test strings over {{{', '.join(afd.alfabeto)}}} against this DFA.
  <div class="sim-controls">
    <input type="text" id="sim-input-{indice}" class="sim-textbox" placeholder="Type test string (e.g. abba) and hit Enter" onkeydown="if(event.key==='Enter') simularPalabra({indice})">
    <button class="btn-run" onclick="simularPalabra({indice})">Evaluate</button>
    <button class="btn-reset" onclick="limpiarSimulador({indice})">Reset</button>
  </div>
  <div id="sim-log-{indice}" class="sim-display"></div>
</div>

<div style="font-size:12px;font-weight:700;text-transform:uppercase;color:var(--ink-secondary);margin:24px 0 8px;">DFA Transition Matrix</div>
<div class="table-box"><table class="matriz"><thead><tr><th class="w-fit"></th><th>State</th>{th_cols}</tr></thead>
<tbody>{"".join(filas_afd)}</tbody></table></div>

<details style="margin-top:20px;"><summary style="cursor:pointer;color:var(--ink-secondary);font-weight:600;">View Input NFA Matrix</summary>
<div class="table-box" style="margin-top:8px;"><table class="matriz"><thead><tr><th class="w-fit"></th><th>State</th>{th_cols}</tr></thead>
<tbody>{"".join(filas_afn)}</tbody></table></div>
</details>
</section>"""


def generar_reporte_completo(afds: List[AutomataDeterminista]) -> str:
    bloques = "".join(_construir_seccion_html(i, a) for i, a in enumerate(afds, 1))

    # Estructura JSON para la simulación
    payload_js = {}
    for i, afd in enumerate(afds, 1):
        payload_js[i] = {
            "alfabeto": afd.alfabeto,
            "inicio": afd.inicio.formato_simbolico(),
            "finales": [s.formato_simbolico() for s in afd.finales],
            "delta": {
                s.formato_simbolico(): {
                    a: afd.transiciones[(s, a)].formato_simbolico()
                    for a in afd.alfabeto
                }
                for s in afd.estados
            }
        }

    js_code = f"""
<script>
const motor_datos = {json.dumps(payload_js)};

function simularPalabra(cid) {{
    const datos = motor_datos[cid];
    const txtInput = document.getElementById('sim-input-' + cid);
    const boxLog = document.getElementById('sim-log-' + cid);
    const svgEl = document.getElementById('grafo-afd-' + cid);

    if (svgEl) {{
        svgEl.querySelectorAll('.nodo-afd').forEach(n => n.classList.remove('nodo-resaltado'));
    }}

    const w = txtInput.value.trim();
    let curr = datos.inicio;
    let recorrido = [];

    for (let i = 0; i < w.length; i++) {{
        const char = w[i];
        if (!datos.alfabeto.includes(char)) {{
            boxLog.innerHTML = `<span class="verdict-fail">Error: Symbol '<b>${{char}}</b>' not in alphabet [${{datos.alfabeto.join(', ')}}]</span>`;
            return;
        }}
        const nextState = datos.delta[curr] ? datos.delta[curr][char] : "∅";
        recorrido.push(`<b>${{curr}}</b> ──(${{char}})──> <b>${{nextState}}</b>`);
        curr = nextState;
    }}

    const pasa = datos.finales.includes(curr);
    const badge = pasa
        ? `<span class="verdict-pass">✓ ACCEPTED (Final state ${{curr}} ∈ F)</span>`
        : `<span class="verdict-fail">✗ REJECTED (Final state ${{curr}} ∉ F)</span>`;

    if (svgEl) {{
        const targetNode = svgEl.querySelector(`[data-state="${{curr}}"]`);
        if (targetNode) targetNode.classList.add('nodo-resaltado');
    }}

    const pasosHtml = recorrido.length > 0
        ? `<div style="margin-top:8px; color:var(--ink-secondary); line-height:1.7;">${{recorrido.join(' &nbsp;•&nbsp; ')}}</div>`
        : `<div style="margin-top:8px; color:var(--ink-secondary);">Empty string λ (starts and halts in state ${{curr}})</div>`;

    boxLog.innerHTML = `<div>${{badge}}</div>${{pasosHtml}}`;
}}

function limpiarSimulador(cid) {{
    document.getElementById('sim-input-' + cid).value = '';
    document.getElementById('sim-log-' + cid).innerHTML = '';
    const svgEl = document.getElementById('grafo-afd-' + cid);
    if (svgEl) svgEl.querySelectorAll('.nodo-afd').forEach(n => n.classList.remove('nodo-resaltado'));
}}
</script>
"""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>NFA to DFA Conversion Engine · Formal Languages</title>
<style>{ESTILOS_REPORT}</style>
</head>
<body>
<header class="hero-header">
  <div class="hero-content">
    <div class="badge-course">SI2002 Formal Languages · Assignment 2 · EAFIT</div>
    <h1>NFA to DFA Subset Construction System</h1>
    <p>Algorithmic determinization based on Dexter Kozen (1997) · {len(afds)} case{"s" if len(afds) != 1 else ""} processed</p>
  </div>
</header>
<main class="page-container">
{bloques}
</main>
<footer>Generated by conversor_afn_afd.py · Department of Computer Science · Universidad EAFIT</footer>
{js_code}
</body>
</html>
"""



# 5. Main


def main():
    args = sys.argv[1:]
    html_target = None
    if "--html" in args:
        idx = args.index("--html")
        if idx + 1 < len(args) and not args[idx + 1].startswith("-"):
            html_target = args[idx + 1]
        else:
            html_target = "output.html"

    buffer_entrada = sys.stdin.read()
    if not buffer_entrada.strip():
        return

    afns = LectorAutomata.procesar_texto(buffer_entrada)
    afds = []
    for afn in afns:
        afd = afn.compilar_a_afd()
        afds.append(afd)
        print("\n".join(afd.generar_lineas_consola()))

    if html_target:
        Path(html_target).write_text(generar_reporte_completo(afds), encoding="utf-8")


if __name__ == "__main__":
    main()
