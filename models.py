"""
models.py
This defines all models used in chatbot app
"""

from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, ARRAY, Table
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from db import Base
from enum import Enum
from sqlalchemy.sql import func

# *** AUTH MODELS ***
class LoginRequest(BaseModel):
    email: str
    password: str

class UserInfoDisplay(BaseModel):
    email: str
    first_name: str 
    last_name: str

    model_config = ConfigDict(from_attributes=True)

# *** ONBOARDING ENUMS ***
class PrimaryGoal(str, Enum):
    IMPROVE_SKILL = "improve_skill"
    BEST_ON_TEAM = "best_on_team"
    COLLEGE_SCOUTING = "college_scouting"
    GO_PRO = "go_pro"
    IMPROVE_FITNESS = "improve_fitness"
    HAVE_FUN = "have_fun"

class Challenge(str, Enum):
    LACK_OF_TIME = "lack_of_time"
    LACK_OF_EQUIPMENT = "lack_of_equipment"
    UNSURE_FOCUS = "unsure_focus"
    MOTIVATION = "motivation"
    INJURY = "injury"
    NO_TEAM = "no_team"

class ExperienceLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    PROFESSIONAL = "professional"

class Position(str, Enum):
    GOALKEEPER = "goalkeeper"
    FULLBACK = "fullback"
    CENTER_BACK = "center_back"
    DEFENSIVE_MID = "defensive_mid"
    CENTER_MID = "center_mid"
    ATTACKING_MID = "attacking_mid"
    WINGER = "winger"
    STRIKER = "striker"

class AgeRange(str, Enum):
    YOUTH = "youth"
    TEEN = "teen"
    JUNIOR = "junior"
    ADULT = "adult"
    SENIOR = "senior"

class Skill(str, Enum):
    PASSING = "passing"
    DRIBBLING = "dribbling"
    SHOOTING = "shooting"
    DEFENDING = "defending"
    FIRST_TOUCH = "first_touch"
    FITNESS = "fitness"

class TrainingLocation(str, Enum):
    FULL_FIELD = "full_field"
    SMALL_FIELD = "small_field"
    INDOOR_COURT = "indoor_court"
    BACKYARD = "backyard"
    SMALL_ROOM = "small_room"

class Equipment(str, Enum):
    BALL = "ball"
    CONES = "cones"
    WALL = "wall"
    GOALS = "goals"

class TrainingDuration(int, Enum):
    MINS_15 = 15
    MINS_30 = 30
    MINS_45 = 45
    MINS_60 = 60
    MINS_90 = 90
    MINS_120 = 120

class TrainingFrequency(str, Enum):
    LIGHT = "light"
    MODERATE = "moderate"
    INTENSE = "intense"

class TrainingStyle(str, Enum):
    MEDIUM_INTENSITY = "medium_intensity"
    HIGH_INTENSITY = "high_intensity"
    GAME_PREP = "game_prep"
    GAME_RECOVERY = "game_recovery"
    REST_DAY = "rest_day"

