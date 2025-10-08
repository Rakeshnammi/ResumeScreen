import spacy
from typing import List, Dict, Set, Tuple
import re
from collections import Counter
import math

class NLPAnalyzer:
    """Advanced NLP analysis for resume and job description processing"""
    
    def __init__(self):
        self.nlp = self._load_nlp_model()
        self.stopwords = self._get_stopwords()
        self.technical_skills = self._load_technical_skills()
    
    def _load_nlp_model(self):
        """Load spaCy NLP model with error handling"""
        try:
            return spacy.load("en_core_web_sm")
        except OSError:
            try:
                return spacy.load("en_core_web_md")
            except OSError:
                print("Warning: No spaCy model found. Using blank model.")
                nlp = spacy.blank("en")
                # Add basic components
                nlp.add_pipe("sentencizer")
                return nlp
    
    def _get_stopwords(self) -> Set[str]:
        """Get English stopwords"""
        try:
            return self.nlp.Defaults.stop_words
        except:
            # Fallback stopwords
            return {
                'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
                'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
                'to', 'was', 'will', 'with', 'the', 'this', 'but', 'they', 'have',
                'had', 'what', 'said', 'each', 'which', 'their', 'time', 'if'
            }
    
    def _load_technical_skills(self) -> Dict[str, List[str]]:
        """Load categorized technical skills for better matching"""
        return {
            'programming': [
                'python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby', 'go',
                'rust', 'scala', 'typescript', 'kotlin', 'swift', 'r', 'matlab'
            ],
            'web': [
                'html', 'css', 'react', 'angular', 'vue', 'node.js', 'express',
                'django', 'flask', 'spring', 'asp.net', 'jquery', 'bootstrap'
            ],
            'database': [
                'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
                'sqlite', 'oracle', 'sql server', 'cassandra', 'dynamodb'
            ],
            'cloud': [
                'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins',
                'terraform', 'ansible', 'git', 'github', 'gitlab'
            ],
            'data_science': [
                'machine learning', 'data science', 'tensorflow', 'pytorch',
                'scikit-learn', 'pandas', 'numpy', 'matplotlib', 'tableau', 'spark'
            ],
            'mobile': [
                'android', 'ios', 'react native', 'flutter', 'xamarin', 'ionic'
            ]
        }
    
    def analyze_job_requirements(self, job_description: str) -> Dict:
        """
        Analyze job description to extract requirements and keywords
        
        Args:
            job_description: Job description text
            
        Returns:
            Dictionary with analyzed job requirements
        """
        doc = self.nlp(job_description.lower())
        
        # Extract key information
        required_skills = self._extract_required_skills(job_description)
        experience_requirements = self._extract_experience_requirements(job_description)
        education_requirements = self._extract_education_requirements(job_description)
        important_keywords = self._extract_important_keywords(doc)
        
        return {
            'required_skills': required_skills,
            'experience_requirements': experience_requirements,
            'education_requirements': education_requirements,
            'important_keywords': important_keywords,
            'processed_text': [token.lemma_ for token in doc if not token.is_stop and not token.is_punct]
        }
    
    def _extract_required_skills(self, text: str) -> List[str]:
        """Extract required skills from job description"""
        text_lower = text.lower()
        found_skills = []
        
        # Check all technical skills
        all_skills = []
        for category, skills in self.technical_skills.items():
            all_skills.extend(skills)
        
        for skill in all_skills:
            if skill.lower() in text_lower:
                found_skills.append(skill)
        
        # Look for skills in requirements sections
        requirements_sections = self._find_requirements_sections(text)
        for section in requirements_sections:
            section_skills = self._parse_skills_from_requirements(section)
            found_skills.extend(section_skills)
        
        return list(set(found_skills))  # Remove duplicates
    
    def _find_requirements_sections(self, text: str) -> List[str]:
        """Find sections containing requirements"""
        requirement_headers = [
            'requirements', 'required skills', 'qualifications', 'must have',
            'essential skills', 'technical requirements', 'preferred skills'
        ]
        
        sections = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            for header in requirement_headers:
                if header in line_lower and len(line.strip()) < 100:
                    # Extract section content
                    section_text = ""
                    for j in range(i + 1, min(i + 15, len(lines))):
                        if lines[j].strip():
                            section_text += lines[j] + "\n"
                        elif len(section_text) > 50:  # End of section
                            break
                    sections.append(section_text)
                    break
        
        return sections
    
    def _parse_skills_from_requirements(self, text: str) -> List[str]:
        """Parse skills from requirements text"""
        skills = []
        
        # Common skill indicators
        skill_patterns = [
            r'experience (?:with|in) ([a-zA-Z0-9\.\+\s]+)',
            r'knowledge of ([a-zA-Z0-9\.\+\s]+)',
            r'proficient in ([a-zA-Z0-9\.\+\s]+)',
            r'familiar with ([a-zA-Z0-9\.\+\s]+)',
            r'skilled in ([a-zA-Z0-9\.\+\s]+)'
        ]
        
        for pattern in skill_patterns:
            matches = re.finditer(pattern, text.lower())
            for match in matches:
                skill = match.group(1).strip()
                if len(skill) > 2 and len(skill) < 50:
                    skills.append(skill.title())
        
        return skills
    
    def _extract_experience_requirements(self, text: str) -> str:
        """Extract experience requirements"""
        experience_patterns = [
            r'(\d+)(?:\+)?\s*years?\s+(?:of\s+)?experience',
            r'minimum\s+(\d+)\s+years?',
            r'at least\s+(\d+)\s+years?',
            r'(\d+)(?:\+)?\s*yrs?\s+experience'
        ]
        
        text_lower = text.lower()
        years_found = []
        
        for pattern in experience_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                years = int(match.group(1))
                if 0 < years < 20:  # Reasonable range
                    years_found.append(years)
        
        if years_found:
            return f"{min(years_found)} years"
        
        return "Not specified"
    
    def _extract_education_requirements(self, text: str) -> str:
        """Extract education requirements"""
        education_patterns = [
            r'(bachelor[s]?|master[s]?|phd|doctorate)',
            r'(degree|diploma|certificate)',
            r'(b\.?[a-z]{2,4}|m\.?[a-z]{2,4})'
        ]
        
        text_lower = text.lower()
        education_found = []
        
        for pattern in education_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                education_found.append(match.group(1))
        
        return ' | '.join(set(education_found)) if education_found else "Not specified"
    
    def _extract_important_keywords(self, doc) -> List[str]:
        """Extract important keywords using TF-IDF like approach"""
        # Get tokens excluding stopwords and punctuation
        tokens = [token.lemma_.lower() for token in doc 
                 if not token.is_stop and not token.is_punct and len(token.text) > 2]
        
        # Count frequency
        token_freq = Counter(tokens)
        
        # Return top keywords
        return [word for word, freq in token_freq.most_common(20)]
    
    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts using spaCy
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score between 0 and 1
        """
        try:
            doc1 = self.nlp(text1.lower())
            doc2 = self.nlp(text2.lower())
            
            # Use spaCy's similarity if available
            if hasattr(doc1, 'similarity'):
                return doc1.similarity(doc2)
            else:
                # Fallback to token-based similarity
                return self._token_similarity(doc1, doc2)
                
        except Exception as e:
            print(f"Error calculating similarity: {e}")
            return 0.0
    
    def _token_similarity(self, doc1, doc2) -> float:
        """Fallback similarity calculation using token overlap"""
        tokens1 = set([token.lemma_.lower() for token in doc1 
                      if not token.is_stop and not token.is_punct])
        tokens2 = set([token.lemma_.lower() for token in doc2 
                      if not token.is_stop and not token.is_punct])
        
        if not tokens1 or not tokens2:
            return 0.0
        
        # Jaccard similarity
        intersection = len(tokens1.intersection(tokens2))
        union = len(tokens1.union(tokens2))
        
        return intersection / union if union > 0 else 0.0
    
    def extract_key_phrases(self, text: str, max_phrases: int = 10) -> List[str]:
        """
        Extract key phrases from text
        
        Args:
            text: Input text
            max_phrases: Maximum number of phrases to return
            
        Returns:
            List of key phrases
        """
        doc = self.nlp(text)
        
        # Extract noun phrases
        noun_phrases = []
        for chunk in doc.noun_chunks:
            phrase = chunk.text.strip().lower()
            if (len(phrase.split()) <= 4 and  # Not too long
                len(phrase) > 3 and  # Not too short
                phrase not in self.stopwords):
                noun_phrases.append(phrase)
        
        # Count frequency and return top phrases
        phrase_freq = Counter(noun_phrases)
        return [phrase for phrase, freq in phrase_freq.most_common(max_phrases)]
    
    def analyze_skill_categories(self, skills: List[str]) -> Dict[str, List[str]]:
        """
        Categorize skills into technical categories
        
        Args:
            skills: List of skills
            
        Returns:
            Dictionary with categorized skills
        """
        categorized = {category: [] for category in self.technical_skills.keys()}
        categorized['other'] = []
        
        for skill in skills:
            skill_lower = skill.lower()
            categorized_flag = False
            
            for category, category_skills in self.technical_skills.items():
                if any(cat_skill in skill_lower for cat_skill in category_skills):
                    categorized[category].append(skill)
                    categorized_flag = True
                    break
            
            if not categorized_flag:
                categorized['other'].append(skill)
        
        # Remove empty categories
        return {k: v for k, v in categorized.items() if v}
