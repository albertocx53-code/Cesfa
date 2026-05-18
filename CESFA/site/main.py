from datetime import datetime, timedelta, timezone
from pathlib import Path
 
from fastapi import FastAPI, Depends, HTTPException, Request, Form, Query
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
 
from database import Base, engine, SessionLocal, get_db
Base.metadata.create_all(bind=engine)
from models import Usuario, Aluno, Turma, Disciplina, Nota, Frequencia, Livro 
# --- Config ---
SECRET_KEY = "cesfa-secret-key-2024-mude-em-producao"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480
 
app = FastAPI(title="CESFA Sistema")

 
BASE_DIR = Path(__file__).resolve().parent
static_dir = BASE_DIR / "static"
if static_dir.is_dir():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")
 
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
 
 
# --- DB Init ---
Base.metadata.create_all(bind=engine)
 
 
def seed_data(db: Session):
    if db.query(Usuario).count() > 0:
        return
 
    admin = Usuario(
        nome="Administrador",
        email="admin@cesfa.com",
        senha_hash=pwd_context.hash("admin123"),
        cargo="admin",
    )
    db.add(admin)
 
    turmas = [
        Turma(nome="6o Ano A", turno="Manha", ano=2024),
        Turma(nome="7o Ano A", turno="Manha", ano=2024),
        Turma(nome="8o Ano A", turno="Tarde", ano=2024),
        Turma(nome="9o Ano A", turno="Tarde", ano=2024),
    ]
    db.add_all(turmas)
    db.flush()
 
    disciplinas = [
        Disciplina(nome="Matematica"),
        Disciplina(nome="Portugues"),
        Disciplina(nome="Ciencias"),
        Disciplina(nome="Historia"),
        Disciplina(nome="Geografia"),
    ]
    db.add_all(disciplinas)
    db.flush()
 
    nomes_alunos = [
        "Ana Silva", "Bruno Santos", "Carla Oliveira", "Daniel Souza",
        "Elena Costa", "Felipe Lima", "Gabriela Rocha", "Henrique Alves",
        "Isabela Ferreira", "Joao Nascimento", "Karen Ribeiro", "Lucas Mendes",
        "Mariana Barbosa", "Nicolas Pereira", "Olivia Gomes", "Pedro Araujo",
        "Rafaela Dias", "Samuel Cardoso", "Tatiana Martins", "Victor Nunes",
        "Yasmin Castro", "William Teixeira", "Zara Monteiro", "Arthur Campos",
        "Beatriz Ramos", "Caio Freitas", "Diana Machado", "Eduardo Moreira",
        "Fernanda Vieira", "Gustavo Correia",
    ]
 
    import random
    random.seed(42)
 
    alunos = []
    for i, nome in enumerate(nomes_alunos):
        turma = turmas[i % len(turmas)]
        aluno = Aluno(
            nome=nome,
            matricula=f"2024{i+1:04d}",
            email=f"{nome.lower().replace(' ', '.')}@email.com",
            telefone=f"(99) 9{random.randint(1000,9999)}-{random.randint(1000,9999)}",
            turma_id=turma.id,
        )
        alunos.append(aluno)
    db.add_all(alunos)
    db.flush()
 
    for aluno in alunos:
        for disciplina in disciplinas:
            for bimestre in range(1, 5):
                nota = Nota(
                    aluno_id=aluno.id,
                    disciplina_id=disciplina.id,
                    valor=round(random.uniform(3.0, 10.0), 1),
                    bimestre=bimestre,
                )
                db.add(nota)
 
    today = datetime.now(timezone.utc)
    for aluno in alunos:
        for day_offset in range(60):
            d = today - timedelta(days=day_offset)
            if d.weekday() < 5:
                freq = Frequencia(
                    aluno_id=aluno.id,
                    data=d,
                    presente=random.random() > 0.08,
                )
                db.add(freq)
 
    db.commit()
 
 
