package ai.mole.mole_ai

import android.os.Bundle
import android.view.WindowManager
import io.flutter.embedding.android.FlutterActivity

class MainActivity : FlutterActivity() {
    // S1 MASVS-STORAGE: toda la app maneja JWT, email y fotos de diagnóstico:
    // nada se muestra en el switcher de apps ni sale en screenshots.
    override fun onCreate(savedInstanceState: Bundle?) {
        window.addFlags(WindowManager.LayoutParams.FLAG_SECURE)
        super.onCreate(savedInstanceState)
    }
}
