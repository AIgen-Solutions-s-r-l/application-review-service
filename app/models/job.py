from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# Definisci la base SQLAlchemy
Base = declarative_base()

# Definisci i modelli del database secondo la tua struttura

class Company(Base):
    __tablename__ = 'Companies'
    company_id = Column(Integer, primary_key=True, autoincrement=True)
    company_name = Column(String, nullable=False)

    jobs = relationship('Job', back_populates='company')

    def __str__(self):
        return f"Company(id={self.company_id}, name={self.company_name})"

class Location(Base):
    __tablename__ = 'Locations'
    location_id = Column(Integer, primary_key=True, autoincrement=True)
    location = Column(String, nullable=False)  # Ad esempio, "Amsterdam, North Holland, Netherlands"

    jobs = relationship('Job', back_populates='location')

    def __str__(self):
        return f"Location(id={self.location_id}, location='{self.location}')"

class Job(Base):
    __tablename__ = 'Jobs'
    job_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    is_remote = Column(Boolean)
    workplace_type = Column(String)
    posted_date = Column(DateTime)
    job_state = Column(String)
    description = Column(Text)
    apply_link = Column(String)

    company_id = Column(Integer, ForeignKey('Companies.company_id'), nullable=False)
    location_id = Column(Integer, ForeignKey('Locations.location_id'), nullable=False)

    company = relationship('Company', back_populates='jobs')
    location = relationship('Location', back_populates='jobs')

    def __str__(self):
        return (f"Job(id={self.job_id}, title='{self.title}', remote={self.is_remote}, "
                f"workplace_type='{self.workplace_type}', posted_date={self.posted_date}, "
                f"state='{self.job_state}', company_id={self.company_id}, location_id={self.location_id})")