_seed_db = SessionLocal()
seed_data(_seed_db)
_seed_db.close()
 
 
# --- Auth helpers ---
def create_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
 
 
def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="Nao autenticado")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalido")
    user = db.query(Usuario).filter(Usuario.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario nao encontrado")
    return user
 
 
# --- Pages ---
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request, "index.html")
 
 
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")
 
 
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request, db: Session = Depends(get_db)):
    try:
        user = get_current_user(request, db)
    except HTTPException:
        return RedirectResponse("/login")
    return templates.TemplateResponse(request, "dashboard.html", {"user": user})
 
 
@app.get("/alunos", response_class=HTMLResponse)
async def alunos_page(request: Request, db: Session = Depends(get_db)):
    try:
        user = get_current_user(request, db)
    except HTTPException:
        return RedirectResponse("/login")
    return templates.TemplateResponse(request, "alunos.html", {"user": user})
 
 
@app.get("/notas", response_class=HTMLResponse)
async def notas_page(request: Request, db: Session = Depends(get_db)):
    try:
        user = get_current_user(request, db)
    except HTTPException:
        return RedirectResponse("/login")
    return templates.TemplateResponse(request, "notas.html", {"user": user})
 
 
@app.get("/boletim", response_class=HTMLResponse)
async def boletim_page(request: Request, db: Session = Depends(get_db)):
    try:
        user = get_current_user(request, db)
    except HTTPException:
        return RedirectResponse("/login")
    return templates.TemplateResponse(request, "boletim.html", {"user": user})
 
 
