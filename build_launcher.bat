@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Compilando WasperLauncher.cs para Wasper.exe...
C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe /nologo /target:winexe /out:Wasper.exe /r:System.Windows.Forms.dll WasperLauncher.cs
if %ERRORLEVEL% EQU 0 (
    echo [OK] Wasper.exe compilado com sucesso!
) else (
    echo [ERRO] Falha ao compilar Wasper.exe
)
