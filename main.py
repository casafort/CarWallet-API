from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime
import models
import schemas
from services import VeiculoService

# Inicialização do App
app = FastAPI(title="CarWallet API - AV2")

# Função auxiliar para gerenciar a sessão do banco de dados
def get_db():
    db = models.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "CarWallet API está online e funcional!"}

@app.get("/limpar-banco")
def limpar_banco():
    """Rota de emergência para resetar o banco (Útil para apresentações)"""
    models.Base.metadata.drop_all(bind=models.engine)
    models.Base.metadata.create_all(bind=models.engine)
    return {"mensagem": "Banco de dados zerado e atualizado com sucesso!"}

# --- ROTAS DE VEÍCULOS ---

@app.get("/veiculos")
def listar_veiculos(db: Session = Depends(get_db)):
    """Retorna a lista de todos os veículos cadastrados."""
    veiculos = db.query(models.VeiculoDB).all()
    return veiculos

@app.post("/veiculos")
def cadastrar_veiculo(veiculo: schemas.VeiculoCreate, db: Session = Depends(get_db)):
    """Cadastra um novo veículo desmembrado e com odômetro inicial."""
    veiculo_existente = db.query(models.VeiculoDB).filter(models.VeiculoDB.placa == veiculo.placa).first()
    if veiculo_existente:
        raise HTTPException(status_code=400, detail="Esta placa já está cadastrada.")
    
    novo_veiculo = models.VeiculoDB(
        placa=veiculo.placa,
        marca=veiculo.marca,
        modelo=veiculo.modelo,
        ano=veiculo.ano,
        tipo=veiculo.tipo,
        combustivel=veiculo.combustivel,
        odometro_inicial=veiculo.odometro_inicial
    )
    
    db.add(novo_veiculo)
    db.commit()
    db.refresh(novo_veiculo)
    
    return {"mensagem": "Veículo salvo com sucesso!", "id_gerado": novo_veiculo.id}

# UX Inteligente - Busca o último odômetro para sugerir na tela do app
@app.get("/veiculos/{veiculo_id}/ultimo-odometro")
def obter_ultimo_odometro(veiculo_id: int, db: Session = Depends(get_db)):
    """Retorna a maior quilometragem já registrada para o veículo ou o odômetro inicial."""
    veiculo = db.query(models.VeiculoDB).filter(models.VeiculoDB.id == veiculo_id).first()
    if not veiculo:
        raise HTTPException(status_code=404, detail="Veículo não encontrado.")

    # Busca o maior odômetro em abastecimentos
    max_odo_abast = db.query(func.max(models.AbastecimentoDB.quilometragem)).filter(models.AbastecimentoDB.veiculo_id == veiculo_id).scalar() or 0.0

    # Busca o maior odômetro em despesas (ignora os nulos)
    max_odo_desp = db.query(func.max(models.DespesaDB.odometro_atual)).filter(models.DespesaDB.veiculo_id == veiculo_id).scalar() or 0.0

    ultimo_registrado = max(max_odo_abast, max_odo_desp)

    # Se não tiver nenhum registro de gasto, devolve o ponto de partida do cadastro
    odometro_final = max(ultimo_registrado, veiculo.odometro_inicial)

    return {"ultimo_odometro": odometro_final}

# --- ROTAS DE ABASTECIMENTO ---

