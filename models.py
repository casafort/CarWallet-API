from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum as SQLAlchemyEnum, create_engine
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import enum
from datetime import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./carwallet.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class CategoriaDespesa(str, enum.Enum):
    COMBUSTIVEL = "Combustível"
    MANUTENCAO = "Manutenção"
    IMPOSTO = "Imposto"
    MULTA = "Multa"        
    ESTETICA = "Estética"
    SEGURO = "Seguro"
    OUTROS = "Outros"

class VeiculoDB(Base):
    __tablename__ = "veiculos"
    id = Column(Integer, primary_key=True, index=True)
    placa = Column(String, unique=True, index=True) 
    marca = Column(String)                          
    modelo = Column(String)                         
    ano = Column(Integer)                           
    tipo = Column(String)                           
    combustivel = Column(String)                    
    odometro_inicial = Column(Float, default=0.0)   
    abastecimentos = relationship("AbastecimentoDB", back_populates="veiculo")
    despesas = relationship("DespesaDB", back_populates="veiculo")

class AbastecimentoDB(Base):
    __tablename__ = "abastecimentos"
    id = Column(Integer, primary_key=True, index=True)
    veiculo_id = Column(Integer, ForeignKey("veiculos.id"))
    quilometragem = Column(Float)
    litros = Column(Float)
    valor_total = Column(Float)
    data_abastecimento = Column(DateTime, default=datetime.utcnow) # NOVO CAMPO DE DATA
    veiculo = relationship("VeiculoDB", back_populates="abastecimentos")

class DespesaDB(Base):
    __tablename__ = "despesas"
    id = Column(Integer, primary_key=True, index=True)
    veiculo_id = Column(Integer, ForeignKey("veiculos.id"))
    data_despesa = Column(DateTime, default=datetime.utcnow)
    tipo_despesa = Column(SQLAlchemyEnum(CategoriaDespesa))
    valor = Column(Float)
    observacao = Column(String, nullable=True)     
    odometro_atual = Column(Float, nullable=True)  
    veiculo = relationship("VeiculoDB", back_populates="despesas")

Base.metadata.create_all(bind=engine)