"""
Suite de Testes Automatizados - Sistema de Gerenciamento de Tarefas
====================================================================
Cobertura:
  - Testes Unitários  : modelos User e Task, hashing de senha
  - Testes de Integração : fluxo completo de registro, login, logout
  - Testes Funcionais : CRUD de tarefas, controle de acesso, proteção de rotas
"""

import sys
import os
import pytest

# Garante que o pacote todo_project seja encontrado no PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'todo_project'))

from todo_project import app as flask_app, db, bcrypt
from todo_project.models import User, Task


# ──────────────────────────────────────────────────────────────────────────────
# FIXTURES
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope='function')
def app():
    """Cria uma instância isolada da aplicação com banco de dados em memória."""
    flask_app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,           # Desabilita CSRF nos formulários durante testes
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SECRET_KEY': 'chave-de-teste-segura',
        'LOGIN_DISABLED': False,
    })
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Cliente HTTP de teste Flask."""
    return app.test_client()


@pytest.fixture(scope='function')
def usuario_registrado(app):
    """Cria um usuário já persistido no banco para testes que exigem conta existente."""
    with app.app_context():
        senha_hash = bcrypt.generate_password_hash('Senha@123').decode('utf-8')
        usuario = User(username='testuser', password=senha_hash)
        db.session.add(usuario)
        db.session.commit()
        return {'username': 'testuser', 'password': 'Senha@123'}


def login(client, username, password):
    """Função auxiliar que realiza login via POST e retorna a resposta."""
    return client.post('/login', data={
        'username': username,
        'password': password,
    }, follow_redirects=True)


def logout(client):
    """Função auxiliar que realiza logout."""
    return client.get('/logout', follow_redirects=True)


# ══════════════════════════════════════════════════════════════════════════════
# BLOCO 1 — TESTES UNITÁRIOS (Modelos e Segurança)
# ══════════════════════════════════════════════════════════════════════════════

class TestModeloUser:
    """Testes unitários do modelo User."""

    def test_criar_usuario_atributos_corretos(self, app):
        """Verifica se o objeto User é criado com os atributos corretos."""
        with app.app_context():
            user = User(username='davi', password='hash_qualquer')
            assert user.username == 'davi'
            assert user.password == 'hash_qualquer'

    def test_repr_usuario(self, app):
        """Verifica a representação em string do modelo User."""
        with app.app_context():
            user = User(username='davi', password='x')
            assert 'davi' in repr(user)

    def test_senha_armazenada_como_hash(self, app):
        """Garante que senhas NUNCA são salvas em texto plano — requisito de segurança."""
        with app.app_context():
            senha_original = 'MinhaSenhaForte'
            hash_senha = bcrypt.generate_password_hash(senha_original).decode('utf-8')
            user = User(username='seguro', password=hash_senha)
            db.session.add(user)
            db.session.commit()

            user_db = User.query.filter_by(username='seguro').first()
            assert user_db.password != senha_original, "FALHA DE SEGURANÇA: senha em texto plano!"
            assert bcrypt.check_password_hash(user_db.password, senha_original)

    def test_username_unico_no_banco(self, app):
        """Verifica a constraint de unicidade do username."""
        with app.app_context():
            from sqlalchemy.exc import IntegrityError
            hash_senha = bcrypt.generate_password_hash('abc').decode('utf-8')
            user1 = User(username='duplicado', password=hash_senha)
            user2 = User(username='duplicado', password=hash_senha)
            db.session.add(user1)
            db.session.commit()
            db.session.add(user2)
            with pytest.raises(IntegrityError):
                db.session.commit()


class TestModeloTask:
    """Testes unitários do modelo Task."""

    def test_criar_tarefa_com_conteudo(self, app):
        """Verifica criação básica de tarefa vinculada a um usuário."""
        with app.app_context():
            hash_senha = bcrypt.generate_password_hash('abc').decode('utf-8')
            user = User(username='autor', password=hash_senha)
            db.session.add(user)
            db.session.commit()

            tarefa = Task(content='Estudar DevSecOps', user_id=user.id)
            db.session.add(tarefa)
            db.session.commit()

            tarefa_db = Task.query.first()
            assert tarefa_db.content == 'Estudar DevSecOps'
            assert tarefa_db.user_id == user.id

    def test_repr_tarefa(self, app):
        """Verifica a representação em string do modelo Task."""
        with app.app_context():
            hash_senha = bcrypt.generate_password_hash('abc').decode('utf-8')
            user = User(username='autor2', password=hash_senha)
            db.session.add(user)
            db.session.commit()
            tarefa = Task(content='Minha Tarefa', user_id=user.id)
            assert 'Minha Tarefa' in repr(tarefa)

    def test_data_postagem_preenchida_automaticamente(self, app):
        """Verifica que date_posted é preenchido automaticamente pelo modelo."""
        with app.app_context():
            hash_senha = bcrypt.generate_password_hash('abc').decode('utf-8')
            user = User(username='autor3', password=hash_senha)
            db.session.add(user)
            db.session.commit()
            tarefa = Task(content='Tarefa com Data', user_id=user.id)
            db.session.add(tarefa)
            db.session.commit()
            assert tarefa.date_posted is not None

    def test_relacao_usuario_tarefas(self, app):
        """Testa o relacionamento ORM entre User e Task."""
        with app.app_context():
            hash_senha = bcrypt.generate_password_hash('abc').decode('utf-8')
            user = User(username='relacao', password=hash_senha)
            db.session.add(user)
            db.session.commit()
            t1 = Task(content='Tarefa 1', user_id=user.id)
            t2 = Task(content='Tarefa 2', user_id=user.id)
            db.session.add_all([t1, t2])
            db.session.commit()

            user_db = User.query.filter_by(username='relacao').first()
            assert len(user_db.tasks) == 2


# ══════════════════════════════════════════════════════════════════════════════
# BLOCO 2 — TESTES DE INTEGRAÇÃO (Autenticação)
# ══════════════════════════════════════════════════════════════════════════════

class TestAutenticacao:
    """Testes de integração do fluxo de autenticação (Caso de Uso 01 e 02)."""

    def test_registro_novo_usuario_valido(self, client):
        """Fluxo de registro completo com dados válidos deve redirecionar para login."""
        resposta = client.post('/register', data={
            'username': 'novousuario',
            'password': 'Senha@123',
            'confirm_password': 'Senha@123',
        }, follow_redirects=True)
        assert resposta.status_code == 200
        assert b'novousuario' in resposta.data or b'Login' in resposta.data

    def test_registro_usuario_duplicado_rejeitado(self, client, usuario_registrado):
        """Tentativa de registrar username já existente deve falhar com erro."""
        resposta = client.post('/register', data={
            'username': usuario_registrado['username'],
            'password': 'Senha@123',
            'confirm_password': 'Senha@123',
        }, follow_redirects=True)
        assert b'Username Exists' in resposta.data

    def test_login_credenciais_validas(self, client, usuario_registrado):
        """Login com credenciais corretas deve redirecionar para lista de tarefas."""
        resposta = login(client, usuario_registrado['username'], usuario_registrado['password'])
        assert resposta.status_code == 200
        assert b'Login Successfull' in resposta.data or b'All Tasks' in resposta.data or b'Task' in resposta.data

    def test_login_senha_errada_bloqueado(self, client, usuario_registrado):
        """Login com senha incorreta deve exibir mensagem de erro — mitigação T01."""
        resposta = login(client, usuario_registrado['username'], 'SenhaErrada')
        assert b'Unsuccessful' in resposta.data or b'Password' in resposta.data

    def test_login_usuario_inexistente_bloqueado(self, client):
        """Login com usuário que não existe no banco deve ser bloqueado."""
        resposta = login(client, 'fantasma', 'qualquersenha')
        assert b'Unsuccessful' in resposta.data or b'Password' in resposta.data

    def test_logout_encerra_sessao(self, client, usuario_registrado):
        """Logout deve encerrar a sessão e redirecionar para login."""
        login(client, usuario_registrado['username'], usuario_registrado['password'])
        resposta = logout(client)
        assert resposta.status_code == 200
        assert b'Login' in resposta.data


# ══════════════════════════════════════════════════════════════════════════════
# BLOCO 3 — TESTES FUNCIONAIS (CRUD e Controle de Acesso)
# ══════════════════════════════════════════════════════════════════════════════

class TestRotasPublicas:
    """Testes das rotas públicas acessíveis sem autenticação."""

    def test_pagina_about_acessivel(self, client):
        """Rota raiz deve retornar 200 sem autenticação."""
        resposta = client.get('/')
        assert resposta.status_code == 200

    def test_pagina_login_acessivel(self, client):
        """Rota /login deve retornar 200 sem autenticação."""
        resposta = client.get('/login')
        assert resposta.status_code == 200

    def test_pagina_register_acessivel(self, client):
        """Rota /register deve retornar 200 sem autenticação."""
        resposta = client.get('/register')
        assert resposta.status_code == 200


class TestControleDeAcesso:
    """
    Testes funcionais de controle de acesso — Caso de Uso 02.
    Garante que rotas protegidas bloqueiam usuários não autenticados.
    """

    def test_all_tasks_requer_autenticacao(self, client):
        """Acesso direto a /all_tasks sem login deve redirecionar para /login."""
        resposta = client.get('/all_tasks', follow_redirects=False)
        assert resposta.status_code == 302
        assert '/login' in resposta.headers.get('Location', '')

    def test_add_task_requer_autenticacao(self, client):
        """Acesso direto a /add_task sem login deve redirecionar para /login."""
        resposta = client.get('/add_task', follow_redirects=False)
        assert resposta.status_code == 302
        assert '/login' in resposta.headers.get('Location', '')

    def test_account_requer_autenticacao(self, client):
        """Acesso direto a /account sem login deve redirecionar para /login."""
        resposta = client.get('/account', follow_redirects=False)
        assert resposta.status_code == 302
        assert '/login' in resposta.headers.get('Location', '')

    def test_change_password_requer_autenticacao(self, client):
        """Acesso direto a /account/change_password sem login deve redirecionar."""
        resposta = client.get('/account/change_password', follow_redirects=False)
        assert resposta.status_code == 302
        assert '/login' in resposta.headers.get('Location', '')

    def test_delete_task_requer_autenticacao(self, client):
        """Tentativa de deletar tarefa sem sessão ativa deve ser bloqueada."""
        resposta = client.get('/all_tasks/1/delete_task', follow_redirects=False)
        assert resposta.status_code == 302
        assert '/login' in resposta.headers.get('Location', '')


class TestCRUDTarefas:
    """Testes funcionais das operações CRUD de tarefas."""

    def test_criar_tarefa_usuario_autenticado(self, client, usuario_registrado):
        """Usuário autenticado deve conseguir criar uma tarefa com sucesso."""
        login(client, usuario_registrado['username'], usuario_registrado['password'])
        resposta = client.post('/add_task', data={
            'task_name': 'Tarefa de Teste CI/CD',
        }, follow_redirects=True)
        assert resposta.status_code == 200
        assert b'Task Created' in resposta.data

    def test_listar_tarefas_usuario_autenticado(self, client, usuario_registrado, app):
        """Usuário autenticado deve ver suas tarefas na listagem."""
        with app.app_context():
            user = User.query.filter_by(username=usuario_registrado['username']).first()
            tarefa = Task(content='Tarefa Visivel', user_id=user.id)
            db.session.add(tarefa)
            db.session.commit()

        login(client, usuario_registrado['username'], usuario_registrado['password'])
        resposta = client.get('/all_tasks')
        assert resposta.status_code == 200
        assert b'Tarefa Visivel' in resposta.data

    def test_deletar_tarefa_proprio_usuario(self, client, usuario_registrado, app):
        """Usuário autenticado deve conseguir deletar suas próprias tarefas."""
        with app.app_context():
            user = User.query.filter_by(username=usuario_registrado['username']).first()
            tarefa = Task(content='Tarefa para Deletar', user_id=user.id)
            db.session.add(tarefa)
            db.session.commit()
            task_id = tarefa.id

        login(client, usuario_registrado['username'], usuario_registrado['password'])
        resposta = client.get(f'/all_tasks/{task_id}/delete_task', follow_redirects=True)
        assert resposta.status_code == 200
        assert b'Task Deleted' in resposta.data

    def test_atualizar_tarefa(self, client, usuario_registrado, app):
        """Usuário autenticado deve conseguir atualizar o conteúdo de uma tarefa."""
        with app.app_context():
            user = User.query.filter_by(username=usuario_registrado['username']).first()
            tarefa = Task(content='Conteudo Original', user_id=user.id)
            db.session.add(tarefa)
            db.session.commit()
            task_id = tarefa.id

        login(client, usuario_registrado['username'], usuario_registrado['password'])
        resposta = client.post(f'/all_tasks/{task_id}/update_task', data={
            'task_name': 'Conteudo Atualizado',
        }, follow_redirects=True)
        assert resposta.status_code == 200
        assert b'Task Updated' in resposta.data


class TestTratamentoDeErros:
    """Testes dos handlers de erro HTTP."""

    def test_rota_inexistente_retorna_404(self, client):
        """Rota inexistente deve retornar HTTP 404."""
        resposta = client.get('/esta-rota-nao-existe')
        assert resposta.status_code == 404