@app.post("/abastecimentos")
def registrar_abastecimento(abastecimento: schemas.AbastecimentoCreate, db: Session = Depends(get_db)):
    """Registra um abastecimento e calcula a média."""
    veiculo = db.query(models.VeiculoDB).filter(models.VeiculoDB.id == abastecimento.veiculo_id).first()
    if not veiculo:
        raise HTTPException(status_code=404, detail="Veículo não encontrado.")

    media_km_l = VeiculoService.calcular_km_por_litro(
        db=db,
        veiculo_id=abastecimento.veiculo_id,
        km_atual=abastecimento.quilometragem,
        litros_abastecidos=abastecimento.litros
    )

    novo_abastecimento = models.AbastecimentoDB(
        veiculo_id=abastecimento.veiculo_id,
        quilometragem=abastecimento.quilometragem,
        litros=abastecimento.litros,
        valor_total=abastecimento.valor_total,
        # Captura a data retroativa se o Android enviar, senão usa a data atual
        data_abastecimento=getattr(abastecimento, "data_abastecimento", None)
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
    """Registra uma despesa genérica utilizando o novo sistema de Categorias."""
    veiculo = db.query(models.VeiculoDB).filter(models.VeiculoDB.id == despesa.veiculo_id).first()
    if not veiculo:
        raise HTTPException(status_code=404, detail="Veículo não encontrado.")
    
    nova_despesa = models.DespesaDB(
        veiculo_id=despesa.veiculo_id,
        data_despesa=despesa.data_despesa,
        tipo_despesa=despesa.tipo_despesa,
        valor=despesa.valor,
        observacao=despesa.observacao,
        odometro_atual=despesa.odometro_atual
    )
    
    db.add(nova_despesa)
    db.commit()
    db.refresh(nova_despesa)
    
    return {"mensagem": "Despesa registrada com sucesso!", "id_despesa": nova_despesa.id}

@app.get("/veiculos/{veiculo_id}/despesas")
def listar_despesas_veiculo(veiculo_id: int, db: Session = Depends(get_db)):
    """Lista o extrato de todas as despesas."""
    despesas = db.query(models.DespesaDB).filter(models.DespesaDB.veiculo_id == veiculo_id).all()
    return despesas

# --- ROTA DE RELATÓRIO COM FILTROS E EXTRATO UNIFICADO ---

@app.get("/relatorios/{veiculo_id}")
def obter_relatorio(veiculo_id: int, mes: Optional[int] = None, ano: Optional[int] = None, db: Session = Depends(get_db)):
    """Retorna o extrato unificado e os totais filtrados por mês/ano."""
    veiculo = db.query(models.VeiculoDB).filter(models.VeiculoDB.id == veiculo_id).first()
    if not veiculo:
        raise HTTPException(status_code=404, detail="Veículo não encontrado.")
    
    hoje = datetime.now()
    mes_alvo = mes if mes else hoje.month
    ano_alvo = ano if ano else hoje.year

    abastecimentos = db.query(models.AbastecimentoDB).filter(models.AbastecimentoDB.veiculo_id == veiculo_id).all()
    despesas = db.query(models.DespesaDB).filter(models.DespesaDB.veiculo_id == veiculo_id).all()
    
    extrato = []
    
    # Adiciona Abastecimentos na Linha do Tempo
    for a in abastecimentos:
        data_item = a.data_abastecimento or hoje
        if data_item.month == mes_alvo and data_item.year == ano_alvo:
            extrato.append({
                "id": f"abast_{a.id}",
                "tipo": "Combustível",
                "valor": a.valor_total,
                "data": data_item.isoformat(),
                "observacao": f"{a.litros} Litros"
            })

    # Adiciona Outras Despesas na Linha do Tempo
    for d in despesas:
        data_item = d.data_despesa or hoje
        if data_item.month == mes_alvo and data_item.year == ano_alvo:
            # Extrai o valor String do Enum para o JSON
            tipo_str = d.tipo_despesa.value if hasattr(d.tipo_despesa, 'value') else str(d.tipo_despesa)
            extrato.append({
                "id": f"desp_{d.id}",
                "tipo": tipo_str,
                "valor": d.valor,
                "data": data_item.isoformat(),
                "observacao": d.observacao or ""
            })

    # Ordena da data mais recente para a mais antiga
    extrato.sort(key=lambda x: x["data"], reverse=True)
    custo_total = sum(item["valor"] for item in extrato)

    return {
        "veiculo": veiculo.modelo,
        "mes": mes_alvo,
        "ano": ano_alvo,
        "custo_total": custo_total,
        "extrato": extrato
    }