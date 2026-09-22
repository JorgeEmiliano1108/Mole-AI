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

import 'package:mole_ai/core/notify.dart';
import 'package:mole_ai/core/offline_store.dart';
import 'package:mole_ai/features/auth/auth_controller.dart';
import 'package:mole_ai/features/home/home_dashboard.dart';
import 'package:mole_ai/features/plants/plants_screen.dart';
import 'package:mole_ai/features/vision/diagnosis_screen.dart';
import 'package:mole_ai/features/weather/weather_screen.dart';
import 'package:mole_ai/widgets/app_drawer.dart';

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
        onDestinationSelected: (i) => setState(() => _index = i),
        destinations: const [
          NavigationDestination(
              icon: Icon(Icons.home_outlined),
              selectedIcon: Icon(Icons.home),
              label: 'Inicio'),
          NavigationDestination(
              icon: Icon(Icons.spa_outlined),
              selectedIcon: Icon(Icons.spa),
              label: 'Plantas'),
          NavigationDestination(
              icon: Icon(Icons.wb_sunny_outlined),
              selectedIcon: Icon(Icons.wb_sunny),
              label: 'Clima'),
          NavigationDestination(
              icon: Icon(Icons.camera_alt_outlined),
              selectedIcon: Icon(Icons.camera_alt),
              label: 'Diagnóstico'),
        ],
      ),
    );
  }
}
