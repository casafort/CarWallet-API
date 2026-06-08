from sqlalchemy.orm import Session
import models

class VeiculoService:
    @staticmethod
    def calcular_km_por_litro(db: Session, veiculo_id: int, km_atual: float, litros_abastecidos: float):
        # Busca o último abastecimento deste veículo específico
        ultimo_abastecimento = db.query(models.AbastecimentoDB)\
            .filter(models.AbastecimentoDB.veiculo_id == veiculo_id)\
            .order_by(models.AbastecimentoDB.id.desc()).first()

        # Se for o primeiro abastecimento, não tem como calcular a média
        if not ultimo_abastecimento:
            return 0.0 

        # Calcula a distância percorrida
        km_rodados = km_atual - ultimo_abastecimento.quilometragem
        
        # Evita divisão por zero ou números negativos
        if km_rodados <= 0 or litros_abastecidos <= 0:
            return 0.0 

        # Calcula a média real
        media = km_rodados / litros_abastecidos
        return round(media, 2)
    