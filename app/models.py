import os
import config as Config

import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSON

ENVIRONMENT = os.getenv("ENVIRONMENT", "dry")
config = Config.get_config(ENVIRONMENT)

Base = declarative_base()
engine = create_engine(config.POSTGRES_CONNECT_STRING, echo=False)


# It doesn't look like we'll be able to report back to the application
# about the real id of the Opportunity. Therefore we'll use the tag to associate
# other records with opportunities.
# (too many db queries to establish this. Could memoize. Dict is threadsafe?)


class Opportunity(Base):
    """
    Each path find_cycles returns is an opportunity, we only insert the
    opportunities we find
    """

    __tablename__ = "opportunity"
    id = Column(Integer, primary_key=True)
    opportunity_tag = Column(String(36), unique=True)

    # By storing the application version we can see our improvements over time
    version = Column(String(16))

    path = Column(JSON(512))

    timestamp = Column(Float)
    required_fiat_quantity = Column(Float)
    projected_profit = Column(Float)
    projected_profit_percent = Column(Float)


class Event(Base):
    """
    Log all events which happen along with timestamps and opportunity id
    """

    __tablename__ = "event"

    id = Column(Integer, primary_key=True)

    event_type = Column(String(100))
    timestamp = Column(Float)

    opportunity_tag = Column(String(36), unique=True)


class Trade(Base):
    """
    Log all trades for analysis and tax reasons.
    """

    __tablename__ = "trade"

    id = Column(Integer, primary_key=True)
    timestamp = Column(Float)

    exchange = Column(Integer)
    market = Column(String(12))
    order_type = Column(String(6))
    side = Column(String(4))

    price = Column(Float)
    quantity = Column(Float)
    quantity_currency = Column(String(5))
    fills = Column(JSON(200))

    status = Column(String(10))
    exchange_order_id = Column(String(64))

    opportunity_tag = Column(String(36), unique=True)


class OpportunityResult(Base):
    """
    Log all opportunity results for analysis and tax reasons.
    """

    __tablename__ = "opportunity_result"
    id = Column(Integer, primary_key=True)
    actual_profit = Column(Float)

    opportunity_tag = Column(String(36), unique=True)


Base.metadata.create_all(engine)
make_livermore_session = sessionmaker(bind=engine)
