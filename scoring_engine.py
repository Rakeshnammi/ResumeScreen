from typing import List, Dict, Tuple
import math
import re
from collections import Counter
from nlp_analyzer import NLPAnalyzer

class ScoringEngine:
    """Scores resumes against job descriptions using various NLP techniques"""
    
    def __init__(self):
        self.nlp_analyzer = NLPAnalyzer()
        self.weights = {
            'skills_match': 0.4,
            'experience_match': 0.25,
            'education_match': 0.15,
            'keyword_relevance': 0.15,
            'text_similarity': 0.05
        }
    
    def score_candidates(self, candidates: List[Dict], job_description: str) -> List[Dict]:
        """
        Score all candidates against job description
        
        Args:
            candidates: List of candidate dictionaries
            job_description: Job description text
            
        Returns:
            List of candidates with scores added
        """
        # Analyze job requirements
        job_analysis = self.nlp_analyzer.analyze_job_requirements(job_description)
        
        scored_candidates = []
        
        for candidate in candidates:
            scores = self._score_single_candidate(candidate, job_description, job_analysis)
            
            # Add scores to candidate data
            candidate_scored = candidate.copy()
            candidate_scored.update(scores)
            
            scored_candidates.append(candidate_scored)
        
        # Sort by overall score
        scored_candidates.sort(key=lambda x: x['overall_score'], reverse=True)
        
        return scored_candidates
    
    def _score_single_candidate(self, candidate: Dict, job_description: str, job_analysis: Dict) -> Dict:
        """
        Score a single candidate against job requirements
        
        Args:
            candidate: Candidate data dictionary
            job_description: Job description text
            job_analysis: Analyzed job requirements
            
        Returns:
            Dictionary with scoring results
        """
        # Individual component scores
        skills_score = self._score_skills_match(
            candidate.get('skills', []), 
            job_analysis['required_skills']
        )
        
        experience_score = self._score_experience_match(
            candidate.get('experience_years', '0'),
            job_analysis['experience_requirements']
        )
        
        education_score = self._score_education_match(
            candidate.get('education', ''),
            job_analysis['education_requirements']
        )
        
        keyword_score = self._score_keyword_relevance(
            candidate.get('raw_text', ''),
            job_analysis['important_keywords']
        )
        
        similarity_score = self._score_text_similarity(
            candidate.get('raw_text', ''),
            job_description
        )
        
        # Calculate weighted overall score
        overall_score = (
            skills_score * self.weights['skills_match'] +
            experience_score * self.weights['experience_match'] +
            education_score * self.weights['education_match'] +
            keyword_score * self.weights['keyword_relevance'] +
            similarity_score * self.weights['text_similarity']
        )
        
        return {
            'skills_score': round(skills_score, 1),
            'experience_score': round(experience_score, 1),
            'education_score': round(education_score, 1),
            'keyword_score': round(keyword_score, 1),
            'similarity_score': round(similarity_score, 1),
            'overall_score': round(overall_score, 1)
        }
    
    def _score_skills_match(self, candidate_skills: List[str], required_skills: List[str]) -> float:
        """
        Score skills matching between candidate and job requirements
        
        Args:
            candidate_skills: List of candidate skills
            required_skills: List of required skills from job description
            
        Returns:
            Skills match score (0-100)
        """
        if not required_skills or not candidate_skills:
            return 0.0
        
        # Convert to lowercase for comparison
        candidate_skills_lower = [skill.lower() for skill in candidate_skills]
        required_skills_lower = [skill.lower() for skill in required_skills]
        
        # Exact matches
        exact_matches = 0
        partial_matches = 0
        
        for required_skill in required_skills_lower:
            # Check for exact match
            if required_skill in candidate_skills_lower:
                exact_matches += 1
            else:
                # Check for partial matches (e.g., "javascript" matches "js")
                for candidate_skill in candidate_skills_lower:
                    if (required_skill in candidate_skill or 
                        candidate_skill in required_skill or
                        self._is_skill_variant(required_skill, candidate_skill)):
                        partial_matches += 1
                        break
        
        # Calculate score
        total_required = len(required_skills_lower)
        exact_weight = 1.0
        partial_weight = 0.7
        
        score = (exact_matches * exact_weight + partial_matches * partial_weight) / total_required
        return min(score * 100, 100)  # Cap at 100%
    
    def _is_skill_variant(self, skill1: str, skill2: str) -> bool:
        """Check if two skills are variants of each other"""
        # Common skill variants
        variants = {
            'javascript': ['js', 'ecmascript'],
            'typescript': ['ts'],
            'python': ['py'],
            'machine learning': ['ml', 'ai', 'artificial intelligence'],
            'database': ['db', 'sql'],
            'user interface': ['ui'],
            'user experience': ['ux'],
            'cascading style sheets': ['css'],
            'hypertext markup language': ['html'],
            'node.js': ['nodejs', 'node'],
            'react.js': ['react', 'reactjs'],
            'angular.js': ['angular', 'angularjs'],
            'vue.js': ['vue', 'vuejs']
        }
        
        for main_skill, variant_list in variants.items():
            if ((skill1 == main_skill and skill2 in variant_list) or
                (skill2 == main_skill and skill1 in variant_list) or
                (skill1 in variant_list and skill2 in variant_list)):
                return True
        
        return False
    
    def _score_experience_match(self, candidate_experience: str, required_experience: str) -> float:
        """
        Score experience matching
        
        Args:
            candidate_experience: Candidate's experience (e.g., "5 years")
            required_experience: Required experience (e.g., "3 years")
            
        Returns:
            Experience match score (0-100)
        """
        # Extract numeric values
        candidate_years = self._extract_years_from_text(candidate_experience)
        required_years = self._extract_years_from_text(required_experience)
        
        if required_years == 0:  # No specific requirement
            return 75.0  # Neutral score
        
        if candidate_years == 0:  # No experience data
            return 30.0  # Low but not zero score
        
        # Calculate score based on experience ratio
        if candidate_years >= required_years:
            # Candidate meets or exceeds requirement
            excess_ratio = candidate_years / required_years
            if excess_ratio <= 1.5:  # Within reasonable range
                return 100.0
            else:
                # Overqualified - slight penalty
                return max(85.0, 100.0 - (excess_ratio - 1.5) * 10)
        else:
            # Candidate has less experience than required
            ratio = candidate_years / required_years
            return ratio * 80  # Max 80% if slightly under-qualified
    
    def _extract_years_from_text(self, text: str) -> int:
        """Extract years from text"""
        if not text or text in ['Not Specified', 'Unknown']:
            return 0
        
        # Look for numeric patterns
        year_patterns = [
            r'(\d+)\s*(?:\+)?\s*years?',
            r'(\d+)\s*(?:\+)?\s*yrs?',
            r'^(\d+)$',  # Just a number
            r'~(\d+)'  # Approximate
        ]
        
        text_lower = str(text).lower()
        
        for pattern in year_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                try:
                    years = int(matches[0])
                    if 0 < years < 50:  # Reasonable range
                        return years
                except ValueError:
                    continue
        
        return 0
    
    def _score_education_match(self, candidate_education: str, required_education: str) -> float:
        """
        Score education matching
        
        Args:
            candidate_education: Candidate's education
            required_education: Required education
            
        Returns:
            Education match score (0-100)
        """
        if not required_education or required_education == "Not specified":
            return 75.0  # Neutral score when no specific requirement
        
        if not candidate_education or candidate_education == "Not Specified":
            return 40.0  # Low score for missing education data
        
        candidate_edu_lower = candidate_education.lower()
        required_edu_lower = required_education.lower()
        
        # Education level hierarchy
        education_levels = {
            'phd': 6, 'doctorate': 6,
            'master': 5, 'masters': 5, 'msc': 5, 'ma': 5, 'mba': 5, 'mtech': 5, 'me': 5,
            'bachelor': 4, 'bachelors': 4, 'bsc': 4, 'ba': 4, 'btech': 4, 'be': 4,
            'associate': 3,
            'diploma': 2,
            'certificate': 1
        }
        
        # Find education levels
        candidate_level = 0
        required_level = 0
        
        for edu_type, level in education_levels.items():
            if edu_type in candidate_edu_lower:
                candidate_level = max(candidate_level, level)
            if edu_type in required_edu_lower:
                required_level = max(required_level, level)
        
        if required_level == 0:  # No clear requirement level
            return 70.0
        
        if candidate_level == 0:  # No clear candidate level
            return 50.0
        
        # Score based on education level comparison
        if candidate_level >= required_level:
            return 100.0  # Meets or exceeds requirement
        elif candidate_level == required_level - 1:
            return 75.0  # One level below
        elif candidate_level == required_level - 2:
            return 50.0  # Two levels below
        else:
            return 25.0  # Significantly below requirement
    
    def _score_keyword_relevance(self, candidate_text: str, important_keywords: List[str]) -> float:
        """
        Score based on presence of important keywords from job description
        
        Args:
            candidate_text: Full text of candidate's resume
            important_keywords: Important keywords from job description
            
        Returns:
            Keyword relevance score (0-100)
        """
        if not important_keywords or not candidate_text:
            return 50.0  # Neutral score
        
        candidate_text_lower = candidate_text.lower()
        
        # Count keyword matches
        matches = 0
        total_keywords = len(important_keywords)
        
        for keyword in important_keywords:
            if keyword.lower() in candidate_text_lower:
                matches += 1
        
        # Calculate score
        if total_keywords == 0:
            return 50.0
        
        match_ratio = matches / total_keywords
        return match_ratio * 100
    
    def _score_text_similarity(self, candidate_text: str, job_description: str) -> float:
        """
        Score based on overall text similarity using NLP
        
        Args:
            candidate_text: Full text of candidate's resume
            job_description: Job description text
            
        Returns:
            Text similarity score (0-100)
        """
        if not candidate_text or not job_description:
            return 0.0
        
        similarity = self.nlp_analyzer.calculate_text_similarity(
            candidate_text, job_description
        )
        
        return similarity * 100
    
    def get_scoring_breakdown(self, candidate: Dict) -> Dict:
        """
        Get detailed scoring breakdown for a candidate
        
        Args:
            candidate: Candidate with scores
            
        Returns:
            Detailed scoring breakdown
        """
        return {
            'component_scores': {
                'Skills Match': {
                    'score': candidate.get('skills_score', 0),
                    'weight': self.weights['skills_match'],
                    'contribution': candidate.get('skills_score', 0) * self.weights['skills_match']
                },
                'Experience Match': {
                    'score': candidate.get('experience_score', 0),
                    'weight': self.weights['experience_match'],
                    'contribution': candidate.get('experience_score', 0) * self.weights['experience_match']
                },
                'Education Match': {
                    'score': candidate.get('education_score', 0),
                    'weight': self.weights['education_match'],
                    'contribution': candidate.get('education_score', 0) * self.weights['education_match']
                },
                'Keyword Relevance': {
                    'score': candidate.get('keyword_score', 0),
                    'weight': self.weights['keyword_relevance'],
                    'contribution': candidate.get('keyword_score', 0) * self.weights['keyword_relevance']
                },
                'Text Similarity': {
                    'score': candidate.get('similarity_score', 0),
                    'weight': self.weights['text_similarity'],
                    'contribution': candidate.get('similarity_score', 0) * self.weights['text_similarity']
                }
            },
            'overall_score': candidate.get('overall_score', 0),
            'strengths': self._identify_strengths(candidate),
            'areas_for_improvement': self._identify_weaknesses(candidate)
        }
    
    def _identify_strengths(self, candidate: Dict) -> List[str]:
        """Identify candidate's strengths based on scores"""
        strengths = []
        
        if candidate.get('skills_score', 0) >= 80:
            strengths.append("Strong skill match with job requirements")
        
        if candidate.get('experience_score', 0) >= 80:
            strengths.append("Excellent experience level for the role")
        
        if candidate.get('education_score', 0) >= 80:
            strengths.append("Educational background aligns well with requirements")
        
        if candidate.get('keyword_score', 0) >= 70:
            strengths.append("Resume contains relevant industry keywords")
        
        return strengths
    
    def _identify_weaknesses(self, candidate: Dict) -> List[str]:
        """Identify areas where candidate could improve"""
        weaknesses = []
        
        if candidate.get('skills_score', 0) < 50:
            weaknesses.append("Limited skill overlap with job requirements")
        
        if candidate.get('experience_score', 0) < 50:
            weaknesses.append("Experience level may not meet job requirements")
        
        if candidate.get('education_score', 0) < 50:
            weaknesses.append("Educational background differs from typical requirements")
        
        if candidate.get('keyword_score', 0) < 40:
            weaknesses.append("Resume could benefit from more relevant industry keywords")
        
        return weaknesses
