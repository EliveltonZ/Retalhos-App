; Instalador do Retalhos (Inno Setup 6).
; Gerado por ferramentas\gerar_instalador.bat, que compila os executáveis e passa a versão:
;   ISCC /DAppVersion=2.0.0 instalador\Retalhos.iss   ->  dist\instalador\Retalhos_Setup_2.0.0.exe
;
; - Instala por usuário em %LOCALAPPDATA%\Programs\Retalhos (sem pedir administrador), a mesma pasta
;   da versão anterior: o Update.exe consegue sobrescrever os arquivos e o Settings.json é gravável.
; - Mesmo AppId do instalador antigo: atualiza a instalação existente, sem entrada duplicada.
; - Settings.json da máquina nunca é sobrescrito nem removido; as planilhas (docs, sheet_proj) também não.

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#define AppName "Retalhos"
#define AppExe "Retalhos.exe"
#define Raiz ".."

[Setup]
AppId={{770C696B-5F13-474A-9A66-B477347B689C}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=GD
VersionInfoVersion={#AppVersion}
DefaultDirName={userpf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir={#Raiz}\dist\instalador
OutputBaseFilename=Retalhos_Setup_{#AppVersion}
SetupIconFile={#Raiz}\retalhos\resources\icon_retalho.ico
UninstallDisplayIcon={app}\{#AppExe}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
; avisa o Windows para recarregar os ícones: quem atualiza da versão antiga tem o ícone velho em cache
; para o mesmo caminho do Retalhos.exe
ChangesAssociations=yes

[Languages]
Name: "ptbr"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[InstallDelete]
; restos da versão anterior (build antigo do PyInstaller); planilhas em docs\ e sheet_proj\ ficam
Type: filesandordirs; Name: "{app}\_internal"
Type: filesandordirs; Name: "{app}\localpycs"
Type: filesandordirs; Name: "{app}\pictures"
Type: files; Name: "{app}\base_library.zip"
Type: files; Name: "{app}\*.toc"
Type: files; Name: "{app}\*.pkg"
Type: files; Name: "{app}\*.pyz"
Type: files; Name: "{app}\*.spec"
Type: files; Name: "{app}\warn-Retalhos.txt"
Type: files; Name: "{app}\xref-Retalhos.html"
Type: files; Name: "{app}\icon_retalho.ico"

[Files]
Source: "{#Raiz}\dist\Retalhos\*"; DestDir: "{app}"; Excludes: "Settings.json"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#Raiz}\dist\Update.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "Settings.padrao.json"; DestDir: "{app}"; DestName: "Settings.json"; Flags: onlyifdoesntexist uninsneveruninstall

[Dirs]
Name: "{app}\sheet_proj"; Flags: uninsneveruninstall

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{group}\Atualizar {#AppName}"; Filename: "{app}\Update.exe"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

[Code]
const
  DRIVER_ACCESS = 'SOFTWARE\ODBC\ODBCINST.INI\Microsoft Access Driver (*.mdb, *.accdb)';

var
  SettingsNovo: Boolean;

function InitializeSetup(): Boolean;
begin
  Result := True;
  if not RegKeyExists(HKLM64, DRIVER_ACCESS) then
    Result := MsgBox('O driver do Microsoft Access (64 bits) não foi encontrado neste computador.' + #13#10 +
      'Sem ele o Retalhos não consegue abrir o banco de dados.' + #13#10#13#10 +
      'Instale o "Microsoft Access Database Engine 2016 Redistributable" (x64).' + #13#10#13#10 +
      'Continuar a instalação mesmo assim?', mbConfirmation, MB_YESNO) = IDYES;
end;

{ texto para dentro de uma string JSON: barras escapadas e acentos como \uXXXX (arquivo segue em UTF-8) }
function JsonEscape(S: String): String;
var
  I: Integer;
begin
  Result := '';
  for I := 1 to Length(S) do
    if S[I] = '\' then
      Result := Result + '\\'
    else if S[I] = '"' then
      Result := Result + '\"'
    else if Ord(S[I]) > 127 then
      Result := Result + Format('\u%.4x', [Ord(S[I])])
    else
      Result := Result + S[I];
end;

{ troca o valor de "Chave": "..." (formato gravado pelo app); se a chave não existir, acrescenta no início }
procedure DefinirValor(var Texto: AnsiString; Chave, Valor: String);
var
  Marca: String;
  P, Fim: Integer;
begin
  Marca := '"' + Chave + '": "';
  P := Pos(Marca, Texto);
  if P = 0 then
  begin
    P := Pos('{', Texto);
    if P > 0 then
      Insert(#13#10 + '  "' + Chave + '": "' + JsonEscape(Valor) + '",', Texto, P + 1);
    Exit;
  end;
  P := P + Length(Marca);
  Fim := P;
  while Fim <= Length(Texto) do
    if Texto[Fim] = '\' then
      Fim := Fim + 2  { pula o caractere escapado (\\ ou \") }
    else if Texto[Fim] = '"' then
      Break
    else
      Fim := Fim + 1;
  Texto := Copy(Texto, 1, P - 1) + JsonEscape(Valor) + Copy(Texto, Fim, MaxInt);
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  Arquivo: String;
  Texto: AnsiString;
begin
  Arquivo := ExpandConstant('{app}\Settings.json');
  if CurStep = ssInstall then
    SettingsNovo := not FileExists(Arquivo)
  else if (CurStep = ssPostInstall) and LoadStringFromFile(Arquivo, Texto) then
  begin
    if SettingsNovo then
      DefinirValor(Texto, 'Sheet_proj', ExpandConstant('{app}\sheet_proj\'));
    { a versão instalada é desta data: o "Atualizar sistema" só oferece um Retalhos.zip mais novo que ela }
    DefinirValor(Texto, 'ultima_att', GetDateTimeString('dd/mm/yyyy hh:nn:ss', '/', ':'));
    SaveStringToFile(Arquivo, Texto, False);
  end;
end;
