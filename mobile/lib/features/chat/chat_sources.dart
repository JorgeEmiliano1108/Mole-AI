/// Visor de fuentes RAG de una respuesta del chat (issue 15).
library;

import 'package:flutter/material.dart';

import 'package:mole_ai/features/chat/chat.dart';

class ChatSourcesSheet extends StatelessWidget {
  const ChatSourcesSheet({super.key, required this.sources});

  final List<ChatSource> sources;

  static Future<void> show(
      BuildContext context, List<ChatSource> sources) {
    return showModalBottomSheet(
      context: context,
      builder: (_) => ChatSourcesSheet(sources: sources),
    );
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text('Fuentes consultadas',
                style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            if (sources.isEmpty)
              const Text(
                  'El asistente respondió sin recuperar documentos.'),
            Flexible(
              child: ListView.builder(
                shrinkWrap: true,
                itemCount: sources.length,
                itemBuilder: (context, i) {
                  final s = sources[i];
                  return ListTile(
                    leading: const Icon(Icons.description_outlined),
                    title: Text(s.autor ?? 'Fuente ${i + 1}'),
                    subtitle: s.url != null ? Text(s.url!) : null,
                    trailing: s.confianza != null
                        ? Text(
                            '${(s.confianza! * 100).toStringAsFixed(0)}%')
                        : null,
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}
