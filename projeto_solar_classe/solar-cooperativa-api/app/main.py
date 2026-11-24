from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db

app = FastAPI(
    title="Cooperativa Solar API",
    description="API CRUD de gestão de unidades consumidoras, contratos e créditos de kWh.",
    version="1.0.0",
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/cooperados", response_model=list[schemas.CooperadoOut])
def listar_cooperados(
    nome: str | None = Query(default=None, description="Filtro parcial por nome fantasia"),
    db: Session = Depends(get_db),
):
    query = db.query(models.Cooperado)
    if nome:
        query = query.filter(models.Cooperado.nome_fantasia.ilike(f"%{nome}%"))
    return query.all()


@app.get("/contratos-energia/{cooperado_id}", response_model=list[schemas.ContratoOut])
def buscar_contratos_por_cooperado(cooperado_id: int, db: Session = Depends(get_db)):
    contratos = (
        db.query(models.ContratoEnergia)
        .filter(models.ContratoEnergia.cooperado_id == cooperado_id)
        .all()
    )
    if not contratos:
        raise HTTPException(status_code=404, detail="Nenhum contrato encontrado para este cooperado.")
    return contratos


@app.patch("/contratos-energia/{contrato_id}", response_model=schemas.ContratoOut)
def atualizar_modalidade_contrato(
    contrato_id: int,
    payload: schemas.ContratoUpdateModalidade,
    db: Session = Depends(get_db),
):
    contrato = db.query(models.ContratoEnergia).filter(models.ContratoEnergia.id == contrato_id).first()
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato não encontrado.")

    contrato.modalidade_cota = payload.modalidade_cota
    contrato.cota_mensal_kwh = payload.cota_mensal_kwh
    db.commit()
    db.refresh(contrato)
    return contrato


@app.patch("/contratos-energia/{contrato_id}/creditos", response_model=schemas.ContratoOut)
def adicionar_creditos_energia(
    contrato_id: int,
    payload: schemas.ContratoAddCreditos,
    db: Session = Depends(get_db),
):
    contrato = db.query(models.ContratoEnergia).filter(models.ContratoEnergia.id == contrato_id).first()
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato não encontrado.")

    contrato.saldo_creditos_kwh += payload.creditos_kwh
    db.commit()
    db.refresh(contrato)
    return contrato


@app.post("/auditoria-regulatoria", response_model=schemas.AuditoriaOut, status_code=201)
def registrar_auditoria(payload: schemas.AuditoriaCreate, db: Session = Depends(get_db)):
    contrato = db.query(models.ContratoEnergia).filter(models.ContratoEnergia.id == payload.contrato_id).first()
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato informado não existe.")

    registro = models.AuditoriaRegulatoria(**payload.model_dump())
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return registro


@app.get("/auditoria-regulatoria", response_model=list[schemas.AuditoriaOut])
def listar_auditorias(contrato_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(models.AuditoriaRegulatoria)
    if contrato_id:
        query = query.filter(models.AuditoriaRegulatoria.contrato_id == contrato_id)
    return query.order_by(models.AuditoriaRegulatoria.id.desc()).all()