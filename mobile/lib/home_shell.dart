/// Shell autenticado (issue 15): drawer lateral + barra de 4 destinos.
///
/// Primarios frecuentes en `NavigationBar`; resto (Especies/Chat/Mapa/
/// Reportes/Historial) + sección admin en `AppDrawer` (hamburger).
/// Conserva el drain de cola al recuperar red.
library;

import 'dart:async';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:mole_ai/core/notify.dart';
import 'package:mole_ai/core/offline_store.dart';
import 'package:mole_ai/features/alerts/alerts.dart';
import 'package:mole_ai/features/auth/auth_controller.dart';
import 'package:mole_ai/features/home/home_dashboard.dart';
import 'package:mole_ai/features/plants/plants_screen.dart';
import 'package:mole_ai/features/vision/diagnosis_screen.dart';
import 'package:mole_ai/features/weather/weather_screen.dart';
import 'package:mole_ai/widgets/app_drawer.dart';

/// Destino Avisos con badge de no-leídos (N-1).
///
/// Función pura para testear sin bombear el shell (connectivity usa
/// platform channels). `unread > 0` → [Badge] con conteo; si no, icono plano.
NavigationDestination alertsDestination(int unread) => NavigationDestination(
      icon: unread > 0
          ? Badge.count(
              count: unread,
              child: const Icon(Icons.notifications_outlined),
            )
          : const Icon(Icons.notifications_outlined),
      selectedIcon: const Icon(Icons.notifications),
      label: 'Avisos',
    );

class HomeShell extends ConsumerStatefulWidget {
  const HomeShell({super.key});

  @override
  ConsumerState<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends ConsumerState<HomeShell> {
  int _index = 0;
  StreamSubscription<List<ConnectivityResult>>? _connSub;

  static const _titles = ['Inicio', 'Mis plantas', 'Clima', 'Diagnóstico'];

  static const _tabs = [
    HomeDashboardScreen(),
    PlantsScreen(),
    WeatherScreen(),
    DiagnosisScreen(),
  ];

  @override
  void initState() {
    super.initState();
    // F2: restaura no-leídos persistidos para el badge de Avisos.
    Future.microtask(
        () => ref.read(unreadAlertsProvider.notifier).hydrate());
    // Al recuperar red: vaciar la cola de diagnósticos en segundo plano.
    _connSub = Connectivity().onConnectivityChanged.listen((results) async {
      if (results.contains(ConnectivityResult.none)) return;
      try {
        final store = await ref.read(offlineStoreProvider.future);
        if ((await store.pending()).isEmpty) return;
        final n = await ref
            .read(visionRepositoryProvider)
            .drainQueue(store);
        if (n > 0 && mounted) {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(
              content: Text('Conexión recuperada: $n foto(s) subida(s).')));
          await NotifyService.show('Cola al día',
              '$n foto(s) pendiente(s) subida(s) al servidor.');
        }
      } catch (_) {}
    });
  }

  @override
  void dispose() {
    _connSub?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    // F2: badge de Avisos vive en NavigationBar (N-1), no solo en drawer.
    final unread = ref.watch(unreadAlertsProvider);
    return Scaffold(
      appBar: AppBar(
        title: Text(_titles[_index]),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Cerrar sesión',
            onPressed: () =>
                ref.read(authControllerProvider.notifier).logout(),
          ),
        ],
      ),
      drawer: const AppDrawer(),
      body: IndexedStack(index: _index, children: _tabs),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (i) {
          // Avisos es ruta propia (/avisos); no altera el tab activo.
          if (i == _tabs.length) {
            context.go('/avisos');
            return;
          }
          setState(() => _index = i);
        },
        destinations: [
          const NavigationDestination(
              icon: Icon(Icons.home_outlined),
              selectedIcon: Icon(Icons.home),
              label: 'Inicio'),
          const NavigationDestination(
              icon: Icon(Icons.spa_outlined),
              selectedIcon: Icon(Icons.spa),
              label: 'Plantas'),
          const NavigationDestination(
              icon: Icon(Icons.wb_sunny_outlined),
              selectedIcon: Icon(Icons.wb_sunny),
              label: 'Clima'),
          const NavigationDestination(
              icon: Icon(Icons.camera_alt_outlined),
              selectedIcon: Icon(Icons.camera_alt),
              label: 'Diagnóstico'),
          alertsDestination(unread),
        ],
      ),
    );
  }
}
