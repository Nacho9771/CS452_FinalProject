param([ValidateSet('build','test','run','signing','devices')][string]$Action = 'build')
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    if (-not $env:JAVA_HOME) {
        $portableRoot = Join-Path $PSScriptRoot '..\.local\jdk17'
        $portableJava = @(Get-ChildItem -LiteralPath $portableRoot -Directory -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName)
        $javaCandidates = $portableJava + @(
            "$env:ProgramFiles\Android\Android Studio\jbr",
            "$env:LOCALAPPDATA\Programs\Android Studio\jbr"
        )
        foreach ($candidate in $javaCandidates) {
            if (Test-Path "$candidate\bin\java.exe") { $env:JAVA_HOME = $candidate; break }
        }
    }
    if (-not $env:JAVA_HOME -or -not (Test-Path "$env:JAVA_HOME\bin\java.exe")) {
        throw 'Install Android Studio first, or set JAVA_HOME to a compatible JDK (17 recommended).'
    }
    $sdkPath = if ($env:ANDROID_HOME) { $env:ANDROID_HOME } else { "$env:LOCALAPPDATA\Android\Sdk" }
    if (-not (Test-Path $sdkPath)) { throw 'Finish the Android Studio SDK setup wizard first.' }
    if (-not (Test-Path 'local.properties')) {
        'sdk.dir=' + $sdkPath.Replace('\','/').Replace(':','\:') | Set-Content -LiteralPath 'local.properties'
    }
    switch ($Action) {
        'devices' { & "$sdkPath\platform-tools\adb.exe" devices }
        'signing' { & .\gradlew.bat :app:signingReport }
        'test' { & .\gradlew.bat :app:connectedDebugAndroidTest }
        'run' {
            & .\gradlew.bat :app:installDebug
            if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
            & "$sdkPath\platform-tools\adb.exe" shell am start -n com.mykitchen.app/.MainActivity
        }
        default { & .\gradlew.bat :app:assembleDebug :app:lintDebug }
    }
    exit $LASTEXITCODE
} finally { Pop-Location }
