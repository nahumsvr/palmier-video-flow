# Resultados por etapa

Solo ejecutar la etapa pedida y las tareas necesarias para hacerla concreta. Para retomar, consultar el calendario, el estado y el editor; no confiar exclusivamente en el historial de conversación.

## Crear / definir

Crear primero registro local e ID, después proyecto Palmier y vinculación. Si falta idea, no inventar un episodio. Un bloqueo del editor conserva el registro para reintentar con el mismo ID.

Al recibir idea, actualizar `idea` y `nombre` sin cambiar carpetas. Elaborar brief y guion: objetivo, promesa demostrable, público, relación con la serie, gancho, contexto, desarrollo, resultado y cierre. Señalar qué graba el usuario, qué podemos reutilizar y qué hace falta obtener. Una promesa de «mostrar el antes» necesita material real de antes.

Preparar también propuestas iniciales de títulos/miniatura. El título recomendado se mantiene como propuesta editorial; `publicacion.titulo_elegido` queda vacío hasta elegirlo. Proponer importancia con motivo: alta para un compromiso temporal explícito o continuación necesaria, media para episodio habitual, baja para experimento no urgente. Confirmar datos desconocidos solo si afectan el trabajo actual.

## Grabar / preparar

El usuario captura voz/gameplay y deja fuentes en `crudo/` o informa su ubicación. No mover crudos externos adoptados. Inspeccionar duración, dimensiones, fps y streams; identificar realmente la voz y evitar duplicarla con el audio del juego.

Registrar cada fuente inspeccionada en `recursos`, con rol y ruta estable. Consultar proyecto/Assets antes de reimportar o generar. Importar en carpetas por función; esperar readiness según recibo antes de colocar. Marcar `importado` solo tras comprobar mediaRef/assetRef; `en_video` requiere timeline y clipIds reales. Si solo se necesita apoyo visual, no introducir su audio bajo la narración.

Proyectos nuevos: 1920 × 1080, 30 fps. Ajustar la composición con las operaciones de layout de Palmier, preservando elementos importantes del juego. Mantener formato de proyectos existentes. Establecer el timeline original y la relación de video/voz/audio vinculados; guardar evidencia antes de cortar.

## Montar / editar

Aplicar `yt-cut-hi` en el montaje del diálogo. Su original conserva cobertura/duración aunque reciba splits; `Ideas completas` contiene el montaje. No usar «todos los silencios» como criterio editorial ni volver a eliminar rangos en audios ya desplazados por ripple.

En edición, crear una copia del montaje llamada `Edición` solo si no existe el ID registrado. Colocar recursos por encima en pistas propias para conservar narración y duración; insertar en medio únicamente cuando se necesita añadir un segmento y sincronizar el desplazamiento. Trabajar por función: explicar cifra/objeto, demostrar cambio, dar contexto o reforzar un remate.

Actualizar `notas.md` con decisiones, recursos y estados de tareas. Los estados de material se generan desde JSON; una tarea puede seguir pendiente con material ya importado. Si un apoyo imprescindible no existe, avanzar con tareas independientes y registrar el bloqueo sin fingir que está resuelto.

Guardar snapshot del corte actual después de cambios y antes de revisión/exportación. Cambios de tracks/clips/frames alteran su firma; movimiento del cursor no. Releer transcripción y mapear las notas por frase/fuente. Tras revisar sus posiciones, registrar la firma de notas. El helper no ajusta automáticamente texto editorial ni remapea tiempos.

## Revisar

Guardar evidencia de comprobaciones estructurales: sincronía, cobertura, uniones, frases completas, encuadre, textos y material prometido. Registrar `revision.estructura`, `revision.firma` y archivo de evidencia solo con resultados reales.

Revisar reproducción audiovisual cuando esté disponible. Si no es posible, entregar los tramos a revisar al usuario y dejar `audiovisual=false`; se puede marcar después de su revisión explícita. Nunca sustituir escucha por transcript o imágenes. `listo` significa corte revisado para entrega; la condición más exigente `listo_para_publicar` incluye exportación, miniatura, descripción, título y fecha.

Si se cambia el corte revisado, tomar otro snapshot y actualizar las verificaciones afectadas. No copiar aprobaciones de una versión anterior automáticamente. Cuando solo se cambian fechas/título, no hay que volver a editar el video.

## Exportar / publicación / archivo

Ante «exporta el video», usar ID final explícito y nombre versionado que no exista. Registrar jobId y estado `en_proceso` inmediatamente. Esperar resultado terminal con `manage_exports`; errores/advertencias se anotan, sin reenviar un trabajo pendiente por tardar. Verificar archivo real (streams, fps, resolución, duración y reproducción cuando esté disponible), registrar firma/timeline y resultados. Solo entonces `completada`, `verificado=true` y etapa `exportado`.

Descripción: redactar apertura y resumen fieles al episodio, pregunta/CTA y enlaces proporcionados. Generar capítulos únicamente con anclajes del corte final; no conservar tiempos de otro corte. Miniatura: tres composiciones realizables, cada una con captura/objeto protagonista, distribución, texto corto, contraste/colores y título compatible. El usuario crea la imagen; `lista` necesita archivo final existente.

La fecha propuesta reserva un día y sigue siendo tentativa con bloqueos. Una fecha confirmada es una decisión editorial; una programación es un hecho en YouTube informado por el usuario con hora/offset. Si informa una programación/publicación que coincide con otra, registrar el hecho y mostrar conflicto sin cambiar ninguno. Para publicado, registrar fecha/hora y URL real.

Archivar solo por pedido: `export_project(mode="palmier")` a un nombre nuevo dentro de `archivo/`; esperar resultado, comprobar paquete y advertencias de medios faltantes. No editar su interior ni eliminar fuentes. Registrar `archivo` completado/verificado; conservar fecha publicada y URL al pasar a etapa `archivado`.

## Fallos y reanudación

- Editor desconectado o proyecto no visible: conservar ID/ruta y registrar actividad bloqueada. No abrir otro proyecto para completar la edición por accidente.
- Importación/generación pendiente: consultar el mismo placeholder, no crear otro por impaciencia. Generaciones de pago requieren autorización específica y dry run según contrato actual.
- Resultado externo incierto: releer estado real antes de reintentar. El helper no convierte varias mutaciones Palmier en una transacción ni en un único undo.
- Estado/documentos inválidos: corregir el dato concreto; no sustituir el calendario por uno vacío que oculte reservas.
- Etapa parcialmente hecha: registrar `--resultado parcial`, qué se aplicó y siguiente paso. Retomar por IDs, no repetir todo el flujo.
