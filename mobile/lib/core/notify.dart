/// Notificaciones locales (decisión: sin FCM/APNs).
///
/// Dos eventos: diagnóstico listo y cola offline subida. Todo envuelto en
/// try/catch: sin inicialización o sin permiso, es no-op (la UI ya informa
/// con SnackBar/Texto; la notificación es redundancia amable, no crítica).
library;

import 'package:flutter_local_notifications/flutter_local_notifications.dart';

class NotifyService {
  NotifyService._();

  static final _plugin = FlutterLocalNotificationsPlugin();
  static bool _ready = false;

  /// Idempotente. Pide permiso POST_NOTIFICATIONS (Android 13+) perezosamente.
  static Future<void> init() async {
    if (_ready) return;
    try {
      const settings = InitializationSettings(
        android: AndroidInitializationSettings('@mipmap/ic_launcher'),
      );
      await _plugin.initialize(settings: settings);
      await _plugin
          .resolvePlatformSpecificImplementation<
              AndroidFlutterLocalNotificationsPlugin>()
          ?.requestNotificationsPermission();
      _ready = true;
    } catch (_) {}
  }

  static Future<void> show(String title, String body) async {
    try {
      if (!_ready) await init();
      if (!_ready) return;
      await _plugin.show(
        id: DateTime.now().microsecondsSinceEpoch ~/ 1000000,
        title: title,
        body: body,
        notificationDetails: const NotificationDetails(
          android: AndroidNotificationDetails(
            'mole_ai',
            'Mole.AI',
            importance: Importance.defaultImportance,
          ),
        ),
      );
    } catch (_) {}
  }

  /// Solo para tests: expone si el plugin respondió.
  static bool get isReady => _ready;
}
