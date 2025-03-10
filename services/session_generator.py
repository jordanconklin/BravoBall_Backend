from sqlalchemy.orm import Session
from models import (
    Drill, 
    TrainingSession, 
    SessionPreferences,
    TrainingLocation,
    TrainingStyle,
    Difficulty
)
from typing import List
from utils.drill_scorer import DrillScorer

class SessionGenerator:
    def __init__(self, db: Session):
        self.db = db

    async def generate_session(self, preferences: SessionPreferences) -> TrainingSession:
        """Generate a training session based on user preferences"""
        # Get all drills from database
        all_drills = self.db.query(Drill).all()
        print(f"\nFound {len(all_drills)} total drills")

        # Create drill scorer that scores drills based on user preferences
        scorer = DrillScorer(preferences)
        
        # Score and rank all drills
        ranked_drills = scorer.rank_drills(all_drills)
        
        # Filter suitable drills
        suitable_drills = []
        current_duration = 0

        # Filter drills based on user preferences and scores
        for ranked_drill in ranked_drills:
            drill = ranked_drill['drill']
            scores = ranked_drill['scores']
            
            print(f"\nChecking drill: {drill.title}")
            print(f": {ranked_drill['total_score']}")
            print(f"Score breakdown: {scores}")
            
            # For limited equipment scenarios, be more lenient with requirements
            has_limited_equipment = len(preferences.available_equipment) <= 1
            
            # Skip drills only if they completely fail critical requirements
            if scores['equipment'] == 0 or scores['location'] == 0:
                if has_limited_equipment and scores['equipment'] == 0:
                    # For limited equipment, only skip if it requires goals
                    if not any(eq == "GOALS" for eq in drill.required_equipment):
                        # Allow drill if it only needs adaptable equipment
                        pass
                    else:
                        print("❌ Failed critical requirements check - requires goals")
                        continue
                else:
                    print("❌ Failed critical requirements check")
                    continue
                
            # More lenient skill relevance check for limited equipment
            if scores['primary_skill'] == 0 and scores['secondary_skill'] == 0:
                if has_limited_equipment:
                    # For limited equipment, accept drills that at least work on basic skills
                    if any(skill in ["ball_mastery", "first_touch", "dribbling"] for skill in preferences.target_skills):
                        pass
                    else:
                        print("❌ Failed skill relevance check")
                        continue
                else:
                    print("❌ Failed skill relevance check")
                    continue

            # Calculate intensity modifier based on player level vs drill difficulty
            intensity_modifier = self._calculate_intensity_modifier(preferences.difficulty, drill.difficulty)
            
            # For limited equipment, allow shorter minimum durations to fit more drills
            original_duration = drill.duration
            min_duration = 3 if has_limited_equipment else 5
            
            # Adjust drill duration based on session time constraint
            adjusted_duration = self._adjust_duration_for_session_fit(
                original_duration, 
                preferences.duration,
                current_duration,
                len(suitable_drills),
                min_duration
            )

            print(f"Original duration: {original_duration} minutes")
            print(f"Adjusted duration: {adjusted_duration} minutes")

            # Store the adjustments with the drill
            drill.adjusted_duration = adjusted_duration
            drill.intensity_modifier = intensity_modifier
            drill.original_duration = original_duration

            # Add drill to suitable drills
            suitable_drills.append(drill)
            current_duration += adjusted_duration

            # For limited equipment, try to get at least 3 drills if possible
            if has_limited_equipment and len(suitable_drills) < 3:
                continue

            # If we've significantly exceeded the preferred duration, stop adding drills
            if current_duration > preferences.duration * 1.2:  # Allow 20% overflow before stopping
                break

        print(f"\nFound {len(suitable_drills)} suitable drills")

        # Normalize durations to fit within target time
        if suitable_drills:
            suitable_drills = self._normalize_session_duration(suitable_drills, preferences.duration)
            current_duration = sum(drill.adjusted_duration for drill in suitable_drills)

        # Create and return the training session
        session = TrainingSession(
            total_duration=current_duration,
            focus_areas=preferences.target_skills
        )
        session.drills = suitable_drills

        # Add to database if user is provided
        if preferences.user_id:
            session.user_id = preferences.user_id
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)

        return session

    def _calculate_intensity_modifier(self, player_difficulty: str, drill_difficulty: str) -> float:
        """Calculate intensity modifier based on player level vs drill difficulty"""
        difficulty_levels = {
            "beginner": 1,
            "intermediate": 2,
            "advanced": 3
        }
        
        player_level = difficulty_levels[player_difficulty.lower()]
        drill_level = difficulty_levels[drill_difficulty.lower()]
        level_diff = player_level - drill_level

        # If player is more advanced than drill, increase intensity
        if level_diff > 0:
            return 1.2  # 20% more intense
        # If player is at drill level, normal intensity
        elif level_diff == 0:
            return 1.0
        # If drill is more advanced than player, reduce intensity
        else:
            return 0.8  # 20% less intense

    def _adjust_duration_for_session_fit(
        self, 
        original_duration: int, 
        target_session_duration: int,
        current_session_duration: int,
        num_drills_so_far: int,
        min_duration: int = 5
    ) -> int:
        """
        Adjust drill duration to better fit within session constraints while maintaining effectiveness.
        Uses a dynamic approach based on session progress and remaining time.
        """
        # If this is the first drill, aim for about 25-35% of session time
        if num_drills_so_far == 0:
            target_first_drill = target_session_duration * 0.3  # 30% of session time
            return max(int(min(original_duration, target_first_drill)), min_duration)

        # Calculate remaining session time
        remaining_time = target_session_duration - current_session_duration

        # If we have plenty of time, keep original duration
        if remaining_time > original_duration * 1.5:
            return original_duration

        # If we're running short on time, scale duration down
        # but maintain a minimum effective duration
        min_effective_duration = max(min_duration, int(original_duration * 0.6))
        scaled_duration = min(original_duration, int(remaining_time * 0.7))
        
        return max(min_effective_duration, scaled_duration)

    def _normalize_session_duration(self, drills: List[Drill], target_duration: int) -> List[Drill]:
        """
        Normalize drill durations to fit within target session duration by proportionally
        reducing all drill durations while maintaining minimum effective durations.
        For shorter sessions, allows more aggressive reduction to fit more drills.
        """
        current_duration = sum(drill.adjusted_duration for drill in drills)
        
        if current_duration <= target_duration:
            return drills
        
        # Calculate base minimum duration based on session length
        # For shorter sessions (30 mins or less), allow drills as short as 3 minutes
        # For longer sessions (60+ mins), keep minimum of 5 minutes
        base_min_duration = max(3, min(5, target_duration // 10))
        
        # Calculate reduction ratio needed
        reduction_ratio = target_duration / current_duration
        
        # First pass: Try to reduce all drills proportionally
        total_adjusted = 0
        for drill in drills:
            # Calculate new duration with ratio, ensuring minimum duration
            new_duration = max(base_min_duration, int(drill.adjusted_duration * reduction_ratio))
            drill.adjusted_duration = new_duration
            total_adjusted += new_duration
        
        # Second pass: If we're still over, reduce longer drills more aggressively
        if total_adjusted > target_duration:
            excess_time = total_adjusted - target_duration
            drills_by_duration = sorted(drills, key=lambda x: x.adjusted_duration, reverse=True)
            
            # Calculate maximum reduction percentage based on session duration
            # Shorter sessions allow up to 80% reduction, longer sessions up to 60%
            max_reduction_pct = 0.8 if target_duration <= 30 else 0.7 if target_duration <= 45 else 0.6
            
            for drill in drills_by_duration:
                if excess_time <= 0:
                    break
                
                # Calculate how much we can reduce this drill
                current_duration = drill.adjusted_duration
                min_duration = max(base_min_duration, int(drill.original_duration * (1 - max_reduction_pct)))
                potential_reduction = current_duration - min_duration
                
                if potential_reduction > 0:
                    # Reduce by either the excess time or the potential reduction
                    actual_reduction = min(excess_time, potential_reduction)
                    drill.adjusted_duration = current_duration - actual_reduction
                    excess_time -= actual_reduction
        
        return drills