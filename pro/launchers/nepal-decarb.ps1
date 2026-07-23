# nepal-decarb launcher (Day 11)
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = $here
while ($true) {
    if (Test-Path (Join-Path $root 'pro\src\nepal_decarb_pro\__init__.py')) { break }
    $parent = Split-Path -Parent $root
    if ($parent -eq $root) {
        Write-Host '[nepal-decarb] ERROR: could not find repo root from' $here -ForegroundColor Red
        exit 1
    }
    $root = $parent
}
$env:NEPAL_DECARB_ROOT = $root
$env:PYTHONPATH = "$root\pro\src;" +
                  "$root\tools\02-kiln-dynamics-simulator\src;" +
                  "$root\tools\03-cooler-grate-simulator\src;" +
                  $env:PYTHONPATH
& 'C:\Users\TG\AppData\Local\Programs\Python\Python312\python.exe' -m nepal_decarb_pro.cli @args
