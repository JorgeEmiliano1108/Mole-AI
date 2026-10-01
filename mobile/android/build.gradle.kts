allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

val newBuildDir: Directory =
    rootProject.layout.buildDirectory
        .dir("../../build")
        .get()
rootProject.layout.buildDirectory.value(newBuildDir)

subprojects {
    val newSubprojectBuildDir: Directory = newBuildDir.dir(project.name)
    project.layout.buildDirectory.value(newSubprojectBuildDir)
}
subprojects {
    project.evaluationDependsOn(":app")
}

// Tolerancia a plugins con target JVM distinto (tflite_flutter Java 11 vs app 17);
// el fix definitivo es alinear todos los subproyectos, pero para el APK debug de
// prueba se reduce a warning vía kotlin.jvm.target.validation.mode en gradle.properties.

tasks.register<Delete>("clean") {
    delete(rootProject.layout.buildDirectory)
}
