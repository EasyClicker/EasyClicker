[Setup]
AppName=EasyClicker
AppVersion=1.0.3
AppPublisher=Easy click studio
AppPublisherURL=https://github.com/EasyClicker/EasyClicker
DefaultDirName={autopf}\EasyClicker
DefaultGroupName=EasyClicker
UninstallDisplayIcon={app}\EasyClicker.exe
UninstallDisplayName=EasyClicker
Compression=lzma2/ultra64
SolidCompression=yes
OutputDir=.\
OutputBaseFilename=EasyClicker_Setup_v1.0.3
SetupIconFile=icon.ico

VersionInfoCompany=Easy click studio
VersionInfoDescription=EasyClicker Installer
VersionInfoTextVersion=1.0.3
VersionInfoVersion=1.0.3
VersionInfoCopyright=Copyright (C) 2026 Easy click studio

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; Забираем один исполняемый файл из папки dist
Source: "dist\EasyClicker.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Ярлык программы в меню Пуск
Name: "{autoprograms}\EasyClicker"; Filename: "{app}\EasyClicker.exe"
; Ярлык на Рабочем столе
Name: "{autodesktop}\EasyClicker"; Filename: "{app}\EasyClicker.exe"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon
; Понятный ярлык для удаления программы в меню Пуск
Name: "{autoprograms}\Удалить EasyClicker"; Filename: "{uninstallexe}"; IconFilename: "{app}\icon.ico"

[Run]
Filename: "{app}\EasyClicker.exe"; Description: "{cm:LaunchProgram,EasyClicker}"; Flags: nowait postinstall skipifsilent
