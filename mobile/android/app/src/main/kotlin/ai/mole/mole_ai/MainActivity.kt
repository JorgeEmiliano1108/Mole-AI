package ai.mole.mole_ai

import android.content.Context
import android.os.BatteryManager
import android.os.Bundle
import android.view.WindowManager
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    // S1 MASVS-STORAGE: toda la app maneja JWT, email y fotos de diagnóstico:
    // nada se muestra en el switcher de apps ni sale en screenshots.
    override fun onCreate(savedInstanceState: Bundle?) {
        window.addFlags(WindowManager.LayoutParams.FLAG_SECURE)
        super.onCreate(savedInstanceState)
    }

    // Track C (harness batería): canal `mole.ai/battery` → `getBatteryPct`.
    // Solo lectura de nivel agregado 0-100; sin PII ni identificadores.
    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(
            flutterEngine.dartExecutor.binaryMessenger,
            "mole.ai/battery"
        ).setMethodCallHandler { call, result ->
            if (call.method == "getBatteryPct") {
                val bm = getSystemService(Context.BATTERY_SERVICE) as BatteryManager
                val pct = bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
                if (pct == Int.MIN_VALUE) {
                    result.error("UNAVAILABLE", "BatteryManager sin lectura", null)
                } else {
                    result.success(pct.toDouble())
                }
            } else {
                result.notImplemented()
            }
        }
    }
}
