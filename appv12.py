import os
import re
import unicodedata
from contextlib import contextmanager
from datetime import datetime

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

# ============================================================
# CONFIGURAÇÃO
# ============================================================

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./ctr_defense.db",
)

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)

if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

engine_kwargs = {
    "pool_pre_ping": True,
}

if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


# ============================================================
# MODELOS
# ============================================================

class Organizacao(Base):
    __tablename__ = "organizacoes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    segmento: Mapped[str | None] = mapped_column(String(150))
    responsavel: Mapped[str | None] = mapped_column(String(150))
    email: Mapped[str | None] = mapped_column(String(200))
    ativa: Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    avaliacoes = relationship(
        "Avaliacao",
        back_populates="organizacao",
        cascade="all, delete-orphan",
    )
    riscos = relationship(
        "Risco",
        back_populates="organizacao",
        cascade="all, delete-orphan",
    )
    gaps = relationship(
        "Gap",
        back_populates="organizacao",
        cascade="all, delete-orphan",
    )
    acoes = relationship(
        "Acao",
        back_populates="organizacao",
        cascade="all, delete-orphan",
    )


class Avaliacao(Base):
    __tablename__ = "avaliacoes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organizacao_id: Mapped[int] = mapped_column(ForeignKey("organizacoes.id"))
    framework: Mapped[str] = mapped_column(String(100), nullable=False)
    item_id: Mapped[str] = mapped_column(String(100), nullable=False)
    titulo: Mapped[str] = mapped_column(String(300), nullable=False)
    status: Mapped[str] = mapped_column(String(80), default="Não iniciado")
    observacao: Mapped[str | None] = mapped_column(Text)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    organizacao = relationship("Organizacao", back_populates="avaliacoes")


class Risco(Base):
    __tablename__ = "riscos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organizacao_id: Mapped[int] = mapped_column(ForeignKey("organizacoes.id"))
    titulo: Mapped[str] = mapped_column(String(300), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    probabilidade: Mapped[int] = mapped_column(Integer, default=1)
    impacto: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(60), default="Aberto")
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    organizacao = relationship("Organizacao", back_populates="riscos")

    @property
    def nivel(self):
        return self.probabilidade * self.impacto


class Gap(Base):
    __tablename__ = "gaps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organizacao_id: Mapped[int] = mapped_column(ForeignKey("organizacoes.id"))
    titulo: Mapped[str] = mapped_column(String(300), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    prioridade: Mapped[str] = mapped_column(String(30), default="Média")
    status: Mapped[str] = mapped_column(String(60), default="Aberto")
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    organizacao = relationship("Organizacao", back_populates="gaps")


class Acao(Base):
    __tablename__ = "acoes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organizacao_id: Mapped[int] = mapped_column(ForeignKey("organizacoes.id"))
    titulo: Mapped[str] = mapped_column(String(300), nullable=False)
    responsavel: Mapped[str | None] = mapped_column(String(150))
    prazo: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(60), default="Não iniciada")
    percentual: Mapped[float] = mapped_column(Float, default=0)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    organizacao = relationship("Organizacao", back_populates="acoes")


Base.metadata.create_all(engine)


@contextmanager
def db_session():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ============================================================
# CONSTANTES
# ============================================================

STATUS_AVALIACAO = [
    "Não iniciado",
    "Em análise",
    "Em implementação",
    "Parcialmente implementado",
    "Implementado",
    "Não aplicável",
]

PERCENTUAIS = {
    "Não iniciado": 0,
    "Em análise": 15,
    "Em implementação": 50,
    "Parcialmente implementado": 75,
    "Implementado": 100,
    "Não aplicável": 100,
}

