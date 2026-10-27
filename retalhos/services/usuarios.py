"""Login e cadastro de usuários (``tblUsuarios``).

A senha nunca é gravada: guarda-se ``pbkdf2_sha256$<iterações>$<salt>$<hash>`` (PBKDF2-HMAC-SHA256
com salt aleatório por usuário). As permissões ficam no usuário e valem em qualquer computador.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import replace
from datetime import datetime

from ..config import Settings
from ..db import Database, UsuarioRepository
from ..models import Usuario
from .estoque import RegraDeNegocioError

ITERACOES = 200_000
SENHA_MINIMA = 4
_ALGORITMO = "pbkdf2_sha256"


# ================================================================== senhas
def gerar_hash(senha: str, iteracoes: int = ITERACOES) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), bytes.fromhex(salt), iteracoes).hex()
    return f"{_ALGORITMO}${iteracoes}${salt}${digest}"


def conferir_senha(senha: str, armazenado: str | None) -> bool:
    try:
        algoritmo, iteracoes, salt, digest = (armazenado or "").split("$")
        if algoritmo != _ALGORITMO:
            return False
        calculado = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), bytes.fromhex(salt), int(iteracoes)).hex()
    except ValueError:
        return False
    return hmac.compare_digest(calculado, digest)  # comparação em tempo constante


def normalizar_login(login: str) -> str:
    return login.strip().upper()


def _validar_senha(senha: str) -> None:
    if len(senha) < SENHA_MINIMA:
        raise RegraDeNegocioError(f"A senha deve ter pelo menos {SENHA_MINIMA} caracteres.")


# ================================================================= serviço
class UsuarioService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.db = Database(settings.database_path, settings.database_password)

    def _agora(self) -> datetime:
        return datetime.now().replace(microsecond=0)

    # ----------------------------------------------------------- preparação
    def preparar_tabela(self) -> bool:
        """Cria ``tblUsuarios`` se ainda não existir (sessão própria). Retorna ``True`` se criou."""
        with self.db.session() as s:
            return UsuarioRepository(s).garantir_tabela()

    def existe_usuario(self) -> bool:
        with self.db.session() as s:
            return UsuarioRepository(s).contar() > 0

    def criar_primeiro_admin(self, login: str, nome: str, senha: str) -> Usuario:
        """Só funciona com a tabela vazia: cria o administrador inicial."""
        with self.db.session() as s:
            if UsuarioRepository(s).contar() > 0:
                raise RegraDeNegocioError("Já existe usuário cadastrado. Peça acesso a um administrador.")
        novo = Usuario(0, login, nome, admin=True, pcp=True, remover_reserva=True, reservar_manual=True)
        return self._inserir(novo, senha)

    # --------------------------------------------------------------- login
    def autenticar(self, login: str, senha: str) -> Usuario:
        login = normalizar_login(login)
        with self.db.session() as s:
            repo = UsuarioRepository(s)
            usuario = repo.buscar(login)
            # mesma mensagem para usuário inexistente e senha errada (não revela quais logins existem)
            if usuario is None or not conferir_senha(senha, repo.hash_da_senha(login)):
                raise RegraDeNegocioError("Usuário ou senha inválidos.")
            if not usuario.ativo:
                raise RegraDeNegocioError("Usuário desativado. Fale com um administrador.")
            usuario.ultimo_acesso = self._agora()
            repo.registrar_acesso(usuario.id, usuario.ultimo_acesso)
        return usuario

    def trocar_senha(self, usuario: Usuario, atual: str | None, nova: str) -> None:
        """Troca a própria senha. ``atual=None`` só quando o login exigiu a troca (senha temporária)."""
        _validar_senha(nova)
        with self.db.session() as s:
            repo = UsuarioRepository(s)
            if atual is not None and not conferir_senha(atual, repo.hash_da_senha(usuario.login)):
                raise RegraDeNegocioError("Senha atual incorreta.")
            if atual is None and not usuario.trocar_senha:
                raise RegraDeNegocioError("Informe a senha atual.")
            repo.definir_senha(usuario.id, gerar_hash(nova), trocar_senha=False)
        usuario.trocar_senha = False

    # ------------------------------------------------------- administração
    def _exigir_admin(self, admin: Usuario | None) -> None:
        """Confere no banco (não só na sessão): o usuário pode ter sido rebaixado/desativado por outro admin."""
        if admin is not None and admin.admin:
            with self.db.session() as s:
                atual = UsuarioRepository(s).buscar(admin.login)
            if atual is not None and atual.admin and atual.ativo:
                return
        raise RegraDeNegocioError("Somente administradores podem gerenciar usuários.")

    def listar(self, admin: Usuario) -> list[Usuario]:
        self._exigir_admin(admin)
        with self.db.session() as s:
            return UsuarioRepository(s).listar()

    def _inserir(self, usuario: Usuario, senha: str) -> Usuario:
        login = normalizar_login(usuario.login)
        if not login:
            raise RegraDeNegocioError("Informe o login.")
        if len(login) > 30:
            raise RegraDeNegocioError("O login deve ter no máximo 30 caracteres.")
        _validar_senha(senha)
        novo = replace(usuario, login=login, nome=usuario.nome.strip().upper()[:60])
        with self.db.session() as s:
            repo = UsuarioRepository(s)
            if repo.buscar(login) is not None:
                raise RegraDeNegocioError(f"Já existe o usuário {login}.")
            novo.id = repo.inserir(novo, gerar_hash(senha), self._agora())
        return novo

    def criar(self, admin: Usuario, usuario: Usuario, senha_temporaria: str) -> Usuario:
        """Novo usuário; ele troca a senha no primeiro acesso."""
        self._exigir_admin(admin)
        return self._inserir(replace(usuario, trocar_senha=True), senha_temporaria)

    def atualizar(self, admin: Usuario, usuario: Usuario) -> None:
        """Altera nome, permissões e se está ativo (o login não muda)."""
        self._exigir_admin(admin)
        if usuario.id == admin.id and (not usuario.admin or not usuario.ativo):
            raise RegraDeNegocioError("Você não pode tirar o seu próprio acesso de administrador nem se desativar.")
        with self.db.session() as s:
            repo = UsuarioRepository(s)
            atual = next((u for u in repo.listar() if u.id == usuario.id), None)
            if atual is None:
                raise RegraDeNegocioError("Usuário não encontrado.")
            perde_admin = atual.admin and atual.ativo and not (usuario.admin and usuario.ativo)
            if perde_admin and repo.contar_admins_ativos() <= 1:
                raise RegraDeNegocioError("O sistema precisa ter pelo menos um administrador ativo.")
            repo.atualizar(replace(usuario, nome=usuario.nome.strip().upper()[:60]))

    def redefinir_senha(self, admin: Usuario, usuario: Usuario, senha_temporaria: str) -> None:
        """Senha temporária definida pelo administrador; o usuário troca no próximo acesso."""
        self._exigir_admin(admin)
        _validar_senha(senha_temporaria)
        with self.db.session() as s:
            UsuarioRepository(s).definir_senha(usuario.id, gerar_hash(senha_temporaria), trocar_senha=True)
