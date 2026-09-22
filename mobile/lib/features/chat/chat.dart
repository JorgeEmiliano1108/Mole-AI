/// Chat con contexto agronómico, vía gateway (contrato §6, fase 2).
///
/// `POST llm/chat/` sync (60/min) + `GET chat/history/`.
/// El disclaimer COFEPRIS se muestra siempre con cada respuesta.
library;

import 'package:mole_ai/core/api_client.dart';

class ChatSource {
  ChatSource({this.autor, this.url, this.confianza});

  factory ChatSource.fromJson(Map<String, dynamic> j) => ChatSource(
        autor: j['autor'] as String?,
        url: j['url'] as String?,
        confianza: (j['confianza'] as num?)?.toDouble(),
      );

  final String? autor;
  final String? url;
  final double? confianza;
}

class ChatAnswer {
  ChatAnswer(
      {required this.response,
      this.sources = const [],
      this.disclaimer});

  factory ChatAnswer.fromJson(Map<String, dynamic> j) => ChatAnswer(
        response: '${j['response'] ?? ''}',
        sources: ((j['sources'] as List?) ?? const [])
            .whereType<Map<String, dynamic>>()
            .map(ChatSource.fromJson)
            .toList(),
        disclaimer: j['disclaimer'] as String?,
      );

  final String response;
  final List<ChatSource> sources;
  final String? disclaimer;
}

class ChatTurn {
  ChatTurn({required this.prompt, required this.answer});
  final String prompt;
  final ChatAnswer answer;
}

class ChatRepository {
  ChatRepository(this._api);
  final ApiClient _api;

  /// Envía `{message}` (el gateway también acepta `question|prompt`).
  Future<ChatAnswer> send(String message) async {
    final body =
        await _api.postJson('llm/chat/', data: {'message': message});
    return ChatAnswer.fromJson(body);
  }

  Future<List<ChatTurn>> history() async {
    final body = await _api.getJson('chat/history/');
    return ((body['results'] as List?) ?? const [])
        .whereType<Map<String, dynamic>>()
        .map((j) => ChatTurn(
              prompt: '${j['prompt'] ?? ''}',
              answer: ChatAnswer(
                  response: '${j['response'] ?? ''}',
                  disclaimer: j['disclaimer'] as String?),
            ))
        .toList();
  }
}