CIS_CONTROLS = [
    (1, "Inventário e controle de ativos corporativos", "IG1"),
    (2, "Inventário e controle de ativos de software", "IG1"),
    (3, "Proteção de dados", "IG1"),
    (4, "Configuração segura de ativos corporativos", "IG1"),
    (5, "Gerenciamento de contas", "IG1"),
    (6, "Gerenciamento de controle de acesso", "IG1"),
    (7, "Gerenciamento contínuo de vulnerabilidades", "IG1"),
    (8, "Gerenciamento de logs de auditoria", "IG1"),
    (9, "Proteção de e-mail e navegador web", "IG1"),
    (10, "Defesas contra malware", "IG1"),
    (11, "Recuperação de dados", "IG1"),
    (12, "Gerenciamento da infraestrutura de rede", "IG2"),
    (13, "Monitoramento e defesa de rede", "IG2"),
    (14, "Conscientização e treinamento de segurança", "IG2"),
    (15, "Gerenciamento de provedores de serviços", "IG2"),
    (16, "Segurança de aplicações", "IG2"),
    (17, "Gerenciamento de resposta a incidentes", "IG2"),
    (18, "Testes de penetração", "IG3"),
]

NIST_RMF = [
    ("Prepare", "Preparar"),
    ("Categorize", "Categorizar"),
    ("Select", "Selecionar"),
    ("Implement", "Implementar"),
    ("Assess", "Avaliar"),
    ("Authorize", "Autorizar"),
    ("Monitor", "Monitorar"),
]


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def limpar_texto_pdf(valor, padrao="-"):
    if valor is None:
        return padrao

    try:
        if pd.isna(valor):
            return padrao
    except Exception:
        pass

    texto = str(valor).strip()

    if not texto:
        return padrao

    substituicoes = {
        "—": "-",
        "–": "-",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "•": "-",
        "✅": "",
        "🛡️": "",
    }

    for origem, destino in substituicoes.items():
        texto = texto.replace(origem, destino)

    texto = unicodedata.normalize("NFKD", texto)
    texto = texto.encode("latin-1", "replace").decode("latin-1")
    texto = "".join(c for c in texto if ord(c) >= 32 or c in "\n\t")
    texto = re.sub(r"[ \t]+", " ", texto)

    return texto.strip() or padrao


def quebrar_textos_longos(texto, tamanho=70):
    texto = limpar_texto_pdf(texto)
    linhas_resultado = []

    for linha in texto.splitlines():
        linha = linha.strip()

        if not linha:
            linhas_resultado.append("")
            continue

        while len(linha) > tamanho:
            corte = linha.rfind(" ", 0, tamanho)

            if corte <= 0:
                corte = tamanho

            linhas_resultado.append(linha[:corte].strip())
            linha = linha[corte:].strip()

        linhas_resultado.append(linha)

    return "\n".join(linhas_resultado) or "-"


def percentual_avaliacao(avaliacoes):
    if not avaliacoes:
        return 0

    valores = [
        PERCENTUAIS.get(item.status, 0)
        for item in avaliacoes
    ]

    return round(sum(valores) / len(valores), 1)


def obter_organizacoes():
    with db_session() as db:
        return db.query(Organizacao).order_by(Organizacao.nome).all()


def obter_organizacao(organizacao_id):
    with db_session() as db:
        return db.get(Organizacao, organizacao_id)


def criar_dados_framework(db, organizacao_id):
    existentes = (
        db.query(Avaliacao)
        .filter(Avaliacao.organizacao_id == organizacao_id)
        .count()
    )

    if existentes > 0:
        return

    for numero, titulo, grupo in CIS_CONTROLS:
        db.add(
            Avaliacao(
                organizacao_id=organizacao_id,
                framework="CIS Controls v8",
                item_id=f"CIS-{numero:02d}",
                titulo=f"{titulo} ({grupo})",
            )
        )

    for codigo, titulo in NIST_RMF:
        db.add(
            Avaliacao(
                organizacao_id=organizacao_id,
                framework="NIST RMF",
                item_id=codigo,
                titulo=titulo,
            )
        )


# ============================================================
# PDF
# ============================================================

class RelatorioPDF(FPDF):
    def __init__(self):
        super().__init__("P", "mm", "A4")
        self.set_margins(15, 18, 15)
        self.set_auto_page_break(auto=True, margin=18)

    def largura_disponivel(self):
        return self.w - self.l_margin - self.r_margin

    def garantir_linha(self, altura=8):
        if self.get_y() + altura > self.h - self.b_margin:
            self.add_page()

    def escrever_multilinha(self, texto, largura=None, altura=5):
        largura = largura or self.largura_disponivel()
        self.garantir_linha(altura)
        self.multi_cell(
            largura,
            altura,
            quebrar_textos_longos(texto),
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )


