#!/usr/bin/env python3
"""Calcula filas de keyframes `scale` y `position` de Palmier Pro para zooms.

Entrada JSON (archivo o stdin):
  {"canvas": [1920, 1080], "media": [2360, 1640], "fit": "contain",
   "rows": [{"frame": 0, "zoom": 1.0},
            {"frame": 10, "zoom": 1.5, "focus": [0.5, 0.04]}]}

`zoom` es el factor sobre el encuadre base (1.0 = encuadre completo o de relleno).
`focus` es el punto de la fuente, en 0-1, que debe quedar en el centro de pantalla; si
no cabe sin mostrar bordes vacíos se limita. Sin `focus` el zoom queda centrado.
Salida: base estática, filas `scale` [frame, ancho, alto] y filas `position` [frame, x, y]
(esquina superior izquierda, coordenadas 0-1 del lienzo), listas para `set_keyframes`.
"""
import argparse
import json
import sys

FITS = ('contain', 'cover')


def base_size(canvas, media, fit):
    cw, ch = canvas
    mw, mh = media
    ratio = min(cw / mw, ch / mh) if fit == 'contain' else max(cw / mw, ch / mh)
    return mw * ratio / cw, mh * ratio / ch


def axis_origin(size, focus):
    """Esquina de un eje: centrada si la imagen cabe; limitada para no mostrar bordes si no."""
    if size <= 1:
        return (1 - size) / 2
    return min(0.0, max(1 - size, 0.5 - focus * size))


def build(spec):
    canvas = spec['canvas']
    media = spec['media']
    fit = spec.get('fit', 'contain')
    decimals = spec.get('decimals', 4)
    if fit not in FITS:
        raise ValueError('fit debe ser contain o cover')
    if len(canvas) != 2 or len(media) != 2 or min(canvas + media) <= 0:
        raise ValueError('canvas y media necesitan [ancho, alto] positivos')
    rows = spec['rows']
    if not rows:
        raise ValueError('rows está vacío')
    base_w, base_h = base_size(canvas, media, fit)
    scale, position, centered = [], [], True
    last = -1
    for row in rows:
        frame, zoom = row['frame'], row['zoom']
        if type(frame) is not int or frame < 0 or frame <= last:
            raise ValueError('frame debe ser entero, no negativo y creciente')
        if zoom <= 0:
            raise ValueError('zoom debe ser positivo')
        last = frame
        focus = row.get('focus')
        if focus is not None:
            if len(focus) != 2 or not all(0 <= v <= 1 for v in focus):
                raise ValueError('focus necesita [x, y] entre 0 y 1')
            centered = False
        fx, fy = focus if focus is not None else (0.5, 0.5)
        w, h = base_w * zoom, base_h * zoom
        extra = [row['interp']] if row.get('interp') else []
        scale.append([frame, round(w, decimals), round(h, decimals)] + extra)
        position.append([frame, round(axis_origin(w, fx), decimals), round(axis_origin(h, fy), decimals)] + extra)
    return {'base': {'width': round(base_w, decimals), 'height': round(base_h, decimals)},
            'fit': fit, 'scale': scale, 'position': position,
            'scale_only_is_enough': centered}


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    cli.add_argument('spec', nargs='?', help='JSON de entrada; sin argumento lee la entrada estándar')
    args = cli.parse_args(argv)
    text = open(args.spec, encoding='utf-8').read() if args.spec else sys.stdin.read()
    try:
        print(json.dumps(build(json.loads(text)), ensure_ascii=False, indent=2))
    except (KeyError, ValueError, TypeError) as error:
        print('Error: ' + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
