"""Login, senhas e administração de usuários (tblUsuarios)."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402

from retalhos.models import Usuario  # noqa: E402
from retalhos.services import EstoqueService, RegraDeNegocioError, UsuarioService  # noqa: E402
from retalhos.services.usuarios import conferir_senha, gerar_hash  # noqa: E402


def _svc(settings):
    svc = UsuarioService(settings)
    assert svc.preparar_tabela() is True  # cria na primeira vez
    assert svc.preparar_tabela() is False  # e não recria
    return svc


def test_hash_de_senha():
    h1, h2 = gerar_hash("abc123"), gerar_hash("abc123")
    assert h1 != h2  # salt aleatório
    assert "abc123" not in h1
    assert conferir_senha("abc123", h1) and conferir_senha("abc123", h2)
    assert not conferir_senha("abc124", h1)
    assert not conferir_senha("abc123", "lixo") and not conferir_senha("abc123", None)


def test_primeiro_admin_e_login(settings):
    svc = _svc(settings)
    assert not svc.existe_usuario()
    admin = svc.criar_primeiro_admin("elivelton", "Elivelton", "1234")
    assert (admin.login, admin.nome, admin.admin, admin.pcp) == ("ELIVELTON", "ELIVELTON", True, True)
    with pytest.raises(RegraDeNegocioError):
        svc.criar_primeiro_admin("outro", "Outro", "1234")  # só com a tabela vazia

    u = svc.autenticar(" Elivelton ", "1234")  # login sem diferenciar maiúsculas/espaços
    assert u.id == admin.id and u.ultimo_acesso is not None
    for login, senha in (("ELIVELTON", "errada"), ("NAOEXISTE", "1234")):
        with pytest.raises(RegraDeNegocioError, match="Usuário ou senha inválidos"):
            svc.autenticar(login, senha)


def test_usuario_novo_troca_senha_no_primeiro_acesso(settings):
    svc = _svc(settings)
    admin = svc.criar_primeiro_admin("ADM", "ADM", "1234")
    novo = svc.criar(admin, Usuario(0, "joao", "João", pcp=True), "temp")
    assert novo.trocar_senha and novo.pcp and not novo.admin

    u = svc.autenticar("JOAO", "temp")
    assert u.trocar_senha
    svc.trocar_senha(u, None, "minha1")  # troca obrigatória: não pede a atual
    assert not svc.autenticar("JOAO", "minha1").trocar_senha
    with pytest.raises(RegraDeNegocioError):
        svc.autenticar("JOAO", "temp")

    u = svc.autenticar("JOAO", "minha1")
    with pytest.raises(RegraDeNegocioError, match="Informe a senha atual"):
        svc.trocar_senha(u, None, "outra1")  # fora da troca obrigatória exige a atual
    with pytest.raises(RegraDeNegocioError, match="incorreta"):
        svc.trocar_senha(u, "errada", "outra1")
    with pytest.raises(RegraDeNegocioError, match="pelo menos"):
        svc.trocar_senha(u, "minha1", "12")
    svc.trocar_senha(u, "minha1", "outra1")
    assert svc.autenticar("JOAO", "outra1")


def test_regras_de_administracao(settings):
    svc = _svc(settings)
    admin = svc.criar_primeiro_admin("ADM", "ADM", "1234")
    joao = svc.criar(admin, Usuario(0, "JOAO", "JOAO"), "temp")
    with pytest.raises(RegraDeNegocioError, match="Já existe"):
        svc.criar(admin, Usuario(0, "joao", "x"), "temp")
    with pytest.raises(RegraDeNegocioError, match="administradores"):
        svc.criar(joao, Usuario(0, "MARIA", "MARIA"), "temp")  # não-admin não cadastra
    with pytest.raises(RegraDeNegocioError):
        svc.listar(joao)

    with pytest.raises(RegraDeNegocioError, match="próprio"):
        svc.atualizar(admin, Usuario(admin.id, "ADM", "ADM", admin=False))  # não se rebaixa
    svc.atualizar(admin, Usuario(joao.id, "JOAO", "João Silva", admin=True, ativo=True))
    assert {u.login: u.nome for u in svc.listar(admin)} == {"ADM": "ADM", "JOAO": "JOÃO SILVA"}

    joao_admin = svc.autenticar("JOAO", "temp")
    svc.atualizar(joao_admin, Usuario(admin.id, "ADM", "ADM", admin=False, ativo=False))  # ainda resta 1 admin
    with pytest.raises(RegraDeNegocioError, match="desativado"):
        svc.autenticar("ADM", "1234")

    svc.redefinir_senha(joao_admin, Usuario(admin.id, "ADM", "ADM"), "nova9")
    svc.atualizar(joao_admin, Usuario(admin.id, "ADM", "ADM", admin=True, ativo=True))
    assert svc.autenticar("ADM", "nova9").trocar_senha


def test_admin_rebaixado_com_sessao_aberta_perde_acesso(settings):
    svc = _svc(settings)
    a = svc.criar_primeiro_admin("A", "A", "1234")  # sessão de A continua aberta com admin=True
    b_id = svc.criar(a, Usuario(0, "B", "B", admin=True), "temp").id
    b = svc.autenticar("B", "temp")
    svc.atualizar(b, Usuario(a.id, "A", "A", admin=False, ativo=True))  # B rebaixa A
    assert a.admin  # o objeto da sessão de A ainda diz admin...
    with pytest.raises(RegraDeNegocioError, match="Somente administradores"):
        svc.atualizar(a, Usuario(b_id, "B", "B", admin=False, ativo=True))  # ...mas o banco é conferido
    with pytest.raises(RegraDeNegocioError, match="Somente administradores"):
        svc.criar(a, Usuario(0, "C", "C"), "temp")


def test_sempre_sobra_um_administrador(settings):
    svc = _svc(settings)
    a = svc.criar_primeiro_admin("A", "A", "1234")
    b = svc.criar(a, Usuario(0, "B", "B", admin=True), "temp")
    svc.atualizar(a, Usuario(b.id, "B", "B", admin=False, ativo=True))  # ok: A continua admin
    assert [u.login for u in svc.listar(a) if u.admin] == ["A"]
    with pytest.raises(RegraDeNegocioError):
        svc.atualizar(a, Usuario(a.id, "A", "A", admin=False, ativo=True))  # A é o último: não sai


def test_responsavel_e_permissoes_vem_do_usuario(settings):
    svc = EstoqueService(settings)
    settings.usuario = Usuario(7, "MARIA", "MARIA SOUZA", remover_reserva=True)
    rid = svc.lancar_retalho(10, 1000, 500)
    assert next(r for r in svc.listar_retalhos() if r.id == rid).responsavel == "MARIA SOUZA"
    assert settings.allow_remove_reserve and not settings.allow_manual_reserve and not settings.is_admin
    with pytest.raises(RegraDeNegocioError, match="administradores"):
        svc.recriar_arquivos()


def test_tela_de_login(settings):
    from retalhos.app import create_app
    from retalhos.ui.dialogs import LoginDialog, PrimeiroAdminDialog

    create_app()
    svc = _svc(settings)
    primeiro = PrimeiroAdminDialog(svc)
    primeiro.txt_login.setText("adm")
    primeiro.txt_nome.setText("Administrador")
    primeiro.txt_senha.setText("1234")
    primeiro.txt_conf.setText("9999")
    primeiro._ok()
    assert "não conferem" in primeiro.lb_erro.text() and not svc.existe_usuario()
    primeiro.txt_conf.setText("1234")
    primeiro._ok()
    assert primeiro.usuario is not None and svc.existe_usuario()

    login = LoginDialog(svc, settings)
    login.txt_login.setText("ADM")
    login.txt_senha.setText("errada")
    login._entrar()
    assert login.usuario is None and "inválidos" in login.lb_erro.text() and login.txt_senha.text() == ""
    login.txt_senha.setText("1234")
    login._entrar()
    assert login.usuario.login == "ADM" and settings.last_login == "ADM"
