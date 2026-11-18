; Instalador do Retalhos (Inno Setup 6).
; Gerado por ferramentas\gerar_instalador.bat, que compila os executáveis e passa a versão:
;   ISCC /DAppVersion=2.1.0 instalador\Retalhos.iss   ->  dist\instalador\Retalhos_Setup_2.1.0.exe
;
; - Instala por usuário em %LOCALAPPDATA%\Programs\Retalhos (sem pedir administrador), a mesma pasta
;   da versão anterior: o próprio app consegue rodar o instalador novo e o Settings.json é gravável.
; - Atualização pelo app (Ajuda › Procurar atualizações): roda este instalador com
;   /SILENT /CLOSEAPPLICATIONS /REABRIR, que fecha o Retalhos aberto e o abre de novo no fim.
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
; atualizador antigo (Retalhos.zip): substituído pela atualização dentro do app
Type: files; Name: "{app}\Update.exe"
Type: files; Name: "{group}\Atualizar {#AppName}.lnk"

[Files]
Source: "{#Raiz}\dist\Retalhos\*"; DestDir: "{app}"; Excludes: "Settings.json"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "Settings.padrao.json"; DestDir: "{app}"; DestName: "Settings.json"; Flags: onlyifdoesntexist uninsneveruninstall

[Dirs]
Name: "{app}\sheet_proj"; Flags: uninsneveruninstall

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
; atualização feita pelo app: abre o Retalhos de novo sem perguntar
Filename: "{app}\{#AppExe}"; Flags: nowait; Check: Reabrir

[Code]
function Reabrir: Boolean;
var
  I: Integer;
begin
  Result := False;
  for I := 1 to ParamCount do
    if CompareText(ParamStr(I), '/REABRIR') = 0 then
      Result := True;
end;

{ há algum Retalhos.exe rodando? (WMI; na dúvida responde que não) }
function RetalhosAberto: Boolean;
var
  Locator, Servico, Lista: Variant;
begin
  Result := False;
  try
    Locator := CreateOleObject('WbemScripting.SWbemLocator');
    Servico := Locator.ConnectServer('.', 'root\CIMV2');
    Lista := Servico.ExecQuery('SELECT ProcessId FROM Win32_Process WHERE Name = ''Retalhos.exe''');
    Result := Lista.Count > 0;
  except
    Result := False;
  end;
end;

{ Atualização pelo app (/REABRIR): o Windows não consegue fechar o Retalhos sozinho e, em modo silencioso,
  o instalador desistiria. O app se fecha logo depois de abrir o instalador: espera até 15 s e, se ainda
  estiver aberto, encerra o Retalhos deste usuário. }
function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  I, Codigo: Integer;
begin
  Result := '';
  if not Reabrir then
    Exit;
  I := 0;
  while RetalhosAberto and (I < 30) do
  begin
    Sleep(500);
    I := I + 1;
  end;
  if RetalhosAberto then
  begin
    Exec(ExpandConstant('{sys}\taskkill.exe'),
      '/F /IM Retalhos.exe /FI "USERNAME eq ' + GetUserNameString + '"', '', SW_HIDE, ewWaitUntilTerminated, Codigo);
    Sleep(1000);
  end;
end;

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
    { data da instalação (informativa) }
    DefinirValor(Texto, 'ultima_att', GetDateTimeString('dd/mm/yyyy hh:nn:ss', '/', ':'));
    SaveStringToFile(Arquivo, Texto, False);
  end;
end;
