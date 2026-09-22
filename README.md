# ctr-defense

# Install

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

cp .env.example .env

Para iniciar com SQLite, mantenha:
DATABASE_URL=sqlite:///./data/ctr_defense.db

Crie a pasta de dados caso ela não exista:
mkdir data

Criar o banco inicial
python seed_database.py

Iniciar a aplicação
treamlit run appv12.py

A aplicação será disponibilizada normalmente em:
http://localhost:8501

Instalação com PostgreSQL usando Docker
docker compose up -d postgres

2. Editar o arquivo .env
APP_ENV=development
DATABASE_URL=postgresql+psycopg2://ctr_user:ctr_senha_altere@localhost:5432/ctr_defense
APP_SECRET_KEY=chave-local-de-desenvolvimento

Criar as tabelas e o registro inicial
python seed_database.py

 Iniciar a aplicação
 streamlit run appv12.py
-------------------------------------------------------------------------------
 Execução em produção
No servidor:
git clone https://github.com/SEU_USUARIO/ctr-defense.git
cd ctr-defense

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

cp .env.example .env
nano .env

python seed_database.py

streamlit run appv12.py \
  --server.address 0.0.0.0 \
  --server.port 8501
--------------------------------------------------------------------------------

Criar backup:
pg_dump -U ctr_user -h localhost -F c -b -v -f ctr_defense_backup.dump ctr_defense
Restore:
pg_restore -U ctr_user -h localhost -d ctr_defense -v ctr_defense_backup.dump


---------------------------------------------------------------------------------

# CTR DEFENSE

Sistema de gestão de cibersegurança, riscos, conformidade e adequação a frameworks.

A aplicação foi desenvolvida com:

- Python;
- Streamlit;
- PostgreSQL ou SQLite;
- SQLAlchemy;
- Pandas;
- Plotly;
- fpdf2.

## Funcionalidades

- Dashboard executivo;
- Cadastro de organizações;
- Assessment NIST CSF 2.0;
- CIS Controls v8;
- 18 controles CIS;
- Priorização IG1, IG2 e IG3;
- NIST RMF;
- 7 etapas do NIST RMF;
- Matriz de riscos;
- Gap Analysis;
- Plano de ação;
- Roadmap de segurança;
- Registro de reuniões;
- Exportação para PDF;
- Exportação para CSV;
- Persistência em banco de dados.

---

## Requisitos

- Python 3.11 ou superior;
- Git;
- PostgreSQL 14 ou superior para produção.

Para desenvolvimento, também é possível utilizar SQLite.

---

## Instalação local

### 1. Clonar o repositório

```bash
git clone https://github.com/SEU_USUARIO/ctr-defense.git
cd ctr-defense

