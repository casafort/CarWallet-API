from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from models import CategoriaDespesa

# --- VEÍCULO ---
class VeiculoBase(BaseModel):
    # REGEX DUPLA: Trava a API para aceitar apenas os padrões do Brasil/Mercosul.
    # Explicando o código:
    # ^[A-Z]{3} = Começa com 3 letras (Maiúsculas)
    # [0-9]{4} = Seguido de 4 números (Padrão Antigo)
    # | = OU
    # ^[A-Z]{3}[0-9][A-Z][0-9]{2}$ = Mercosul (3 letras, 1 número, 1 letra, 2 números)
    placa: str = Field(..., pattern="^[A-Z]{3}[0-9]{4}$|^[A-Z]{3}[0-9][A-Z][0-9]{2}$", description="Placa no padrão Brasileiro antigo ou Mercosul, sem espaços.")
    marca: str
    modelo: str
    ano: int
    tipo: str
    combustivel: str
    odometro_inicial: float

class VeiculoCreate(VeiculoBase):
    pass

class VeiculoResponse(VeiculoBase):
    id: int
    class Config:
        from_attributes = True

# --- ABASTECIMENTO ---
class AbastecimentoCreate(BaseModel):
    veiculo_id: int
    quilometragem: float
    litros: float
    valor_total: float

class AbastecimentoResponse(AbastecimentoCreate):
    id: int
    class Config:
        from_attributes = True

# --- DESPESA ---
class DespesaCreate(BaseModel):
    veiculo_id: int
    tipo_despesa: CategoriaDespesa
    valor: float
    data_despesa: Optional[datetime] = None
    observacao: Optional[str] = None
    odometro_atual: Optional[float] = None

class DespesaResponse(DespesaCreate):
    id: int
    class Config:
        from_attributes = True

# --- ABASTECIMENTO ---
class AbastecimentoCreate(BaseModel):
    veiculo_id: int
    quilometragem: float
    litros: float
    valor_total: float
    data_abastecimento: Optional[datetime] = None  # <- ADICIONE ESTA LINHA