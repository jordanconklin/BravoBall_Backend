"""
Unit tests for the session generator module.
Tests the generation of training sessions for different user profiles.

Key test cases:
1. Beginner player with standard equipment
2. Limited equipment player with minimal resources

Run with: pytest unit_tests/session_generator.py -v -s
"""

import sys
from pathlib import Path
import pytest
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from models import *
from services.session_generator import SessionGenerator
from db import SessionLocal

# Test profiles with different equipment and skill levels
USER_PROFILES = {
    "beginner_player": {
        "name": "Beginner Player",
        "description": "New player with basic equipment (ball, cones)",
        "preferences": {
            "duration": 30,
            "available_equipment": [Equipment.BALL.value, Equipment.CONES.value],
            "training_style": TrainingStyle.MEDIUM_INTENSITY.value,
            "training_location": TrainingLocation.BACKYARD.value,
            "difficulty": Difficulty.BEGINNER.value,
            "target_skills": ["passing", "first_touch"]
        }
    },
    "limited_equipment_player": {
        "name": "Limited Equipment Player",
        "description": "Player with only a ball, training indoors",
        "preferences": {
            "duration": 30,
            "available_equipment": [Equipment.BALL.value],
            "training_style": TrainingStyle.MEDIUM_INTENSITY.value,
            "training_location": TrainingLocation.SMALL_ROOM.value,
            "difficulty": Difficulty.INTERMEDIATE.value,
            "target_skills": ["ball_mastery", "first_touch"]
        }
    },
    # New test profile for 90-minute session
    "ninety_minute_player": {
        "name": "90-Minute Session Player",
        "description": "Player with a 90-minute session, full equipment",
        "preferences": {
            "duration": 90,
            "available_equipment": [Equipment.BALL.value, Equipment.CONES.value, Equipment.GOALS.value, Equipment.WALL.value],
            "training_style": TrainingStyle.HIGH_INTENSITY.value,
            "training_location": TrainingLocation.FULL_FIELD.value,
            "difficulty": Difficulty.ADVANCED.value,
            "target_skills": ["shooting", "dribbling", "first_touch"]
        }
    }
}

def create_session_preferences(profile):
    """Create SessionPreferences object from profile data."""
    return SessionPreferences(
        duration=profile["preferences"]["duration"],
        available_equipment=profile["preferences"]["available_equipment"],
        training_style=profile["preferences"]["training_style"],
        training_location=profile["preferences"]["training_location"],
        difficulty=profile["preferences"]["difficulty"],
        target_skills=profile["preferences"]["target_skills"]
    )

def print_session_details(profile_name, session, profile):
    """
    Print detailed session information in a formatted way.
    
    Args:
        profile_name: Name of the user profile being tested
        session: Generated training session
        profile: User profile configuration
    """
    print("\n" + "="*80)
    print(f"🏃 Testing Profile: {profile_name}")
    print(f"📝 {profile['description']}")
    print("-"*80)
    
    # Print Profile Preferences
    print("\n📋 Profile Preferences:")
    prefs = profile["preferences"]
    print(f"⏱  Duration Goal: {prefs['duration']} minutes")
    print(f"📍  Location: {prefs['training_location']}")
    print(f"🎯  Difficulty: {prefs['difficulty']}")
    print(f"⚽  Equipment: {', '.join(prefs['available_equipment'])}")
    print(f"🔄  Target Skills: {', '.join(prefs['target_skills'])}")
    
    if not session.ordered_drills:
        print("\n❌ No suitable drills found for this profile")
        return

    # Print Selected Drills
    print("\n📚 Selected Drills:")
    for i, osd in enumerate(sorted(session.ordered_drills, key=lambda x: x.position), 1):
        drill = osd.drill
        print(f"\n{i}. {drill.title}")
        print(f"   {'Duration':12} │ {getattr(drill, 'duration', 0):2d} min │ Adjusted: {osd.duration or drill.duration:2d} min")
        print(f"   {'Equipment':12} │ {', '.join(drill.equipment) if drill.equipment else 'None'}")
        print(f"   {'Difficulty':12} │ {drill.difficulty.title() if drill.difficulty else 'Unknown'}")
        print(f"   {'Sets':12} │ {osd.sets if osd.sets is not None else drill.sets}")
        print(f"   {'Reps':12} │ {osd.reps if osd.reps is not None else drill.reps}")
        print(f"   {'Rest':12} │ {osd.rest if osd.rest is not None else drill.rest}")
    
    # Print Session Summary
    print("\n📊 Session Summary:")
    print(f"✓ Total Duration: {session.total_duration}/{prefs['duration']} minutes")
    print(f"✓ Number of Drills: {len(session.ordered_drills)}")
    
    equipment_used = set()
    for osd in session.ordered_drills:
        drill = osd.drill
        if drill.equipment:
            equipment_used.update(drill.equipment)
    print(f"✓ Equipment Types Used: {', '.join(sorted(equipment_used))}")
    print("="*80 + "\n")

@pytest.mark.asyncio
async def test_session_generation():
    """
    Test session generation for different user profiles.
    Verifies that appropriate drills are selected and durations are adjusted correctly.
    """
    db = SessionLocal()
    try:
        generator = SessionGenerator(db)
        
        for profile_name, profile in USER_PROFILES.items():
            # Create preferences from profile
            preferences = create_session_preferences(profile)
            
            # Generate session
            session = await generator.generate_session(preferences)
            
            # Print detailed session information
            print_session_details(profile_name, session, profile)
            
            # Basic assertions
            assert session is not None, f"Session should be generated for {profile_name}"
            assert len(session.ordered_drills) > 0, f"Session should contain drills for {profile_name}"
            assert session.total_duration <= preferences.duration * 1.2, \
                f"Session duration ({session.total_duration}) should not exceed preferred duration ({preferences.duration}) by more than 20%"
            
            # Equipment assertions
            for osd in session.ordered_drills:
                drill = osd.drill
                missing_equipment = set(drill.equipment or []) - set(preferences.available_equipment)
                if missing_equipment:
                    assert missing_equipment <= generator.ADAPTABLE_EQUIPMENT, \
                        f"Drill {drill.title} requires unavailable equipment: {missing_equipment}"
            
            # New assertion for 90-minute session: max 5 drills
            if preferences.duration == 90:
                assert len(session.ordered_drills) <= 6, (
                    f"90-minute session should have at most 6 drills, got {len(session.ordered_drills)}"
                )
    finally:
        db.close()

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"]) 