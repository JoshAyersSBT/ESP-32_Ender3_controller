param(
    [string]$Port = "auto",
    [string]$UploadPort = "",
    [string]$SourceDir = (Get-Location).Path,
    [string]$Firmware = "",
    [switch]$FlashOnly,
    [switch]$SkipFlash,
    [switch]$Reset,
    [switch]$Verbose
)

$RequiredFiles = @(
    "boot.py",
    "main.py",
    "config.py",
    "wifi.py",
    "state.py",
    "printer.py",
    "print_job.py",
    "storage.py",
    "webserver.py",
    "www/index.html",
    "www/app.js",
    "www/style.css"
)

function Log($msg) {
    Write-Host "[install] $msg"
}

function Fail($msg) {
    Write-Host "[error] $msg" -ForegroundColor Red
    exit 1
}

function RunCmd($cmd) {
    if ($Verbose) {
        Write-Host "+ $cmd"
    }
    Invoke-Expression $cmd
}

function Get-UsePort {
    if ($UploadPort -ne "") {
        return $UploadPort
    }
    return $Port
}

function MP($args) {
    $usePort = Get-UsePort

    if ($usePort -eq "auto") {
        RunCmd "mpremote $args"
    } else {
        RunCmd "mpremote connect $usePort $args"
    }
}

function CheckDependencies {
    if (-not (Get-Command mpremote -ErrorAction SilentlyContinue)) {
        Fail "mpremote not found"
    }

    if (-not $SkipFlash) {
        if (-not (Get-Command esptool -ErrorAction SilentlyContinue)) {
            Fail "esptool not found"
        }
    }
}

function CheckSourceTree {
    if ($FlashOnly) { return }

    foreach ($file in $RequiredFiles) {
        if (-not (Test-Path "$SourceDir\$file")) {
            Fail "Missing file: $file"
        }
    }
}

function ResolveFirmware {
    if ($SkipFlash) { return }

    if ($Firmware -ne "") {
        if (-not (Test-Path $Firmware)) {
            if (Test-Path "$SourceDir\$Firmware") {
                $Firmware = "$SourceDir\$Firmware"
            } else {
                Fail "Firmware not found: $Firmware"
            }
        }
        return
    }

    $bins = Get-ChildItem -Path $SourceDir -Filter *.bin

    if ($bins.Count -eq 1) {
        $Firmware = $bins[0].FullName
        Log "Auto-detected firmware: $Firmware"
    }
}

function FlashFirmware {
    if ($SkipFlash) {
        Log "Skipping flash"
        return
    }

    if ($Firmware -eq "") {
        Log "No firmware provided, skipping flash"
        return
    }

    if ($Port -eq "auto") {
        Fail "Flashing requires --port"
    }

    Log "Flashing firmware: $Firmware"

    RunCmd "esptool --chip esp32 --port $Port erase-flash"
    RunCmd "esptool --chip esp32 --port $Port --baud 460800 write-flash -z 0x1000 `"$Firmware`""

    Log "Waiting for reboot..."
    Start-Sleep -Seconds 4
}

function CheckConnection {
    if ($FlashOnly) { return }

    $usePort = Get-UsePort
    Log "Checking connection on $usePort"

    for ($i = 0; $i -lt 5; $i++) {
        try {
            MP "fs ls" | Out-Null
            Log "Connection OK"
            return
        } catch {
            Start-Sleep -Seconds 2
        }
    }

    Fail "Could not connect to ESP32"
}

function MakeDirs {
    if ($FlashOnly) { return }

    MP "fs mkdir :/www"
    MP "fs mkdir :/uploads"
}

function UploadFile($src, $dst) {
    Log "Uploading $src"
    MP "fs cp `"$src`" $dst"
}

function UploadAll {
    if ($FlashOnly) { return }

    UploadFile "$SourceDir\boot.py" ":/boot.py"
    UploadFile "$SourceDir\main.py" ":/main.py"
    UploadFile "$SourceDir\config.py" ":/config.py"
    UploadFile "$SourceDir\wifi.py" ":/wifi.py"
    UploadFile "$SourceDir\state.py" ":/state.py"
    UploadFile "$SourceDir\printer.py" ":/printer.py"
    UploadFile "$SourceDir\print_job.py" ":/print_job.py"
    UploadFile "$SourceDir\storage.py" ":/storage.py"
    UploadFile "$SourceDir\webserver.py" ":/webserver.py"

    UploadFile "$SourceDir\www\index.html" ":/www/index.html"
    UploadFile "$SourceDir\www\app.js" ":/www/app.js"
    UploadFile "$SourceDir\www\style.css" ":/www/style.css"
}

function MaybeReset {
    if ($Reset -and -not $FlashOnly) {
        Log "Resetting device"
        MP "reset"
    }
}

# ===== MAIN =====

CheckDependencies
CheckSourceTree
ResolveFirmware
FlashFirmware

if ($FlashOnly) {
    Log "Flash-only complete"
    exit
}

CheckConnection
MakeDirs
UploadAll
MaybeReset

Log "Install complete"