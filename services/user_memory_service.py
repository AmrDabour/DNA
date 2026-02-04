"""
User Memory Service - Long-term memory storage for AI Agent

Provides persistent per-user memory that stores:
- User name and preferences
- DNA analysis results (gender, ancestry)
- Disease risk factors
- Health recommendations

This memory is injected as a background prompt at the start of each chat session.
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class UserMemoryService:
    """Service for managing persistent user memory for the DNA Agent"""
    
    def __init__(self):
        self._collection = None
    
    @property
    def collection(self):
        """Lazy-load MongoDB collection"""
        if self._collection is None:
            try:
                from config.mongodb import get_user_memory_collection
                self._collection = get_user_memory_collection()
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB for user memory: {e}")
                return None
        return self._collection
    
    def get_user_memory(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get stored memory for a user.
        
        Args:
            user_id: The user's database ID
            
        Returns:
            User memory document or None if not found
        """
        if self.collection is None:
            return None
        
        try:
            memory = self.collection.find_one({'user_id': user_id})
            if memory:
                memory.pop('_id', None)  # Remove MongoDB ObjectId
            return memory
        except Exception as e:
            logger.error(f"Error fetching user memory for user {user_id}: {e}")
            return None
    
    def update_user_memory(self, user_id: int, updates: Dict[str, Any]) -> bool:
        """
        Update user memory with new data (upsert).
        
        Args:
            user_id: The user's database ID
            updates: Dictionary of fields to update
            
        Returns:
            True if successful, False otherwise
        """
        if self.collection is None:
            return False
        
        try:
            updates['user_id'] = user_id
            updates['updated_at'] = datetime.utcnow()
            
            self.collection.update_one(
                {'user_id': user_id},
                {'$set': updates},
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Error updating user memory for user {user_id}: {e}")
            return False
    
    def build_memory_from_analyses(self, user_id: int) -> Dict[str, Any]:
        """
        Build/rebuild user memory from their analysis history.
        Aggregates DNA results, disease risks, and health recommendations.
        
        Args:
            user_id: The user's database ID
            
        Returns:
            Aggregated memory data
        """
        try:
            from database.models import User, AnalysisHistory, GeneticRiskProfile
            
            user = User.query.get(user_id)
            if not user:
                return {}
            
            memory = {
                'user_id': user_id,
                'name': user.full_name or user.username,
                'memory_enabled': True,
                'updated_at': datetime.utcnow()
            }
            
            # Get most recent completed analysis
            latest_analysis = AnalysisHistory.query.filter_by(
                user_id=user_id,
                status='completed'
            ).order_by(AnalysisHistory.created_at.desc()).first()
            
            if latest_analysis:
                memory['dna_profile'] = {
                    'predicted_gender': latest_analysis.gender_prediction,
                    'gender_confidence': latest_analysis.gender_confidence,
                    'predicted_ancestry': latest_analysis.ancestry_prediction,
                    'ancestry_code': latest_analysis.ancestry_code,
                    'ancestry_confidence': latest_analysis.ancestry_confidence,
                    'last_analysis_date': latest_analysis.created_at.isoformat() if latest_analysis.created_at else None,
                    'sample_id': latest_analysis.sample_id,
                    'total_analyses': AnalysisHistory.query.filter_by(user_id=user_id).count()
                }
            
            # Get most recent risk profile
            latest_risk = GeneticRiskProfile.query.filter_by(
                user_id=user_id
            ).order_by(GeneticRiskProfile.created_at.desc()).first()
            
            if latest_risk:
                memory['health_profile'] = {
                    'overall_risk_score': latest_risk.overall_risk_score,
                    'cardiovascular_risk': latest_risk.cardiovascular_risk,
                    'diabetes_risk': latest_risk.diabetes_risk,
                    'cancer_risk': latest_risk.cancer_risk,
                    'alzheimer_risk': latest_risk.alzheimer_risk,
                    'health_recommendations': latest_risk.health_recommendations,
                    'lifestyle_recommendations': latest_risk.lifestyle_recommendations
                }
            
            # Store the aggregated memory
            self.update_user_memory(user_id, memory)
            
            return memory
            
        except Exception as e:
            logger.error(f"Error building memory from analyses for user {user_id}: {e}")
            return {}
    
    def set_user_preferences(self, user_id: int, preferences: Dict[str, Any]) -> bool:
        """
        Update user preferences in memory.
        
        Args:
            user_id: The user's database ID
            preferences: Dictionary with preference settings
            
        Returns:
            True if successful
        """
        return self.update_user_memory(user_id, {'preferences': preferences})
    
    def enable_memory(self, user_id: int, enabled: bool = True) -> bool:
        """
        Enable or disable memory for a user.
        
        Args:
            user_id: The user's database ID
            enabled: Whether memory should be enabled
            
        Returns:
            True if successful
        """
        return self.update_user_memory(user_id, {'memory_enabled': enabled})
    
    def delete_user_memory(self, user_id: int) -> bool:
        """
        Completely delete a user's memory (right to be forgotten).
        
        Args:
            user_id: The user's database ID
            
        Returns:
            True if successful
        """
        if self.collection is None:
            return False
        
        try:
            self.collection.delete_one({'user_id': user_id})
            return True
        except Exception as e:
            logger.error(f"Error deleting user memory for user {user_id}: {e}")
            return False
    
    def _get_user_basic_info(self, user_id: int) -> dict:
        """
        Get basic user info directly from PostgreSQL as fallback.
        Used when MongoDB is unavailable.
        """
        try:
            from database.models import User
            user = User.query.get(user_id)
            if user:
                return {
                    'user_id': user_id,
                    'name': user.full_name or user.username,
                    'memory_enabled': True
                }
        except Exception as e:
            logger.error(f"Failed to get basic user info: {e}")
        return None
    
    def generate_memory_prompt(self, user_id: int) -> str:
        """
        Generate the background prompt to inject into the system prompt.
        This is called at the start of each chat session.
        
        Args:
            user_id: The user's database ID
            
        Returns:
            Formatted prompt string with user context
        """
        memory = self.get_user_memory(user_id)
        
        if not memory:
            # Try to build memory from analyses if none exists
            memory = self.build_memory_from_analyses(user_id)
        
        if not memory:
            # Final fallback: get basic info from PostgreSQL
            memory = self._get_user_basic_info(user_id)
        
        if not memory or not memory.get('memory_enabled', True):
            return ""
        
        prompt_parts = []
        
        # User identification - VERY IMPORTANT
        name = memory.get('name', 'User')
        prompt_parts.append(f"## 👤 CURRENT USER IDENTITY:")
        prompt_parts.append(f"**Name: {name}**")
        prompt_parts.append(f"(When user asks 'what is my name?', answer: '{name}')")
        
        # DNA Profile
        dna = memory.get('dna_profile', {})
        if dna:
            prompt_parts.append("\n### Stored DNA Analysis Results:")
            if dna.get('predicted_gender'):
                confidence = dna.get('gender_confidence', 0)
                prompt_parts.append(f"- **Gender**: {dna['predicted_gender']} ({confidence:.1%} confidence)")
            if dna.get('predicted_ancestry'):
                code = dna.get('ancestry_code', '')
                confidence = dna.get('ancestry_confidence', 0)
                prompt_parts.append(f"- **Ancestry**: {dna['predicted_ancestry']} ({code}) ({confidence:.1%} confidence)")
            if dna.get('last_analysis_date'):
                prompt_parts.append(f"- **Last Analysis**: {dna['last_analysis_date'][:10]}")
            if dna.get('total_analyses'):
                prompt_parts.append(f"- **Total Analyses**: {dna['total_analyses']}")
        
        # Health Profile
        health = memory.get('health_profile', {})
        if health:
            prompt_parts.append("\n### Health Risk Profile:")
            
            risk_mapping = [
                ('cardiovascular_risk', 'Cardiovascular'),
                ('diabetes_risk', 'Diabetes'),
                ('cancer_risk', 'Cancer'),
                ('alzheimer_risk', "Alzheimer's")
            ]
            
            for key, label in risk_mapping:
                risk = health.get(key)
                if risk is not None:
                    level = 'Low' if risk < 0.3 else ('Moderate' if risk < 0.6 else 'Elevated')
                    prompt_parts.append(f"- **{label} Risk**: {level} ({risk:.1%})")
        
        
        # User preferences
        prefs = memory.get('preferences', {})
        if prefs:
            prompt_parts.append("\n### User Preferences:")
            if prefs.get('detail_level'):
                prompt_parts.append(f"- Detail Level: {prefs['detail_level']}")
            if prefs.get('focus_areas'):
                prompt_parts.append(f"- Focus Areas: {', '.join(prefs['focus_areas'])}")
        
        # Instructions for agent
        prompt_parts.append("\n### ⚠️ IMPORTANT INSTRUCTIONS:")
        prompt_parts.append(f"- When user asks 'what is my name?', respond: 'Your name is {name}'")
        prompt_parts.append("- When user asks about their gender/ancestry, use the stored results above if available")
        prompt_parts.append("- Reference their DNA profile when relevant to their questions")
        prompt_parts.append("- Be mindful of their health risk factors in recommendations")
        
        return "\n".join(prompt_parts)


# Singleton instance
_user_memory_service = None


def get_user_memory_service() -> UserMemoryService:
    """Get the singleton UserMemoryService instance"""
    global _user_memory_service
    if _user_memory_service is None:
        _user_memory_service = UserMemoryService()
    return _user_memory_service


def get_user_memory_prompt(user_id: int) -> str:
    """
    Convenience function to get the memory prompt for a user.
    
    Args:
        user_id: The user's database ID
        
    Returns:
        Formatted prompt string
    """
    service = get_user_memory_service()
    return service.generate_memory_prompt(user_id)


def update_user_memory_after_analysis(user_id: int) -> bool:
    """
    Convenience function to refresh user memory after a new analysis.
    Call this after completing an analysis to keep memory up-to-date.
    
    Args:
        user_id: The user's database ID
        
    Returns:
        True if successful
    """
    service = get_user_memory_service()
    memory = service.build_memory_from_analyses(user_id)
    return bool(memory)
