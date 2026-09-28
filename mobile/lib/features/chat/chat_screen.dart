/// Pantalla de chat agronómico (contrato §6).
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mole_ai/core/errors.dart';
import 'package:mole_ai/core/safety_block_banner.dart';
import 'package:mole_ai/features/auth/auth_controller.dart';
import 'package:mole_ai/features/chat/chat.dart';
import 'package:mole_ai/features/chat/chat_sources.dart';

final chatRepositoryProvider = Provider<ChatRepository>(
    (ref) => ChatRepository(ref.watch(apiClientProvider)));

String _friendly(Object e) => e is ApiException
    ? e.message
    : 'Error inesperado. Intenta de nuevo.';

class ChatScreen extends ConsumerStatefulWidget {
  const ChatScreen({super.key});

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  final _input = TextEditingController();
  final _turns = <ChatTurn>[];
  bool _loading = false;
  bool _sending = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    Future.microtask(_loadHistory);
  }

  @override
  void dispose() {
    _input.dispose();
    super.dispose();
  }

  Future<void> _loadHistory() async {
    setState(() => _loading = true);
    try {
      final h = await ref.read(chatRepositoryProvider).history();
      if (mounted) {
        setState(() {
          _turns.addAll(h);
          _loading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = _friendly(e);
          _loading = false;
        });
      }
    }
  }

  Future<void> _send() async {
    final msg = _input.text.trim();
    if (msg.isEmpty || _sending) return;
    setState(() {
      _sending = true;
      _error = null;
    });
    _input.clear();
    try {
      final answer = await ref.read(chatRepositoryProvider).send(msg);
      if (mounted) {
        setState(() {
          _turns.add(ChatTurn(prompt: msg, answer: answer));
          _sending = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = _friendly(e);
          _sending = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          children: [
            Expanded(
              child: _loading
                  ? const Center(child: CircularProgressIndicator())
                  : _turns.isEmpty
                      ? const Center(
                          child: Text(
                              'Pregunta sobre tus plantas.\nEl asistente usa tus sensores como contexto.',
                              textAlign: TextAlign.center))
                      : ListView.builder(
                          itemCount: _turns.length,
                          itemBuilder: (context, i) {
                            final t = _turns[i];
                            return Column(
                              crossAxisAlignment:
                                  CrossAxisAlignment.stretch,
                              children: [
                                Align(
                                  alignment: Alignment.centerRight,
                                  child: Card(
                                    color: Theme.of(context)
                                        .colorScheme
                                        .primaryContainer,
                                    child: Padding(
                                      padding: const EdgeInsets.all(10),
                                      child: Text(t.prompt),
                                    ),
                                  ),
                                ),
                                Card(
                                  child: Padding(
                                    padding: const EdgeInsets.all(10),
                                    child: Column(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.start,
                                      children: [
                                        if (t.answer.isSafetyBlocked)
                                          SafetyBlockBanner(
                                            reason: t.answer.safetyReason ??
                                                'Contenido bloqueado por seguridad.',
                                            code: t.answer.safetyCode,
                                          )
                                        else ...[
                                          Text(t.answer.response),
                                          if (t.answer.sources.isNotEmpty)
                                            TextButton.icon(
                                              onPressed: () =>
                                                  ChatSourcesSheet.show(context,
                                                      t.answer.sources),
                                              icon: const Icon(
                                                  Icons.library_books_outlined,
                                                  size: 18),
                                              label: Text(
                                                  'Fuentes (${t.answer.sources.length})'),
                                            ),
                                          if (t.answer.disclaimer != null) ...[
                                            const SizedBox(height: 6),
                                            Text(t.answer.disclaimer!,
                                                style: Theme.of(context)
                                                    .textTheme
                                                    .bodySmall),
                                          ],
                                        ],
                                      ],
                                    ),
                                  ),
                                ),
                                const SizedBox(height: 6),
                              ],
                            );
                          },
                        ),
            ),
            if (_error != null) ...[
              Semantics(
                liveRegion: true,
                child: Text(_error!,
                    style: TextStyle(
                        color: Theme.of(context).colorScheme.error)),
              ),
              const SizedBox(height: 4),
            ],
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _input,
                    decoration: const InputDecoration(
                        labelText: 'Escribe tu pregunta'),
                    textInputAction: TextInputAction.send,
                    minLines: 1,
                    maxLines: 4,
                    enabled: !_sending,
                    onSubmitted: (_) => _send(),
                  ),
                ),
                const SizedBox(width: 8),
                FilledButton(
                  style: FilledButton.styleFrom(
                      minimumSize: const Size(56, 48)),
                  onPressed: _sending ? null : _send,
                  child: _sending
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child:
                              CircularProgressIndicator(strokeWidth: 2))
                      : const Icon(Icons.send),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
