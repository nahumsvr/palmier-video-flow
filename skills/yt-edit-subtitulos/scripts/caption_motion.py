#!/usr/bin/env python3
"""Keyframes de entrada de captions (subida con rebote y desenfoque de movimiento).

Subcomandos:
  rows   Lee [{"id", "duration", "x", "yf"}] y devuelve keyframes `position`, `blur` y `fadeInFrames`.
         `x`, `yf`: esquina superior izquierda FINAL del clip (coordenadas 0-1); `duration` en fotogramas.
  sizes  Lee width/height/centro de clips de un project.json (solo lectura) y calcula x e yf
         para que el texto quede centrado en x = 0.5 sobre su `y` actual.

Receta (30 fps): sube 0.045 desde abajo, pasa 0.012 de largo, baja 0.004 y asienta;
el desenfoque va de 14 px a 0 y el fundido dura 2 fotogramas. Clips cortos comprimen la
entrada; los de 1-2 fotogramas no se animan. Los keyframes de posición son absolutos
(esquina superior izquierda): si cambia el tamaño o el texto del clip hay que recalcularlos.
"""
import argparse
import json
import sys

OFFSETS = (0.045, -0.012, 0.004, 0.0)
BLUR_VALUES = (14, 4, 0)
FADE_IN = 2
# duración mínima -> (fotogramas de posición, fotogramas de desenfoque)
SHAPES = ((6, (0, 2, 4, 6), (0, 3, 5)),
          (5, (0, 2, 3, 5), (0, 2, 4)),
          (4, (0, 1, 3, 4), (0, 2, 3)),
          (3, (0, 1, 2, 3), (0, 2, 3)))


def motion(duration, x, yf, decimals=3):
    if type(duration) is not int or duration < 1:
        raise ValueError('duration debe ser un entero positivo')
    for minimum, pos_frames, blur_frames in SHAPES:
        if duration >= minimum:
            position = [[f, round(x, decimals), round(yf + o, decimals)] for f, o in zip(pos_frames, OFFSETS)]
            blur = [[f, v] for f, v in zip(blur_frames, BLUR_VALUES)]
            return {'position': position, 'blur': blur, 'fadeInFrames': FADE_IN}
    return None


def rows(items):
    result = []
    for item in items:
        entry = {'id': item.get('id')}
        found = motion(item['duration'], item['x'], item['yf'])
        entry.update(found if found else {'position': None, 'blur': None, 'fadeInFrames': 0,
                                          'note': 'clip de 1-2 fotogramas: sin animación'})
        result.append(entry)
    return result


def centered_corner(center_x, center_y, width, height, decimals=4):
    return {'x': round(center_x - width / 2, decimals), 'yf': round(center_y - height / 2, decimals)}


def find_clips(node, prefixes, found):
    if isinstance(node, dict):
        clip_id = node.get('id')
        transform = node.get('transform')
        if isinstance(clip_id, str) and isinstance(transform, dict) and 'width' in transform:
            for prefix in prefixes:
                if clip_id.upper().startswith(prefix.upper()):
                    found[prefix] = (clip_id, transform)
        for value in node.values():
            find_clips(value, prefixes, found)
    elif isinstance(node, list):
        for value in node:
            find_clips(value, prefixes, found)


def sizes(project_json, prefixes):
    with open(project_json, encoding='utf-8') as handle:
        data = json.load(handle)
    found = {}
    find_clips(data, prefixes, found)
    result = []
    for prefix in prefixes:
        if prefix not in found:
            result.append({'id': prefix, 'error': 'no encontrado'})
            continue
        clip_id, t = found[prefix]
        corner = centered_corner(t.get('centerX', 0.5), t.get('centerY', 0.5), t['width'], t['height'])
        result.append({'id': prefix, 'full_id': clip_id, 'width': t['width'], 'height': t['height'],
                       'centerX': t.get('centerX', 0.5), 'centerY': t.get('centerY', 0.5), **corner})
    return result


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = cli.add_subparsers(dest='command', required=True)
    rows_cmd = commands.add_parser('rows', help='Keyframes por clip')
    rows_cmd.add_argument('items', nargs='?', help='JSON de clips; sin argumento lee la entrada estándar')
    sizes_cmd = commands.add_parser('sizes', help='Tamaño y esquina centrada leídos de un project.json')
    sizes_cmd.add_argument('project_json')
    sizes_cmd.add_argument('ids', nargs='+', help='Prefijos de ID de clip')
    args = cli.parse_args(argv)
    try:
        if args.command == 'rows':
            text = open(args.items, encoding='utf-8').read() if args.items else sys.stdin.read()
            output = rows(json.loads(text))
        else:
            output = sizes(args.project_json, args.ids)
    except (KeyError, ValueError, TypeError, OSError) as error:
        print('Error: ' + str(error), file=sys.stderr)
        return 1
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
