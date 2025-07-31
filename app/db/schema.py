from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Define a dynamic table for team rosters and stats
def create_team_tables(team_id):
    class Roster(Base):
        __tablename__ = f"team_{team_id}_roster"

        id = Column(Integer, primary_key=True, nullable=False)
        full_name = Column(String, nullable=False)
        position = Column(String, nullable=False)
        is_pitcher = Column(Boolean, nullable=False)
        bats = Column(String, nullable=True)
        throws = Column(String, nullable=True)

    Roster.__name__ = f"Roster_{team_id}"

    class Stats(Base):
        __tablename__ = f"team_{team_id}_stats"

        player_id = Column(Integer, primary_key=True, nullable=False)
        season = Column(Integer, primary_key=True, nullable=False)
        avg = Column(Float, nullable=True)
        ops = Column(Float, nullable=True)
        hr = Column(Integer, nullable=True)
        rbi = Column(Integer, nullable=True)
        k_pct = Column(Float, nullable=True)
        contact_pct = Column(Float, nullable=True)
        whiff_pct = Column(Float, nullable=True)
        o_swing_pct = Column(Float, nullable=True)
        z_contact_pct = Column(Float, nullable=True)

    Stats.__name__ = f"Stats_{team_id}"

    return Roster, Stats

class Team(Base):
    __tablename__ = 'teams'

    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    abbreviation = Column(String, nullable=False)
    league = Column(String, nullable=False)
    division = Column(String, nullable=False)

    players = relationship('Player', back_populates='team')

class Player(Base):
    __tablename__ = 'players'

    id = Column(Integer, primary_key=True, nullable=False)
    full_name = Column(String, nullable=False)
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    position = Column(String, nullable=False)
    is_pitcher = Column(Boolean, nullable=False)
    bats = Column(String, nullable=False)
    throws = Column(String, nullable=False)

    team = relationship('Team', back_populates='players')
    hitter_stats = relationship('HitterStats', back_populates='player', cascade='all, delete-orphan')
    pitcher_stats = relationship('PitcherStats', back_populates='player', cascade='all, delete-orphan')

class HitterStats(Base):
    __tablename__ = 'hitter_stats'

    player_id = Column(Integer, ForeignKey('players.id'), primary_key=True, nullable=False)
    season = Column(Integer, primary_key=True, nullable=False)
    avg = Column(Float, nullable=True)
    ops = Column(Float, nullable=True)
    hr = Column(Integer, nullable=True)
    rbi = Column(Integer, nullable=True)
    k_pct = Column(Float, nullable=True)
    contact_pct = Column(Float, nullable=True)
    whiff_pct = Column(Float, nullable=True)
    o_swing_pct = Column(Float, nullable=True)
    z_contact_pct = Column(Float, nullable=True)

    player = relationship('Player', back_populates='hitter_stats')

class PitcherStats(Base):
    __tablename__ = 'pitcher_stats'

    player_id = Column(Integer, ForeignKey('players.id'), primary_key=True, nullable=False)
    season = Column(Integer, primary_key=True, nullable=False)
    era = Column(Float, nullable=True)
    whip = Column(Float, nullable=True)
    k_pct = Column(Float, nullable=True)
    k9 = Column(Float, nullable=True)
    whiff_pct = Column(Float, nullable=True)
    strikeout_walk_ratio = Column(Float, nullable=True)

    player = relationship('Player', back_populates='pitcher_stats')