def pdf_secao(pdf, titulo):
    pdf.ln(4)
    pdf.set_font("Arial", "B", 13)
    pdf.set_text_color(11, 48, 64)
    pdf.cell(
        pdf.largura_disponivel(),
        8,
        limpar_texto_pdf(titulo),
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )
    pdf.set_text_color(0, 0, 0)


def pdf_linha(pdf, titulo, valor, largura_titulo=42):
    largura_total = pdf.largura_disponivel()
    largura_valor = max(20, largura_total - largura_titulo)

    pdf.set_font("Arial", "B", 9)
    pdf.cell(
        largura_titulo,
        6,
        limpar_texto_pdf(titulo),
        new_x=XPos.RIGHT,
        new_y=YPos.TOP,
    )

    pdf.set_font("Arial", "", 9)
    pdf.multi_cell(
        largura_valor,
        6,
        quebrar_textos_longos(valor),
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )


def gerar_pdf_relatorio(organizacao_id):
    with db_session() as db:
        organizacao = db.get(Organizacao, organizacao_id)

        if not organizacao:
            return b""

        avaliacoes = (
            db.query(Avaliacao)
            .filter(Avaliacao.organizacao_id == organizacao_id)
            .order_by(Avaliacao.framework, Avaliacao.item_id)
            .all()
        )

        riscos = (
            db.query(Risco)
            .filter(Risco.organizacao_id == organizacao_id)
            .all()
        )

        gaps = (
            db.query(Gap)
            .filter(Gap.organizacao_id == organizacao_id)
            .all()
        )

        acoes = (
            db.query(Acao)
            .filter(Acao.organizacao_id == organizacao_id)
            .all()
        )

        pdf = RelatorioPDF()
        pdf.add_page()

        pdf.set_font("Arial", "B", 18)
        pdf.cell(
            pdf.largura_disponivel(),
            12,
            "CTR DEFENSE - Relatorio Executivo",
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )

        pdf.set_font("Arial", "", 9)
        pdf.cell(
            pdf.largura_disponivel(),
            6,
            datetime.now().strftime("%d/%m/%Y %H:%M"),
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )

        pdf_secao(pdf, "Identificacao")
        pdf_linha(pdf, "Organizacao:", organizacao.nome)
        pdf_linha(pdf, "Segmento:", organizacao.segmento)
        pdf_linha(pdf, "Responsavel:", organizacao.responsavel)
        pdf_linha(pdf, "E-mail:", organizacao.email)

        pdf_secao(pdf, "Resumo da Avaliacao")

        for framework in ["CIS Controls v8", "NIST RMF"]:
            itens = [a for a in avaliacoes if a.framework == framework]
            pdf_linha(
                pdf,
                f"{framework}:",
                f"{len(itens)} itens - {percentual_avaliacao(itens)}% de atendimento",
            )

        pdf_secao(pdf, "CIS Controls v8")

        cis = [a for a in avaliacoes if a.framework == "CIS Controls v8"]

        for item in cis:
            pdf.garantir_linha(10)
            pdf.set_font("Arial", "B", 9)
            pdf.cell(
                27,
                6,
                limpar_texto_pdf(item.item_id),
                new_x=XPos.RIGHT,
                new_y=YPos.TOP,
            )
            pdf.set_font("Arial", "", 9)
            pdf.multi_cell(
                pdf.largura_disponivel() - 27,
                6,
                quebrar_textos_longos(
                    f"{item.titulo} - {item.status}"
                ),
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )

        pdf_secao(pdf, "NIST RMF - 7 Etapas")

        rmf = [a for a in avaliacoes if a.framework == "NIST RMF"]

        for item in rmf:
            pdf_linha(
                pdf,
                f"{item.item_id}:",
                f"{item.titulo} - {item.status}",
            )

        pdf_secao(pdf, "Riscos")

        if riscos:
            for risco in riscos:
                pdf_linha(
                    pdf,
                    f"Risco {risco.id}:",
                    f"{risco.titulo} | Nivel: {risco.nivel} | Status: {risco.status}",
                )
                pdf.escrever_multilinha(risco.descricao)
        else:
            pdf.escrever_multilinha("Nenhum risco cadastrado.")

        pdf_secao(pdf, "Gaps")

        if gaps:
            for gap in gaps:
                pdf_linha(
                    pdf,
                    f"Gap {gap.id}:",
                    f"{gap.titulo} | Prioridade: {gap.prioridade} | Status: {gap.status}",
                )
                pdf.escrever_multilinha(gap.descricao)
        else:
            pdf.escrever_multilinha("Nenhum gap cadastrado.")

        pdf_secao(pdf, "Acoes")

        if acoes:
            for acao in acoes:
                pdf_linha(
                    pdf,
                    f"Acao {acao.id}:",
                    f"{acao.titulo} | Responsavel: {acao.responsavel} | "
                    f"Prazo: {acao.prazo} | Status: {acao.status} | "
                    f"{acao.percentual:.0f}%",
                )
        else:
            pdf.escrever_multilinha("Nenhuma acao cadastrada.")

        return bytes(pdf.output())


