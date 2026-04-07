; installer.iss
; Установщик для программы "Реестр подключенных услуг"

[Setup]
AppName=Реестр подключенных услуг
AppVersion=2026.1.0
AppPublisher=ПАО "Ростелеком"
DefaultDirName={autopf}\Ростелеком\Реестр подключенных услуг
DefaultGroupName=Ростелеком
OutputDir=installer
OutputBaseFilename=SubscribersRegistry_Setup
SetupIconFile=assets\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
UninstallDisplayIcon={app}\SubscribersRegistry.exe

[Languages]
Name: "russian"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Создать ярлык на рабочем столе"; GroupDescription: "Дополнительные задачи:"
Name: "quicklaunchicon"; Description: "Создать ярлык в панели быстрого запуска"; GroupDescription: "Дополнительные задачи:"

[Files]
Source: "dist\SubscribersRegistry.exe"; DestDir: "{app}"
Source: "dist\assets\*"; DestDir: "{app}\assets"; Flags: recursesubdirs
Source: "dist\config.json"; DestDir: "{app}"; Flags: onlyifdoesntexist
Source: "dist\README.txt"; DestDir: "{app}"
Source: "dist\LICENSE.txt"; DestDir: "{app}"

[Icons]
Name: "{group}\Реестр подключенных услуг"; Filename: "{app}\SubscribersRegistry.exe"; IconFilename: "{app}\assets\icon.ico"
Name: "{group}\Инициализация базы данных"; Filename: "{app}\init_db.exe"; IconFilename: "{app}\assets\icon.ico"
Name: "{group}\Руководство пользователя (Админ)"; Filename: "{app}\assets\user_manual_admin.pdf"; IconFilename: "{app}\assets\icon.ico"
Name: "{group}\Руководство пользователя (Гость)"; Filename: "{app}\assets\user_manual_guest.pdf"; IconFilename: "{app}\assets\icon.ico"
Name: "{group}\{cm:UninstallProgram}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Реестр подключенных услуг"; Filename: "{app}\SubscribersRegistry.exe"; IconFilename: "{app}\assets\icon.ico"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\Реестр подключенных услуг"; Filename: "{app}\SubscribersRegistry.exe"; IconFilename: "{app}\assets\icon.ico"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\SubscribersRegistry.exe"; Description: "Запустить программу"; Flags: postinstall nowait skipifsilent unchecked

[UninstallDelete]
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\backups"