from pydantic import BaseModel
from typing import TypeVar
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, DateTime, Numeric

T = TypeVar("T", bound=BaseModel)  # Bind T to Pydantic BaseModel
Base = declarative_base()


class Zampapagentinvoices(Base):
    __tablename__ = "ZAMPAPAGENTINVOICES"
    # __table_args__ = {'schema': 'DEMO'}
    id = Column("ID", String, primary_key=True)
    invoicedate = Column("INVOICEDATE", DateTime)
    duedate = Column("DUEDATE", DateTime)
    amount = Column("AMOUNT", Numeric(38, 0))
    invoice_metadata = Column("METADATA", String)
    status = Column("STATUS", String)
    currency = Column("CURRENCY", String)
    vendorid = Column("VENDORID", String)
    gcspath = Column("GCSPATH", String)
    organizationid = Column("ORGANIZATIONID", String)
    invoiceid = Column("INVOICEID", String)
    description = Column("DESCRIPTION", String)
    invoicebucketpath = Column("INVOICEBUCKETPATH", String)
    contractid = Column("CONTRACTID", String)

    def to_dict(self):
        return {
            "id": self.id,
            "invoicedate": self.invoicedate,
            "duedate": self.duedate,
            "amount": self.amount,
            "invoice_metadata": self.invoice_metadata,
            "status": self.status,
            "currency": self.currency,
            "vendorid": self.vendorid,
            "gcspath": self.gcspath,
            "organizationid": self.organizationid,
            "invoiceid": self.invoiceid,
            "description": self.description,
            "invoicebucketpath": self.invoicebucketpath,
            "contractid": self.contractid,
        }