# ============================================================
# TELAS
# ============================================================

def tela_dashboard(organizacao_id):
    with db_session() as db:
        organizacao = db.get(Organizacao, organizacao_id)
        avaliacoes = (
            db.query(Avaliacao)
            .filter(Avaliacao.organizacao_id == organizacao_id)
            .all()
        )
        riscos = (
            db.query(Risco)
            .filter(Risco.organizacao_id == organizacao_id)
            .all()
        )
        gaps = (
            db.query(Gap)
            .filter(Gap.organizacao_id == organizacao_id)
            .all()
        )
        acoes = (
            db.query(Acao)
            .filter(Acao.organizacao_id == organizacao_id)
            .all()
        )

    st.title("Dashboard")
    st.caption(f"Organizacao ativa: {organizacao.nome}")

    colunas = st.columns(5)
    colunas[0].metric("Maturidade", f"{percentual_avaliacao(avaliacoes):.1f}%")
    colunas[1].metric("Avaliacoes", len(avaliacoes))
    colunas[2].metric("Riscos", len(riscos))
    colunas[3].metric("Gaps", len(gaps))
    colunas[4].metric("Acoes", len(acoes))

    if avaliacoes:
        dados = pd.DataFrame(
            [
                {
                    "Framework": item.framework,
                    "Status": item.status,
                    "Percentual": PERCENTUAIS.get(item.status, 0),
                }
                for item in avaliacoes
            ]
        )

        resumo = (
            dados.groupby("Framework", as_index=False)["Percentual"]
            .mean()
            .rename(columns={"Percentual": "Atendimento"})
        )

        st.subheader("Atendimento por framework")
        st.bar_chart(resumo.set_index("Framework"))

    st.subheader("Riscos prioritarios")

    if riscos:
        tabela = pd.DataFrame(
            [
                {
                    "Titulo": risco.titulo,
                    "Probabilidade": risco.probabilidade,
                    "Impacto": risco.impacto,
                    "Nivel": risco.nivel,
                    "Status": risco.status,
                }
                for risco in sorted(riscos, key=lambda x: x.nivel, reverse=True)
            ]
        )
        st.dataframe(tabela, use_container_width=True)
    else:
        st.info("Nenhum risco cadastrado.")


