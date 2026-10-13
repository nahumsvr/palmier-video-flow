#!/usr/bin/env python3
"""Planifica tarjetas negras de capítulo insertadas con ripple.

Entrada JSON (archivo o stdin):
  {"cuts": [1192, 2172, 4525], "card_frames": 36, "total_frames": 6351,
   "map_frames": [3515, 4105]}

`cuts` son los fotogramas del corte ORIGINAL donde se inserta cada tarjeta, en fotogramas
del timeline antes de insertar. Devuelve el orden seguro de inserción (de atrás hacia
adelante), el inicio final de cada tarjeta, la duración nueva y, si se piden, los
fotogramas originales trasladados al timeline resultante.
"""
import argparse
import json
import sys


def shift(frame, cuts, card_frames):
    return frame + card_frames * sum(1 for c in cuts if c <= frame)


def plan(spec):
    cuts = spec['cuts']
    card = spec['card_frames']
    total = spec['total_frames']
    if type(card) is not int or card < 1:
        raise ValueError('card_frames debe ser un entero positivo')
    if any(type(c) is not int or c < 0 or c > total for c in cuts):
        raise ValueError('cada corte debe ser un entero entre 0 y total_frames')
    if len(set(cuts)) != len(cuts):
        raise ValueError('hay cortes repetidos')
    ordered = sorted(cuts)
    cards = [{'original_cut': c, 'start': c + card * i, 'end': c + card * (i + 1)} for i, c in enumerate(ordered)]
    result = {'insert_order_desc': sorted(cuts, reverse=True), 'cards': cards,
              'new_total_frames': total + card * len(cuts)}
    if spec.get('map_frames'):
        result['mapped'] = {str(f): shift(f, ordered, card) for f in spec['map_frames']}
    return result


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    cli.add_argument('spec', nargs='?', help='JSON de entrada; sin argumento lee la entrada estándar')
    args = cli.parse_args(argv)
    text = open(args.spec, encoding='utf-8').read() if args.spec else sys.stdin.read()
    try:
        print(json.dumps(plan(json.loads(text)), ensure_ascii=False, indent=2))
    except (KeyError, ValueError, TypeError) as error:
        print('Error: ' + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
