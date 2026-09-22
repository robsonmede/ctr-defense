# repositories.py

from typing import Optional

from models import Organizacao


def listar_organizacoes(db):
    """
    Retorna todas as organizações cadastradas.
    """
    return (
        db.query(Organizacao)
        .order_by(Organizacao.nome.asc())
        .all()
    )


def buscar_organizacao_por_id(db, organizacao_id: int):
    """
    Busca uma organização pelo ID.
    """
    return (
        db.query(Organizacao)
        .filter(Organizacao.id == organizacao_id)
        .first()
    )


def buscar_organizacao_por_slug(db, slug: str):
    """
    Busca uma organização pelo slug.
    """
    return (
        db.query(Organizacao)
        .filter(Organizacao.slug == slug)
        .first()
    )


def criar_organizacao(
    db,
    nome: str,
    slug: Optional[str] = None,
    segmento: Optional[str] = None,
    responsavel: Optional[str] = None,
    email: Optional[str] = None,
):
    """
    Cria e persiste uma organização.
    """

    organizacao = Organizacao(
        nome=nome,
        slug=slug,
        segmento=segmento,
        responsavel=responsavel,
        email=email,
    )

    db.add(organizacao)
    db.flush()

    return organizacao