def tela_organizacoes():
    st.title("Organizacoes")

    with st.form("nova_organizacao"):
        nome = st.text_input("Nome da organizacao")
        segmento = st.text_input("Segmento")
        responsavel = st.text_input("Responsavel")
        email = st.text_input("E-mail")
        enviar = st.form_submit_button("Criar organizacao")

        if enviar:
            if not nome.strip():
                st.error("Informe o nome da organizacao.")
            else:
                with db_session() as db:
                    organizacao = Organizacao(
                        nome=nome.strip(),
                        segmento=segmento.strip(),
                        responsavel=responsavel.strip(),
                        email=email.strip(),
                    )
                    db.add(organizacao)
                    db.flush()
                    criar_dados_framework(db, organizacao.id)

                st.success("Organizacao criada com sucesso.")
                st.rerun()

    organizacoes = obter_organizacoes()

    if organizacoes:
        st.subheader("Organizacoes cadastradas")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "ID": organizacao.id,
                        "Nome": organizacao.nome,
                        "Segmento": organizacao.segmento,
                        "Responsavel": organizacao.responsavel,
                        "E-mail": organizacao.email,
                    }
                    for organizacao in organizacoes
                ]
            ),
            use_container_width=True,
        )


def tela_avaliacao(organizacao_id, framework):
    st.title(framework)

    with db_session() as db:
        itens = (
            db.query(Avaliacao)
            .filter(
                Avaliacao.organizacao_id == organizacao_id,
                Avaliacao.framework == framework,
            )
            .order_by(Avaliacao.item_id)
            .all()
        )

        if not itens:
            st.warning("Nenhum item encontrado.")
            return

        for item in itens:
            chave = f"status_{framework}_{item.id}"

            novo_status = st.selectbox(
                f"{item.item_id} - {item.titulo}",
                STATUS_AVALIACAO,
                index=STATUS_AVALIACAO.index(item.status)
                if item.status in STATUS_AVALIACAO
                else 0,
                key=chave,
            )

            observacao = st.text_area(
                "Observacao",
                value=item.observacao or "",
                key=f"obs_{framework}_{item.id}",
            )

            if novo_status != item.status or observacao != (item.observacao or ""):
                item.status = novo_status
                item.observacao = observacao

        if st.button("Salvar avaliacao", type="primary"):
            st.success("Avaliacao salva com sucesso.")


def tela_riscos(organizacao_id):
    st.title("Riscos")

    with st.form("novo_risco"):
        titulo = st.text_input("Titulo")
        descricao = st.text_area("Descricao")
        probabilidade = st.slider("Probabilidade", 1, 5, 3)
        impacto = st.slider("Impacto", 1, 5, 3)
        status = st.selectbox("Status", ["Aberto", "Em tratamento", "Aceito", "Encerrado"])

        if st.form_submit_button("Cadastrar risco"):
            if not titulo.strip():
                st.error("Informe o titulo.")
            else:
                with db_session() as db:
                    db.add(
                        Risco(
                            organizacao_id=organizacao_id,
                            titulo=titulo,
                            descricao=descricao,
                            probabilidade=probabilidade,
                            impacto=impacto,
                            status=status,
                        )
                    )
                st.success("Risco cadastrado.")
                st.rerun()

    with db_session() as db:
        riscos = (
            db.query(Risco)
            .filter(Risco.organizacao_id == organizacao_id)
            .order_by(Risco.id.desc())
            .all()
        )

    if riscos:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "ID": risco.id,
                        "Titulo": risco.titulo,
                        "Probabilidade": risco.probabilidade,
                        "Impacto": risco.impacto,
                        "Nivel": risco.nivel,
                        "Status": risco.status,
                    }
                    for risco in riscos
                ]
            ),
            use_container_width=True,
        )


def tela_gaps(organizacao_id):
    st.title("Gaps")

    with st.form("novo_gap"):
        titulo = st.text_input("Titulo")
        descricao = st.text_area("Descricao")
        prioridade = st.selectbox("Prioridade", ["Baixa", "Media", "Alta", "Critica"])
        status = st.selectbox("Status", ["Aberto", "Em tratamento", "Resolvido"])

        if st.form_submit_button("Cadastrar gap"):
            if not titulo.strip():
                st.error("Informe o titulo.")
            else:
                with db_session() as db:
                    db.add(
                        Gap(
                            organizacao_id=organizacao_id,
                            titulo=titulo,
                            descricao=descricao,
                            prioridade=prioridade,
                            status=status,
                        )
                    )
                st.success("Gap cadastrado.")
                st.rerun()

    with db_session() as db:
        gaps = (
            db.query(Gap)
            .filter(Gap.organizacao_id == organizacao_id)
            .order_by(Gap.id.desc())
            .all()
        )

    if gaps:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "ID": gap.id,
                        "Titulo": gap.titulo,
                        "Prioridade": gap.prioridade,
                        "Status": gap.status,
                    }
                    for gap in gaps
                ]
            ),
            use_container_width=True,
        )


