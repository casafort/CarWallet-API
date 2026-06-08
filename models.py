from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. CONFIGURAÇÃO DO BANCO DE DADOS (SQLITE)
SQLALCHEMY_DATABASE_URL = "sqlite:///./carwallet.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 2. DEFINIÇÃO DA TABELA DE VEÍCULOS
class VeiculoDB(Base):
    __tablename__ = "veiculos"
    
    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String, index=True)
    modelo = Column(String, index=True)
    placa = Column(String, unique=True, index=True)
    combustivel = Column(String)

# 3. DEFINIÇÃO DA TABELA DE ABASTECIMENTOS
class AbastecimentoDB(Base):
    __tablename__ = "abastecimentos"
    
    id = Column(Integer, primary_key=True, index=True)
    veiculo_id = Column(Integer, ForeignKey("veiculos.id")) # Conecta com o veículo
    quilometragem = Column(Float)
    litros = Column(Float)
    valor_total = Column(Float)

# 4. DEFINIÇÃO DA TABELA DE DESPESAS (Manutenção, Impostos, Seguros)
class DespesaDB(Base):
    __tablename__ = "despesas"
    
    id = Column(Integer, primary_key=True, index=True)
    veiculo_id = Column(Integer, ForeignKey("veiculos.id")) # Conecta com o veículo
    data_despesa = Column(String) # Formato YYYY-MM-DD
    tipo_despesa = Column(String) # Ex: "Manutenção", "Imposto", "Seguro"
    descricao = Column(String)
    valor = Column(Float)

# Comando que cria o banco e as tabelas fisicamente
Base.metadata.create_all(bind=engine)