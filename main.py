from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import models
import schemas
from services import VeiculoService

# Inicialização do App
app = FastAPI(title="CarWallet API - AV2")

# Função auxiliar para gerenciar a sessão do banco de dados
# (Padrão de Injeção de Dependência)
def get_db():
    db = models.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- ROTAS DE VEÍCULOS ---

@app.get("/veiculos")
def listar_veiculos(db: Session = Depends(get_db)):
    """Retorna a lista de todos os veículos cadastrados."""
    veiculos = db.query(models.VeiculoDB).all()
    return veiculos

@app.post("/veiculos")
def cadastrar_veiculo(veiculo: schemas.VeiculoCreate, db: Session = Depends(get_db)):
    """Cadastra um novo veículo, verificando se a placa já existe."""
    veiculo_existente = db.query(models.VeiculoDB).filter(models.VeiculoDB.placa == veiculo.placa).first()
    if veiculo_existente:
        raise HTTPException(status_code=400, detail="Esta placa já está cadastrada.")
    
    novo_veiculo = models.VeiculoDB(
        tipo=veiculo.tipo,
        modelo=veiculo.modelo,
        placa=veiculo.placa,
        combustivel=veiculo.combustivel
    )
    
    db.add(novo_veiculo)
    db.commit()
    db.refresh(novo_veiculo)
    
    return {"mensagem": "Veículo salvo com sucesso!", "id_gerado": novo_veiculo.id}

# --- ROTAS DE ABASTECIMENTO ---

@app.post("/abastecimentos")
def registrar_abastecimento(abastecimento: schemas.AbastecimentoCreate, db: Session = Depends(get_db)):
    """
    Registra um novo abastecimento e utiliza o VeiculoService 
    para calcular a média de consumo (Km/L).
    """
    
    # 1. Validação: O veículo precisa existir
    veiculo = db.query(models.VeiculoDB).filter(models.VeiculoDB.id == abastecimento.veiculo_id).first()
    if not veiculo:
        raise HTTPException(status_code=404, detail="Veículo não encontrado.")

    # 2. Executa a lógica de negócio via Service Layer
    media_km_l = VeiculoService.calcular_km_por_litro(
        db=db,
        veiculo_id=abastecimento.veiculo_id,
        km_atual=abastecimento.quilometragem,
        litros_abastecidos=abastecimento.litros
    )

    # 3. Persistência dos dados
    novo_abastecimento = models.AbastecimentoDB(
        veiculo_id=abastecimento.veiculo_id,
        quilometragem=abastecimento.quilometragem,
        litros=abastecimento.litros,
        valor_total=abastecimento.valor_total
    )
    
    db.add(novo_abastecimento)
    db.commit()
    db.refresh(novo_abastecimento)
    
    return {
        "mensagem": "Abastecimento registrado com sucesso!",
        "media_consumo_atual_kml": media_km_l,
        "id_abastecimento": novo_abastecimento.id
    }

# --- ROTAS DE DESPESAS ---

@app.post("/despesas")
def registrar_despesa(despesa: schemas.DespesaCreate, db: Session = Depends(get_db)):
    """Registra uma nova despesa (manutenção, imposto, lavagem, etc) para o veículo."""
    
    # Validação: O veículo precisa existir
    veiculo = db.query(models.VeiculoDB).filter(models.VeiculoDB.id == despesa.veiculo_id).first()
    if not veiculo:
        raise HTTPException(status_code=404, detail="Veículo não encontrado.")
    
    nova_despesa = models.DespesaDB(
        veiculo_id=despesa.veiculo_id,
        data_despesa=despesa.data_despesa,
        tipo_despesa=despesa.tipo_despesa,
        descricao=despesa.descricao,
        valor=despesa.valor
    )
    
    db.add(nova_despesa)
    db.commit()
    db.refresh(nova_despesa)
    
    return {"mensagem": "Despesa registrada com sucesso!", "id_despesa": nova_despesa.id}

@app.get("/veiculos/{veiculo_id}/despesas")
def listar_despesas_veiculo(veiculo_id: int, db: Session = Depends(get_db)):
    """Lista todo o histórico de despesas de um veículo específico."""
    despesas = db.query(models.DespesaDB).filter(models.DespesaDB.veiculo_id == veiculo_id).all()
    return despesas

# --- ROTA DE RELATÓRIO (ADICIONADA) ---

@app.get("/relatorios/{veiculo_id}")
def obter_relatorio(veiculo_id: int, db: Session = Depends(get_db)):
    """Calcula indicadores financeiros e de uso para um veículo específico."""
    
    # 1. Verifica se o veículo existe
    veiculo = db.query(models.VeiculoDB).filter(models.VeiculoDB.id == veiculo_id).first()
    if not veiculo:
        raise HTTPException(status_code=404, detail="Veículo não encontrado.")
    
    # 2. Busca todos os abastecimentos deste veículo
    abastecimentos = db.query(models.AbastecimentoDB).filter(models.AbastecimentoDB.veiculo_id == veiculo_id).all()
    
    # 3. Faz o cálculo dos totais
    custo_total = sum(a.valor_total for a in abastecimentos)
    qtd_abastecimentos = len(abastecimentos)
    
    # 4. Retorna no formato que o app espera
    return {
        "veiculo": veiculo.modelo,
        "placa": veiculo.placa,
        "indicadores": {
            "abastecimentos_registrados": qtd_abastecimentos,
            "custo_total_r$": custo_total
        }
    }