def tela_acoes(organizacao_id):
    st.title("Plano de acoes")

    with st.form("nova_acao"):
        titulo = st.text_input("Titulo")
        responsavel = st.text_input("Responsavel")
        prazo = st.text_input("Prazo")
        status = st.selectbox(
            "Status",
            ["Nao iniciada", "Em andamento", "Concluida", "Cancelada"],
        )
        percentual = st.slider("Percentual concluido", 0, 100, 0)

        if st.form_submit_button("Cadastrar acao"):
            if not titulo.strip():
                st.error("Informe o titulo.")
            else:
                with db_session() as db:
                    db.add(
                        Acao(
                            organizacao_id=organizacao_id,
                            titulo=titulo,
                            responsavel=responsavel,
                            prazo=prazo,
                            status=status,
                            percentual=percentual,
                        )
                    )
                st.success("Acao cadastrada.")
                st.rerun()

    with db_session() as db:
        acoes = (
            db.query(Acao)
            .filter(Acao.organizacao_id == organizacao_id)
            .order_by(Acao.id.desc())
            .all()
        )

    if acoes:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "ID": acao.id,
                        "Titulo": acao.titulo,
                        "Responsavel": acao.responsavel,
                        "Prazo": acao.prazo,
                        "Status": acao.status,
                        "Percentual": acao.percentual,
                    }
                    for acao in acoes
                ]
            ),
            use_container_width=True,
        )


def tela_relatorios(organizacao_id):
    st.title("Relatorios")

    pdf = gerar_pdf_relatorio(organizacao_id)

    st.download_button(
        "Baixar relatorio PDF",
        data=pdf,
        file_name="relatorio_ctr_defense.pdf",
        mime="application/pdf",
    )


# ============================================================
# APLICACAO PRINCIPAL
# ============================================================

def main():
    st.set_page_config(
        page_title="CTR DEFENSE",
        page_icon="🛡️",
        layout="wide",
    )

    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.title("CTR DEFENSE")

    organizacoes = obter_organizacoes()

    if not organizacoes:
        st.info("Cadastre uma organizacao para iniciar.")
        tela_organizacoes()
        return

    mapa_organizacoes = {
        f"{organizacao.id} - {organizacao.nome}": organizacao.id
        for organizacao in organizacoes
    }

    organizacao_selecionada = st.sidebar.selectbox(
        "Organizacao ativa",
        list(mapa_organizacoes.keys()),
    )

    organizacao_id = mapa_organizacoes[organizacao_selecionada]

    menu = st.sidebar.radio(
        "Menu",
        [
            "Dashboard",
            "Organizacoes",
            "NIST CSF",
            "CIS Controls v8",
            "NIST RMF",
            "Riscos",
            "Gaps",
            "Acoes",
            "Relatorios",
        ],
    )

    if menu == "Dashboard":
        tela_dashboard(organizacao_id)

    elif menu == "Organizacoes":
        tela_organizacoes()

    elif menu == "NIST CSF":
        st.title("NIST CSF 2.0")
        st.info(
            "O modulo de avaliacao NIST CSF pode ser expandido com as categorias "
            "especificas da sua organizacao."
        )

    elif menu == "CIS Controls v8":
        tela_avaliacao(organizacao_id, "CIS Controls v8")

    elif menu == "NIST RMF":
        tela_avaliacao(organizacao_id, "NIST RMF")

    elif menu == "Riscos":
        tela_riscos(organizacao_id)

    elif menu == "Gaps":
        tela_gaps(organizacao_id)

    elif menu == "Acoes":
        tela_acoes(organizacao_id)

    elif menu == "Relatorios":
        tela_relatorios(organizacao_id)


if __name__ == "__main__":
    main()