# --- Auth API ---
@app.post("/api/login")
async def api_login(email: str = Form(...), senha: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.email == email).first()
    if not user or not pwd_context.verify(senha, user.senha_hash):
        raise HTTPException(status_code=401, detail="Credenciais invalidas")
    token = create_token({"sub": user.email, "nome": user.nome})
    response = JSONResponse({"message": "Login realizado", "nome": user.nome})
    response.set_cookie("token", token, httponly=True, max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    return response
 
 
@app.post("/api/logout")
async def api_logout():
    response = JSONResponse({"message": "Logout realizado"})
    response.delete_cookie("token")
    return response
 
 
# --- Alunos API ---
@app.get("/api/alunos")
async def api_listar_alunos(
    request: Request,
    db: Session = Depends(get_db),
    busca: str = Query(default=""),
    turma_id: int = Query(default=0),
):
    get_current_user(request, db)
    query = db.query(Aluno).options(joinedload(Aluno.turma)).filter(Aluno.ativo == True)
    if busca:
        query = query.filter(Aluno.nome.ilike(f"%{busca}%"))
    if turma_id:
        query = query.filter(Aluno.turma_id == turma_id)
    alunos = query.order_by(Aluno.nome).all()
    return [
        {
            "id": a.id,
            "nome": a.nome,
            "matricula": a.matricula,
            "email": a.email,
            "telefone": a.telefone,
            "turma": a.turma.nome if a.turma else None,
            "turma_id": a.turma_id,
        }
        for a in alunos
    ]
 
 
@app.post("/api/alunos")
async def api_criar_aluno(
    request: Request,
    nome: str = Form(...),
    matricula: str = Form(...),
    email: str = Form(default=""),
    telefone: str = Form(default=""),
    turma_id: int = Form(...),
    db: Session = Depends(get_db),
):
    get_current_user(request, db)
    existing = db.query(Aluno).filter(Aluno.matricula == matricula).first()
    if existing:
        raise HTTPException(status_code=400, detail="Matricula ja cadastrada")
    aluno = Aluno(nome=nome, matricula=matricula, email=email, telefone=telefone, turma_id=turma_id)
    db.add(aluno)
    db.commit()
    return {"message": "Aluno cadastrado", "id": aluno.id}
 
 
@app.put("/api/alunos/{aluno_id}")
async def api_atualizar_aluno(
    aluno_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    get_current_user(request, db)
    body = await request.json()
    aluno = db.query(Aluno).filter(Aluno.id == aluno_id).first()
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno nao encontrado")
    for field in ["nome", "matricula", "email", "telefone", "turma_id"]:
        if field in body:
            setattr(aluno, field, body[field])
    db.commit()
    return {"message": "Aluno atualizado"}
 
 
@app.delete("/api/alunos/{aluno_id}")
async def api_deletar_aluno(aluno_id: int, request: Request, db: Session = Depends(get_db)):
    get_current_user(request, db)
    aluno = db.query(Aluno).filter(Aluno.id == aluno_id).first()
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno nao encontrado")
    aluno.ativo = False
    db.commit()
    return {"message": "Aluno removido"}
 
 
# --- Turmas API ---
@app.get("/api/turmas")
async def api_listar_turmas(request: Request, db: Session = Depends(get_db)):
    get_current_user(request, db)
    turmas = db.query(Turma).order_by(Turma.nome).all()
    return [{"id": t.id, "nome": t.nome, "turno": t.turno, "ano": t.ano} for t in turmas]
 
 
# --- Notas API ---
@app.get("/api/notas")
async def api_listar_notas(
    request: Request,
    db: Session = Depends(get_db),
    aluno_id: int = Query(default=0),
    disciplina_id: int = Query(default=0),
    bimestre: int = Query(default=0),
):
    get_current_user(request, db)
    query = db.query(Nota).options(
        joinedload(Nota.aluno), joinedload(Nota.disciplina)
    )
    if aluno_id:
        query = query.filter(Nota.aluno_id == aluno_id)
    if disciplina_id:
        query = query.filter(Nota.disciplina_id == disciplina_id)
    if bimestre:
        query = query.filter(Nota.bimestre == bimestre)
    notas = query.order_by(Nota.aluno_id, Nota.disciplina_id, Nota.bimestre).all()
    return [
        {
            "id": n.id,
            "aluno": n.aluno.nome,
            "aluno_id": n.aluno_id,
            "disciplina": n.disciplina.nome,
            "disciplina_id": n.disciplina_id,
            "valor": n.valor,
            "bimestre": n.bimestre,
        }
        for n in notas
    ]
 
 
@app.post("/api/notas")
async def api_criar_nota(
    request: Request,
    aluno_id: int = Form(...),
    disciplina_id: int = Form(...),
    valor: float = Form(...),
    bimestre: int = Form(...),
    db: Session = Depends(get_db),
):
    get_current_user(request, db)
    nota = Nota(aluno_id=aluno_id, disciplina_id=disciplina_id, valor=valor, bimestre=bimestre)
    db.add(nota)
    db.commit()
    return {"message": "Nota registrada", "id": nota.id}
 
 
@app.get("/api/disciplinas")
async def api_listar_disciplinas(request: Request, db: Session = Depends(get_db)):
    get_current_user(request, db)
    disciplinas = db.query(Disciplina).order_by(Disciplina.nome).all()
    return [{"id": d.id, "nome": d.nome} for d in disciplinas]
 
 
# --- Dashboard API ---
@app.get("/api/dashboard")
async def api_dashboard(request: Request, db: Session = Depends(get_db)):
    get_current_user(request, db)
 
    total_alunos = db.query(Aluno).filter(Aluno.ativo == True).count()
    total_turmas = db.query(Turma).count()
 
    media_geral = db.query(func.avg(Nota.valor)).scalar()
    media_geral = round(float(media_geral or 0), 1)
 
    total_freq = db.query(Frequencia).count()
    presentes = db.query(Frequencia).filter(Frequencia.presente == True).count()
    freq_pct = round((presentes / total_freq * 100) if total_freq else 0, 1)
 
    aprovados = (
        db.query(Aluno.id)
        .join(Nota)
        .group_by(Aluno.id)
        .having(func.avg(Nota.valor) >= 7)
        .count()
    )
    reprovados = total_alunos - aprovados
 
    notas_por_disciplina = (
        db.query(Disciplina.nome, func.avg(Nota.valor))
        .join(Nota)
        .group_by(Disciplina.nome)
        .order_by(Disciplina.nome)
        .all()
    )
 
    notas_por_bimestre = (
        db.query(Nota.bimestre, func.avg(Nota.valor))
        .group_by(Nota.bimestre)
        .order_by(Nota.bimestre)
        .all()
    )
 
    top_alunos = (
        db.query(Aluno.nome, func.avg(Nota.valor).label("media"))
        .join(Nota)
        .group_by(Aluno.id)
        .order_by(func.avg(Nota.valor).desc())
        .limit(10)
        .all()
    )
 
    return {
        "total_alunos": total_alunos,
        "total_turmas": total_turmas,
        "media_geral": media_geral,
        "frequencia": freq_pct,
        "aprovados": aprovados,
        "reprovados": reprovados,
        "notas_por_disciplina": [
            {"disciplina": nome, "media": round(float(media), 1)}
            for nome, media in notas_por_disciplina
        ],
        "notas_por_bimestre": [
            {"bimestre": f"{bim}o Bimestre", "media": round(float(media), 1)}
            for bim, media in notas_por_bimestre
        ],
        "top_alunos": [
            {"nome": nome, "media": round(float(media), 1)}
            for nome, media in top_alunos
        ],
    }
 
 
# --- Boletim API ---
@app.get("/api/boletim/{aluno_id}")
async def api_boletim(aluno_id: int, request: Request, db: Session = Depends(get_db)):
    get_current_user(request, db)
    aluno = db.query(Aluno).options(joinedload(Aluno.turma)).filter(Aluno.id == aluno_id).first()
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno nao encontrado")
 
    notas = (
        db.query(Nota)
        .options(joinedload(Nota.disciplina))
        .filter(Nota.aluno_id == aluno_id)
        .order_by(Nota.disciplina_id, Nota.bimestre)
        .all()
    )
 
    disciplinas = {}
    for nota in notas:
        nome = nota.disciplina.nome
        if nome not in disciplinas:
            disciplinas[nome] = {"bimestres": {}, "media": 0}
        disciplinas[nome]["bimestres"][nota.bimestre] = nota.valor
 
    for disc in disciplinas.values():
        vals = list(disc["bimestres"].values())
        disc["media"] = round(sum(vals) / len(vals), 1) if vals else 0
 
    total_freq = db.query(Frequencia).filter(Frequencia.aluno_id == aluno_id).count()
    presentes = db.query(Frequencia).filter(
        Frequencia.aluno_id == aluno_id, Frequencia.presente == True
    ).count()
    freq_pct = round((presentes / total_freq * 100) if total_freq else 0, 1)
 
    return {
        "aluno": {
            "id": aluno.id,
            "nome": aluno.nome,
            "matricula": aluno.matricula,
            "turma": aluno.turma.nome if aluno.turma else None,
        },
        "disciplinas": disciplinas,
        "frequencia": freq_pct,
    }


# =========================
# PÁGINA LIVROS
# =========================

@app.get("/livros", response_class=HTMLResponse)
async def livros_page(request: Request, db: Session = Depends(get_db)):
    try:
        user = get_current_user(request, db)
    except HTTPException:
        return RedirectResponse("/login")

    return templates.TemplateResponse(
        "livros.html",
        {
            "request": request,
            "user": user
        }
    )


# =========================
# API LIVROS
# =========================

@app.get("/api/livros")
async def api_listar_livros(
    request: Request,
    db: Session = Depends(get_db)
):
    get_current_user(request, db)

    livros = db.query(Livro).all()

    return [
        {
            "id": livro.id,
            "titulo": livro.titulo,
            "autor": livro.autor,
            "categoria": livro.categoria,
            "quantidade": livro.quantidade,
            "descricao": livro.descricao,
            "capa": livro.capa,
        }
        for livro in livros
    ]


@app.post("/api/livros")
async def api_criar_livro(
    request: Request,
    titulo: str = Form(...),
    autor: str = Form(...),
    categoria: str = Form(...),
    quantidade: int = Form(...),
    descricao: str = Form(default=""),
    capa: str = Form(default=""),
    db: Session = Depends(get_db)
):
    get_current_user(request, db)

    livro = Livro(
        titulo=titulo,
        autor=autor,
        categoria=categoria,
        quantidade=quantidade,
        descricao=descricao,
        capa=capa
    )

    db.add(livro)
    db.commit()

    return {
        "message": "Livro cadastrado com sucesso"
    }


@app.delete("/api/livros/{livro_id}")
async def api_excluir_livro(
    livro_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    get_current_user(request, db)

    livro = db.query(Livro).filter(Livro.id == livro_id).first()

    if not livro:
        raise HTTPException(status_code=404, detail="Livro não encontrado")

    db.delete(livro)
    db.commit()

    return {
        "message": "Livro removido"
    }