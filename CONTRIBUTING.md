# Contribuir

Trabaja en una rama breve desde `main`, con un propósito por cambio. Usa Conventional Commits, por ejemplo `docs(usage): explain publication tracking` o `fix(calendar): preserve confirmed dates`.

## Comprobaciones

```bash
python3 -m unittest discover -s skills/yt-video-flow/scripts -p 'test_*.py' -v
python3 -m unittest discover -s tests -p 'test_*.py' -v
git diff --check
```

Las pruebas del flujo cubren workspaces temporales, reservas, estados de recursos, anclajes y entregas. Las del repositorio comprueban distribución, enlaces, ejemplos y el planificador de rangos. No necesitan Palmier ni acceso a Internet; no prueban la calidad audiovisual de una edición real.

Conserva la fuente de verdad y los bloques editoriales del usuario. Para cambios de esquema define cómo se conservarán registros existentes y agrega una prueba del comportamiento. Si cambias comandos, actualiza guías y ejemplos.

Los episodios y medios son datos locales ignorados. Stagea rutas explícitas de herramientas/documentación y revisa el diff antes de guardar. No publiques rutas personales, transcripciones reales ni credenciales en fixtures.

No se eligió una licencia de distribución todavía. No añadas ni cambies una licencia sin decisión del titular.
