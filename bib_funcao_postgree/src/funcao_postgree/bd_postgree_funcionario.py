"""
Modulo responsável pela adiministração do banco de dados dos funcionários.
"""

import random
import string
from .bd_postgree_base import Bd_Base
from typing import Tuple, Union
import json
from passlib.hash import pbkdf2_sha256 # type: ignore

class BdFuncionario(Bd_Base):
    """
    Classe para manipulação de dados da tabela funcionario no banco de dados PostgreSQL.

    Essa classe permite realizar operações como inserção, recuperação e validação de dados
    relacionados aos funcionários.
    """

    def __init__(self, host: str = 'localhost', database: str = 'database-postgres', user: str = 'root', password: str = 'root') -> None:
        """
        Inicializa a conexão com o banco de dados e cria a tabela funcionario caso ela não exista.

        Args:
            host (str): Endereço do host do banco de dados.
            database (str): Nome do banco de dados.
            user (str): Nome de usuário para autenticação.
            password (str): Senha para autenticação.
        """
        super().__init__(host, database, user, password)
        self.database_init()

    def database_init(self) -> None:
        """
        Cria a tabela funcionario no banco de dados caso ela não exista.
        """
        try:
            cursor = self.get_cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS funcionario (
                    id SERIAL PRIMARY KEY,
                    usuario VARCHAR(255) UNIQUE,
                    senha VARCHAR(255) NOT NULL,
                    email VARCHAR(255) NOT NULL UNIQUE
                );
            """)
            self.commit()
        except Exception as e:
            print(f"[LOG ERRO] Não foi possível criar a tabela: {e}")
        finally:
            cursor.close()

    def _format_from_inserct(self, funcionario: str) -> dict:
        """
        Formata os dados do funcionário para inserção no banco de dados.

        Args:
            funcionario (str): Dados do funcionário em formato JSON.

        Returns:
            dict: Dicionário contendo os dados formatados para inserção.
        """
        valor = json.loads(funcionario)
        valor["senha"] = pbkdf2_sha256.hash(valor["senha"])
        return (valor['usuario'], valor["senha"], valor["email"])

    def insert_funcionario(self, funcionario: str) -> bool:
        """
        Insere um novo funcionário no banco de dados.

        Args:
            funcionario (str): Dados do funcionário em formato JSON.

        Returns:
            bool: True se a inserção foi bem-sucedida, False caso contrário.
        """
        retorno = True
        try:
            valor = self._format_from_inserct(funcionario)
            query = """
                INSERT INTO funcionario (usuario, senha, email)
                VALUES (%s, %s, %s)
            """
            cursor = self.get_cursor()
            cursor.execute(query, valor)
            self.commit()
        except Exception as e:
            print("[LOG ERRO] Erro ao inserir funcionario: ", e)
            self.post_client.rollback()
            retorno = False
        finally:
            cursor.close()

        return retorno

    def get_email(self, usuario: str) -> str:
        """
        Recupera o e-mail de um funcionário com base no nome de usuário.

        Args:
            usuario (str): Nome de usuário do funcionário.

        Returns:
            str: E-mail do funcionário, ou uma string vazia se não encontrado.
        """
        retorno = ""
        try:
            query = """
                SELECT email FROM funcionario 
                WHERE usuario = %s
            """
            cursor = self.get_cursor()
            cursor.execute(query, (usuario,))
            resultado = cursor.fetchone()

            if resultado:
                retorno = resultado[0]
        except Exception as e:
            print("[LOG ERRO] Erro ao recuperar email: ", e)
        finally:
            cursor.close()

        return retorno

    def validar_acesso(self, usuario: str, senha: str) -> bool:
        """
        Valida o acesso de um funcionário com base no nome de usuário e senha.

        Args:
            usuario (str): Nome de usuário do funcionário.
            senha (str): Senha do funcionário.

        Returns:
            bool: True se as credenciais forem válidas, False caso contrário.
        """
        retorno = False
        try:
            query = """
                SELECT senha FROM funcionario 
                WHERE usuario = %s
            """
            cursor = self.get_cursor()
            cursor.execute(query, (usuario,))
            resultado = cursor.fetchone()

            if resultado:
                retorno = pbkdf2_sha256.verify(senha, resultado[0])
        except Exception as e:
            print("[LOG ERRO] Erro ao validar acesso: ", e)
        finally:
            cursor.close()

        return retorno

    def recuperar_senha_usuario(self, email: str) -> Union[Tuple[str, str], bool]:
        """
        Gera uma nova senha para um funcionário e a atualiza no banco de dados.

        Args:
            email (str): E-mail do funcionário.

        Returns:
            Union[Tuple[str, str], bool]: Nome de usuário e nova senha gerada, ou False se não encontrado.
        """
        retorno = False

        try:
            query_select = """
                SELECT usuario FROM funcionario
                WHERE email = %s
            """
            query_update = """
                UPDATE funcionario
                SET senha = %s
                WHERE email = %s
            """
            cursor = self.get_cursor()
            cursor.execute(query_select, (email,))
            resultado = cursor.fetchone()

            if resultado:
                nova_senha = ''.join(random.choices(string.ascii_letters + string.digits, k=8))  # Gera senha aleatória de 8 caracteres
                hash_senha = pbkdf2_sha256.hash(nova_senha)
                cursor.execute(query_update, (hash_senha, email))
                self.commit()
                retorno = (resultado[0], nova_senha)
        except Exception as e:
            print("[LOG ERRO] Erro ao recuperar senha: ", e)
        finally:
            if cursor:
                cursor.close()

        return retorno

    def trocar_senha(self, usuario: str, senha: str) -> bool:
        """
        Atualiza a senha de um funcionário no banco de dados.

        Args:
            usuario (str): Nome de usuário do funcionário.
            senha (str): Nova senha do funcionário.

        Returns:
            bool: True se a senha foi atualizada com sucesso, False caso contrário.
        """
        retorno = False
        try:
            query = """
                UPDATE funcionario
                SET senha = %s
                WHERE usuario = %s
            """
            cursor = self.get_cursor()
            cursor.execute(query, (pbkdf2_sha256.hash(senha), usuario))
            self.commit()
            retorno = True
        except Exception as e:
            print("[LOG ERRO] Erro ao trocar senha: ", e)
        finally:
            cursor.close()

        return retorno
