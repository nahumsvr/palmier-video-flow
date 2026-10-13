#!/usr/bin/env python3
"""Convierte eventos de edición en entradas de `add_clips` para efectos de sonido.

Entrada JSON (archivo o stdin):
  {"events": [{"frame": 1289, "role": "cifra"}, {"frame": 1215, "role": "zoom"}],
   "media": {"5 - Camera Click": "F6DEABC9", "3 - Whoosh 3": "7577A628"},
   "min_gap": 12}

`media` asocia nombre de efecto y mediaRef de Palmier (`get_media`, carpeta Efectos). Cada
rol elige efecto de una lista que se rota para no repetir, adelanta el inicio unos
fotogramas y fija un volumen. Avisa de efectos del mismo recurso demasiado juntos y de
efectos que no están importados. No toca el editor.
"""
import argparse
import json
import sys

# rol: (efectos en rotación, adelanto en fotogramas, volumen dB)
ROLES = {
    'impacto_capitulo': (('17 - Camera Shutter 2',), 0, -8),
    'salida_capitulo': (('14 - Quick Whoosh', '15 - Quick Whoosh 2'), 0, -14),
    'zoom': (('3 - Whoosh 3', '4 - Whoosh 4', '1 - Whoosh', '2 - Whoosh 2'), 0, -14),
    'corte': (('9 - Whoosh 8', '8 - Whoosh 7', '7 - Whoosh 6', '10 - Whoosh 9', '20 - Swish Whoosh'), 2, -18),
    'cifra': (('5 - Camera Click',), 0, -12),
    'remate': (('16 - Camera Shutter',), 0, -14),
    'impacto_grande': (('12 - Jet Whoosh',), 4, -12),
    'transicion': (('13 - Smooth Whoosh', '18 - Whoosh Wind', '19 - Remembering Whoosh'), 2, -14),
}


def plan(spec):
    media = spec.get('media', {})
    min_gap = spec.get('min_gap', 12)
    counters = {}
    entries, warnings, missing, last_start = [], [], [], {}
    for event in sorted(spec['events'], key=lambda e: e['frame']):
        role = event['role']
        if role not in ROLES:
            raise ValueError('rol desconocido: ' + role)
        pool, lead, volume = ROLES[role]
        name = event.get('effect') or pool[counters.get(role, 0) % len(pool)]
        counters[role] = counters.get(role, 0) + 1
        start = max(0, event['frame'] - lead)
        ref = media.get(name)
        if ref is None:
            missing.append(name)
            continue
        if ref in last_start and start - last_start[ref] < min_gap:
            warnings.append('«%s» repetido a %d fotogramas en %d' % (name, start - last_start[ref], start))
        last_start[ref] = start
        entries.append({'mediaRef': ref, 'startFrame': start, 'volumeDb': volume, 'effect': name, 'role': role})
    by_volume = {}
    for entry in entries:
        by_volume.setdefault(entry['volumeDb'], []).append(entry['startFrame'])
    return {'add_clips_entries': [{'mediaRef': e['mediaRef'], 'startFrame': e['startFrame']} for e in entries],
            'detail': entries, 'volume_groups': {str(k): v for k, v in sorted(by_volume.items())},
            'missing_effects': sorted(set(missing)), 'warnings': warnings}


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
