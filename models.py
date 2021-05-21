from app import db
from datetime import datetime
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Boolean,
)


class Genre(db.Model):
    __tablename__ = "Genre"
    id = Column(Integer, primary_key=True)
    name = Column(String)


# Artist:Genre :: N:N
artist_genre = db.Table(
    "Artist_Genre",
    Column("genre_id", Integer, ForeignKey("Genre.id"), primary_key=True),
    Column("artist_id", Integer, ForeignKey("Artist.id"), primary_key=True),
)

# Venue:Genre :: N:N
venue_genre = db.Table(
    "Venue_Genre",
    Column("genre_id", Integer, ForeignKey("Genre.id"), primary_key=True),
    Column("venue_id", Integer, ForeignKey("Venue.id"), primary_key=True),
)


class Venue(db.Model):
    __tablename__ = "Venue"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    city = Column(String(120))
    state = Column(String(120))
    address = Column(String(120))
    phone = Column(String(120))
    image_link = Column(String(500))
    facebook_link = Column(String(120))
    website = Column(String(120))
    seeking_talent = Column(Boolean, default=False)
    seeking_description = Column(String(120))

    genres = db.relationship(
        "Genre", secondary=venue_genre, backref=db.backref("venues")
    )
    shows = db.relationship("Show", backref="Venue", lazy=True)

    def __repr__(self):
        return f"<Venue {self.id} {self.name}>"


class Artist(db.Model):
    __tablename__ = "Artist"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    city = Column(String(120))
    state = Column(String(120))
    phone = Column(String(120))
    image_link = Column(String(500))
    facebook_link = Column(String(120))
    website = Column(String(120))
    seeking_venue = Column(Boolean, default=False)
    seeking_description = Column(String(120))

    genres = db.relationship(
        "Genre", secondary=artist_genre, backref=db.backref("Artists")
    )
    shows = db.relationship("Show", backref="Artist", lazy=True)

    def __repr__(self):
        return f"<Artist {self.id} {self.name}>"


class Show(db.Model):
    __tablename__ = "Show"
    id = Column(Integer, primary_key=True)
    start_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    artist_id = Column(Integer, ForeignKey("Artist.id"), nullable=False)
    venue_id = Column(Integer, ForeignKey("Venue.id"), nullable=False)

    def __repr__(self):
        return f"<Show {self.id} {self.start_time} artist_id={self.artist_id} venue_id={self.venue_id}>"
