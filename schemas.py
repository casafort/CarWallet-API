from pydantic import BaseModel

class VeiculoCreate(BaseModel):
    tipo: str
    modelo: str
    placa: str
    combustivel: str

class AbastecimentoCreate(BaseModel):
    veiculo_id: int
    quilometragem: float
    litros: float
    valor_total: float

class DespesaCreate(BaseModel):
    veiculo_id: int
    data_despesa: str
    tipo_despesa: str
    descricao: str
    valor: float