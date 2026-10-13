import os
from typing import List, Optional, Dict, Any
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Integer,
    Numeric,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from datetime import datetime
import uuid

Base = declarative_base()


class CompanyModel(Base):
    __tablename__ = "companies"
    id = Column(String(64), primary_key=True)
    name = Column(String(255), nullable=False)
    ticker = Column(String(16), unique=True)
    country = Column(String(64), default="US")
    reporting_currency = Column(String(10), default="USD")
    sector = Column(String(128))
    industry = Column(String(128))
    created_at = Column(DateTime, default=datetime.utcnow)


class DocumentModel(Base):
    __tablename__ = "documents"
    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(64), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    fiscal_year = Column(Integer, nullable=False)
    period_type = Column(String(16), default="FY")
    document_type = Column(String(64), default="annual_report")
    original_filename = Column(String(255), nullable=False)
    storage_path = Column(Text, nullable=False)
    status = Column(String(32), default="uploaded")
    total_pages = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class FinancialSourceModel(Base):
    __tablename__ = "financial_sources"
    id = Column(String(128), primary_key=True)
    document_id = Column(String(64), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    page_number = Column(Integer, nullable=False)
    section_name = Column(String(128))
    table_identifier = Column(String(128))
    raw_snippet = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class FinancialFactModel(Base):
    __tablename__ = "financial_facts"
    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(64), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(String(64), ForeignKey("documents.id", ondelete="SET NULL"))
    metric = Column(String(64), nullable=False)
    value = Column(Numeric(24, 4), nullable=False)
    currency = Column(String(10), default="USD")
    unit = Column(String(32), default="USD")
    scale = Column(String(32), default="exact")
    fiscal_year = Column(Integer, nullable=False)
    period_type = Column(String(16), default="FY")
    source_id = Column(String(128))
    source_page = Column(Integer)
    statement_type = Column(String(64))
    validation_status = Column(String(32), default="pending")
    is_restated = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("company_id", "fiscal_year", "period_type", "metric", "is_restated", name="uq_comp_fact"),
    )


class DatabaseService:
    """Manages relational database sessions and operations."""

    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or os.getenv("DATABASE_URL", "sqlite:///./financial_rag.db")
        self.engine = create_engine(self.db_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.create_tables()

    def create_tables(self):
        Base.metadata.create_all(bind=self.engine)

    def get_session(self) -> Session:
        return self.SessionLocal()

    def save_facts(self, facts: List[Any], document_id: Optional[str] = None) -> int:
        session = self.get_session()
        count = 0
        try:
            # Deduplicate facts in-memory by unique constraint key
            # (company_id, fiscal_year, period_type, metric, is_restated)
            deduped_facts: Dict[Any, Any] = {}
            for fact in facts:
                key = (
                    fact.company_id,
                    fact.fiscal_year,
                    fact.period_type,
                    fact.metric,
                    fact.is_restated,
                )
                deduped_facts[key] = fact

            # Ensure company and document foreign keys exist if foreign keys are enabled
            unique_companies = {fact.company_id for fact in deduped_facts.values()}
            for comp_id in unique_companies:
                company = session.query(CompanyModel).filter(CompanyModel.id == comp_id).first()
                if not company:
                    session.add(CompanyModel(id=comp_id, name=comp_id.replace("_", " ").title()))
            
            target_doc_id = document_id or (facts[0].document_id if facts else None)
            if target_doc_id:
                doc = session.query(DocumentModel).filter(DocumentModel.id == target_doc_id).first()
                if not doc:
                    first_comp = facts[0].company_id if facts else "unknown"
                    session.add(DocumentModel(
                        id=target_doc_id,
                        company_id=first_comp,
                        fiscal_year=facts[0].fiscal_year if facts else 2025,
                        original_filename="uploaded_document.pdf",
                        storage_path="",
                    ))
            session.flush()

            for fact in deduped_facts.values():
                # Upsert / check existing
                existing = session.query(FinancialFactModel).filter(
                    FinancialFactModel.company_id == fact.company_id,
                    FinancialFactModel.fiscal_year == fact.fiscal_year,
                    FinancialFactModel.period_type == fact.period_type,
                    FinancialFactModel.metric == fact.metric,
                    FinancialFactModel.is_restated == fact.is_restated,
                ).first()

                if existing:
                    existing.value = fact.value
                    existing.source_page = fact.source_page
                    existing.validation_status = (
                        fact.validation_status.value
                        if hasattr(fact.validation_status, "value")
                        else str(fact.validation_status)
                    )
                    existing.scale = (
                        fact.scale.value
                        if hasattr(fact.scale, "value")
                        else str(fact.scale)
                    )
                    existing.source_id = fact.source_id
                    existing.statement_type = (
                        fact.statement_type.value
                        if hasattr(fact.statement_type, "value")
                        else str(fact.statement_type)
                    )
                else:
                    new_fact = FinancialFactModel(
                        id=str(fact.id),
                        company_id=fact.company_id,
                        document_id=target_doc_id,
                        metric=fact.metric,
                        value=fact.value,
                        currency=fact.currency,
                        unit=fact.unit,
                        scale=(
                            fact.scale.value
                            if hasattr(fact.scale, "value")
                            else str(fact.scale)
                        ),
                        fiscal_year=fact.fiscal_year,
                        period_type=fact.period_type,
                        source_id=fact.source_id,
                        source_page=fact.source_page,
                        statement_type=(
                            fact.statement_type.value
                            if hasattr(fact.statement_type, "value")
                            else str(fact.statement_type)
                        ),
                        validation_status=(
                            fact.validation_status.value
                            if hasattr(fact.validation_status, "value")
                            else str(fact.validation_status)
                        ),
                        is_restated=fact.is_restated,
                    )
                    session.add(new_fact)
                count += 1
            session.commit()
            return count
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def query_facts(
        self,
        company_id: str,
        fiscal_years: Optional[List[int]] = None,
        metrics: Optional[List[str]] = None,
        verified_only: bool = True,
    ) -> List[Dict[str, Any]]:
        session = self.get_session()
        try:
            query = session.query(FinancialFactModel).filter(
                FinancialFactModel.company_id == company_id
            )
            if fiscal_years:
                query = query.filter(FinancialFactModel.fiscal_year.in_(fiscal_years))
            if metrics:
                query = query.filter(FinancialFactModel.metric.in_(metrics))
            if verified_only:
                query = query.filter(FinancialFactModel.validation_status == "verified")

            results = query.all()
            return [
                {
                    "id": r.id,
                    "company_id": r.company_id,
                    "fiscal_year": r.fiscal_year,
                    "period_type": r.period_type,
                    "metric": r.metric,
                    "value": float(r.value),
                    "currency": r.currency,
                    "unit": r.unit,
                    "scale": r.scale,
                    "source_id": r.source_id,
                    "source_page": r.source_page,
                    "statement_type": r.statement_type,
                    "validation_status": r.validation_status,
                }
                for r in results
            ]
        finally:
            session.close()
