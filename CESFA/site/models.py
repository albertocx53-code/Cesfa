from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)

    nome = Column(String, nullable=False)

    email = Column(String, unique=True, nullable=False)

    senha_hash = Column(String, nullable=False)

    cargo = Column(String, default="admin")


class Turma(Base):
    __tablename__ = "turmas"

    id = Column(Integer, primary_key=True, index=True)

    nome = Column(String, nullable=False)

    turno = Column(String)

    ano = Column(Integer)

    alunos = relationship("Aluno", back_populates="turma")


class Aluno(Base):
    __tablename__ = "alunos"

    id = Column(Integer, primary_key=True, index=True)

    nome = Column(String, nullable=False)

    matricula = Column(String, unique=True, nullable=False)

    email = Column(String)

    telefone = Column(String)

    ativo = Column(Boolean, default=True)

    turma_id = Column(Integer, ForeignKey("turmas.id"))

    turma = relationship("Turma", back_populates="alunos")

    notas = relationship("Nota", back_populates="aluno")

    frequencias = relationship("Frequencia", back_populates="aluno")


class Disciplina(Base):
    __tablename__ = "disciplinas"

    id = Column(Integer, primary_key=True, index=True)

    nome = Column(String, nullable=False)

    notas = relationship("Nota", back_populates="disciplina")


class Nota(Base):
    __tablename__ = "notas"

    id = Column(Integer, primary_key=True, index=True)

    aluno_id = Column(Integer, ForeignKey("alunos.id"))

    disciplina_id = Column(Integer, ForeignKey("disciplinas.id"))

    valor = Column(Float)

    bimestre = Column(Integer)

    aluno = relationship("Aluno", back_populates="notas")

    disciplina = relationship("Disciplina", back_populates="notas")


class Frequencia(Base):
    __tablename__ = "frequencias"

    id = Column(Integer, primary_key=True, index=True)

    aluno_id = Column(Integer, ForeignKey("alunos.id"))

    data = Column(DateTime, default=datetime.utcnow)

    presente = Column(Boolean, default=True)

    aluno = relationship("Aluno", back_populates="frequencias")


class Livro(Base):
    __tablename__ = "livros"

    id = Column(Integer, primary_key=True, index=True)

    titulo = Column(String, nullable=False)

    autor = Column(String)

    categoria = Column(String)

    quantidade = Column(Integer, default=1)

    descricao = Column(String)

    capa = Column(String)
