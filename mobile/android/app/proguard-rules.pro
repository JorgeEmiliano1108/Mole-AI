# S1 MASVS-CODE: reglas mínimas (Flutter ya conserva lo necesario vía
# getDefaultProguardFile + flutter-gradle-plugin; aquí solo librerías con
# reflexión). Sin reglas: R8 podría romper plugins con JNI.
-keep class io.flutter.app.** { *; }
-keep class io.flutter.plugin.** { *; }
-keep class io.flutter.util.** { *; }
-keep class io.flutter.view.** { *; }
-keep class io.flutter.** { *; }
-keep class com.dexterous.** { *; }