class Difficulty(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

# *** SKILL CATEGORY ENUMS ***
class SkillCategory(str, Enum):
    PASSING = "passing"
    SHOOTING = "shooting"
    DRIBBLING = "dribbling"
    FIRST_TOUCH = "first_touch"
    FITNESS = "fitness"

class PassingSubSkill(str, Enum):
    SHORT_PASSING = "short_passing"
    LONG_PASSING = "long_passing"
    WALL_PASSING = "wall_passing"

class ShootingSubSkill(str, Enum):
    POWER = "power"
    FINISHING = "finishing"
    VOLLEYS = "volleys"
    LONG_SHOTS = "long_shots"

class DribblingSubSkill(str, Enum):
    BALL_MASTERY = "ball_mastery"
    CLOSE_CONTROL = "close_control"
    SPEED_DRIBBLING = "speed_dribbling"
    ONE_V_ONE_MOVES = "1v1_moves"

class FirstTouchSubSkill(str, Enum):
    GROUND_CONTROL = "ground_control"
    AERIAL_CONTROL = "aerial_control"
    TURNING_WITH_BALL = "turning_with_ball"
    ONE_TOUCH_CONTROL = "one_touch_control"

class FitnessSubSkill(str, Enum):
    SPEED = "speed"
    AGILITY = "agility"
    ENDURANCE = "endurance"

# *** USER MODELS ***
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    hashed_password = Column(String)
    age = Column(String)
    level = Column(String)
    position = Column(String)
    # player_details = Column(JSON)
    playstyle_representatives = Column(JSON)
    strengths = Column(JSON)
    weaknesses = Column(JSON)
    has_team = Column(Boolean, default=False)
    primary_goal = Column(String)
    timeline = Column(String)
    skill_level = Column(String)
    training_days = Column(JSON)
    available_equipment = Column(JSON)
    session_preferences = relationship("SessionPreferences", back_populates="user", uselist=False)
    
class OnboardingData(BaseModel):
    primary_goal: PrimaryGoal
    main_challenge: Challenge
    experience_level: ExperienceLevel
    position: Position
    playstyle_representative: str
    age_range: AgeRange
    strengths: List[Skill]
    areas_to_improve: List[Skill]
    training_location: TrainingLocation
    available_equipment: List[Equipment]
    daily_training_time: TrainingDuration
    weekly_training_days: TrainingFrequency

    model_config = ConfigDict(from_attributes=True)

# *** DRILL MODELS ***

class DrillCategory(Base):
    __tablename__ = "drill_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    description = Column(String)

class DrillType(str, Enum):
    TIME_BASED = "time_based"  # e.g., "Perform for 2 minutes"
    REP_BASED = "rep_based"    # e.g., "Do 10 shots"
    SET_BASED = "set_based"    # e.g., "3 sets of 5 reps"
    CONTINUOUS = "continuous"   # e.g., "Until successful completion"

class DrillSkillFocus(Base):
    __tablename__ = "drill_skill_focus"
    
    id = Column(Integer, primary_key=True, index=True)
    drill_id = Column(Integer, ForeignKey("drills.id"))
    category = Column(String)  # SkillCategory enum value
    sub_skill = Column(String)  # Corresponding SubSkill enum value
    is_primary = Column(Boolean, default=True)  # Whether this is a primary or secondary skill focus

class Drill(Base):
    __tablename__ = "drills"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    category_id = Column(Integer, ForeignKey("drill_categories.id"))
    
    # Time and Intensity
    duration = Column(Integer)  # in minutes
    intensity = Column(String)  # high, medium, low
    training_styles = Column(JSON)  # List of TrainingStyle
    
    # Structure
    type = Column(String)  # DrillType enum
    sets = Column(Integer, nullable=True)
    reps = Column(Integer, nullable=True)
    rest = Column(Integer, nullable=True)  # in seconds
    
    # Requirements
    equipment = Column(JSON)  # List of Equipment
    suitable_locations = Column(JSON)  # List of Location
    
    # Technical
    difficulty = Column(String)
    skill_focus = relationship("DrillSkillFocus", backref="drill")  # Relationship to skill focus
    
    # Content
    instructions = Column(JSON)  # List of steps
    tips = Column(JSON)  # List of coaching tips
    common_mistakes = Column(JSON)  # Things to watch out for
    progression_steps = Column(JSON)  # How to make it harder/easier
    variations = Column(JSON)  # Alternative versions
    video_url = Column(String, nullable=True)
    thumbnail_url = Column(String, nullable=True)

    category = relationship("DrillCategory", backref="drills")

    
# *** SESSION MODELS ***

class SessionPreferences(Base):
    __tablename__ = "session_preferences"

    id = Column(Integer, primary_key=True, index=True)
    duration = Column(Integer)  # in minutes
    available_equipment = Column(ARRAY(String))
    training_style = Column(String)
    training_location = Column(String)
    difficulty = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    target_skills = Column(JSON)  # List of {category: str, sub_skills: List[str]}
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    user = relationship("User", back_populates="session_preferences")

class TrainingSession(Base):
    """Represents a complete training session"""
    __tablename__ = "training_sessions"

    id = Column(Integer, primary_key=True, index=True)
    total_duration = Column(Integer)  # in minutes
    focus_areas = Column(JSON)  # List of skill areas
    created_at = Column(DateTime, server_default=func.now())
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Optional user association

    # Many-to-many relationship with drills
    drills = relationship(
        "Drill",
        secondary="session_drills",
        backref="training_sessions"
    )

    user = relationship("User", backref="training_sessions")

# Association table for many-to-many relationship between sessions and drills
session_drills = Table(
    "session_drills",
    Base.metadata,
    Column("session_id", Integer, ForeignKey("training_sessions.id")),
    Column("drill_id", Integer, ForeignKey("drills.id")),
)
    