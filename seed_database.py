from database import criar_tabelas, get_db
from repositories import criar_organizacao, listar_organizacoes


def executar():
    criar_tabelas()

    with get_db() as db:
        existentes = listar_organizacoes(db)

        if existentes:
            print("O banco já possui dados.")
            return

        criar_organizacao(
            db=db,
            nome="Organização Demonstração",
            slug="organizacao-demonstracao",
            segmento="Tecnologia",
            responsavel="Administrador",
            email="admin@exemplo.com",
        )

        print("Banco inicial criado com sucesso.")


if __name__ == "__main__":
    executar()
