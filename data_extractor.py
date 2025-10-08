import re
import spacy
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import email_validator

class DataExtractor:
    """Extracts structured data from resume text using NLP"""
    
    def __init__(self):
        self.nlp = self._load_nlp_model()
        self.skills_keywords = self._load_skills_keywords()
        self.education_keywords = self._load_education_keywords()
    
    def _load_nlp_model(self):
        """Load spaCy NLP model"""
        try:
            # Try to load the full English model
            return spacy.load("en_core_web_sm")
        except OSError:
            try:
                # Fallback to basic English model
                return spacy.load("en_core_web_md")
            except OSError:
                # If no model is available, create a blank one
                print("Warning: No spaCy model found. Creating blank model.")
                return spacy.blank("en")
    
    def _load_skills_keywords(self) -> List[str]:
        """Load common technical and professional skills"""
        return [
            # Programming Languages
            'python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby', 'go', 'rust', 'scala',
            'typescript', 'kotlin', 'swift', 'objective-c', 'r', 'matlab', 'perl', 'shell', 'bash',
            
            # Web Technologies
            'html', 'css', 'react', 'angular', 'vue', 'node.js', 'express', 'django', 'flask',
            'spring', 'asp.net', 'laravel', 'jquery', 'bootstrap', 'sass', 'less',
            
            # Databases
            'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'sqlite', 'oracle',
            'sql server', 'cassandra', 'dynamodb', 'firebase',
            
            # Cloud & DevOps
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git', 'github', 'gitlab',
            'terraform', 'ansible', 'chef', 'puppet', 'nagios', 'prometheus',
            
            # Data Science & ML
            'machine learning', 'data science', 'tensorflow', 'pytorch', 'scikit-learn', 'pandas',
            'numpy', 'matplotlib', 'seaborn', 'jupyter', 'tableau', 'power bi', 'spark', 'hadoop',
            
            # Mobile Development
            'android', 'ios', 'react native', 'flutter', 'xamarin', 'cordova', 'ionic',
            
            # Other Technical Skills
            'api', 'rest', 'graphql', 'microservices', 'agile', 'scrum', 'kanban', 'jira',
            'confluence', 'slack', 'trello', 'linux', 'windows', 'macos', 'networking',
            
            # Soft Skills
            'leadership', 'communication', 'teamwork', 'problem solving', 'analytical',
            'project management', 'time management', 'critical thinking', 'creativity',
            'adaptability', 'collaboration', 'presentation', 'negotiation'
        ]
    
    def _load_education_keywords(self) -> List[str]:
        """Load education-related keywords"""
        return [
            'bachelor', 'master', 'phd', 'doctorate', 'associate', 'diploma', 'certificate',
            'degree', 'university', 'college', 'institute', 'school', 'academy',
            'computer science', 'engineering', 'business', 'mba', 'btech', 'mtech',
            'bsc', 'msc', 'ba', 'ma', 'bca', 'mca', 'be', 'me'
        ]
    
    def extract_candidate_data(self, text: str) -> Dict:
        """
        Extract comprehensive candidate information from resume text
        
        Args:
            text: Resume text content
            
        Returns:
            Dictionary containing extracted candidate data
        """
        # Process text with spaCy
        doc = self.nlp(text)
        
        # Extract different components
        name = self._extract_name(doc, text)
        email = self._extract_email(text)
        phone = self._extract_phone(text)
        skills = self._extract_skills(text)
        education = self._extract_education(text)
        experience_years = self._extract_experience_years(text)
        
        return {
            'name': name,
            'email': email,
            'phone': phone,
            'skills': skills,
            'education': education,
            'experience_years': experience_years
        }
    
    def _extract_name(self, doc, text: str) -> str:
        """Extract candidate name using NLP and heuristics"""
        # Method 1: Use spaCy NER to find person names
        person_names = []
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                person_names.append(ent.text.strip())
        
        if person_names:
            # Return the first person name found
            return person_names[0]
        
        # Method 2: Look for name patterns in the first few lines
        lines = text.split('\n')[:10]  # Check first 10 lines
        for line in lines:
            line = line.strip()
            if len(line) > 0 and len(line) < 50:  # Reasonable name length
                # Check if line contains only letters, spaces, and common name punctuation
                if re.match(r'^[A-Za-z\s\.\,\-\']+$', line):
                    # Avoid lines that are clearly not names
                    if not any(keyword in line.lower() for keyword in 
                              ['resume', 'cv', 'curriculum', 'address', 'email', 'phone', 'tel']):
                        words = line.split()
                        if 2 <= len(words) <= 4:  # Typical name length
                            return line
        
        return "Unknown"
    
    def _extract_email(self, text: str) -> str:
        """Extract email address using regex"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.findall(email_pattern, text)
        
        if matches:
            # Validate and return the first valid email
            for email in matches:
                try:
                    # Basic validation
                    if '@' in email and '.' in email.split('@')[1]:
                        return email.lower()
                except:
                    continue
        
        return "Not Found"
    
    def _extract_phone(self, text: str) -> str:
        """Extract phone number using regex patterns"""
        # Common phone number patterns
        phone_patterns = [
            r'\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # US format
            r'\+?91[-.\s]?\d{10}',  # Indian format with country code
            r'\d{10}',  # Simple 10-digit format
            r'\+?\d{1,3}[-.\s]?\d{3,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}'  # International
        ]
        
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            if matches:
                # Clean and return the first match
                phone = re.sub(r'[^\d+]', '', matches[0])
                if len(phone) >= 10:
                    return matches[0].strip()
        
        return "Not Found"
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills from resume text"""
        text_lower = text.lower()
        found_skills = []
        
        # Find skills from predefined list
        for skill in self.skills_keywords:
            if skill.lower() in text_lower:
                # Avoid duplicates and variations
                if not any(existing.lower() == skill.lower() for existing in found_skills):
                    found_skills.append(skill.title())
        
        # Extract skills from common sections
        skills_sections = self._find_skills_sections(text)
        for section_text in skills_sections:
            # Extract comma-separated or bullet-point skills
            section_skills = self._parse_skills_section(section_text)
            for skill in section_skills:
                if skill not in found_skills and len(skill) > 2:
                    found_skills.append(skill)
        
        return found_skills[:20]  # Limit to top 20 skills
    
    def _find_skills_sections(self, text: str) -> List[str]:
        """Find sections that likely contain skills"""
        skills_headers = [
            'skills', 'technical skills', 'core competencies', 'technologies',
            'programming languages', 'tools', 'software', 'expertise',
            'technical expertise', 'proficiencies'
        ]
        
        sections = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            for header in skills_headers:
                if header in line_lower and len(line.strip()) < 50:
                    # Found a skills header, extract the section
                    section_text = ""
                    for j in range(i + 1, min(i + 10, len(lines))):
                        if lines[j].strip():
                            section_text += lines[j] + "\n"
                        else:
                            break
                    sections.append(section_text)
                    break
        
        return sections
    
    def _parse_skills_section(self, text: str) -> List[str]:
        """Parse skills from a skills section"""
        skills = []
        
        # Split by common delimiters
        for delimiter in [',', '•', '·', '▪', '|', ';']:
            if delimiter in text:
                parts = text.split(delimiter)
                for part in parts:
                    skill = part.strip().strip('.')
                    if skill and len(skill) > 2 and len(skill) < 30:
                        skills.append(skill.title())
        
        # If no delimiters found, try line by line
        if not skills:
            lines = text.split('\n')
            for line in lines:
                line = line.strip().strip('•·▪-').strip()
                if line and len(line) > 2 and len(line) < 30:
                    skills.append(line.title())
        
        return skills
    
    def _extract_education(self, text: str) -> str:
        """Extract education information"""
        text_lower = text.lower()
        education_info = []
        
        # Look for degree keywords
        degree_patterns = [
            r'(bachelor[s]?|master[s]?|phd|doctorate|associate|diploma)\s+(?:of|in)?\s+([a-zA-Z\s]+)',
            r'(b\.?[a-z]{1,4}|m\.?[a-z]{1,4}|phd)\s+(?:in)?\s+([a-zA-Z\s]+)',
            r'(btech|mtech|be|me|bsc|msc|ba|ma|bca|mca|mba)\s+(?:in)?\s+([a-zA-Z\s]+)?'
        ]
        
        for pattern in degree_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                degree = match.group(1).title()
                field = match.group(2).title() if match.group(2) else ""
                if field:
                    education_info.append(f"{degree} in {field.strip()}")
                else:
                    education_info.append(degree)
        
        # Look for university names
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['university', 'college', 'institute']):
                if len(line) < 100:  # Reasonable length for institution name
                    education_info.append(line)
        
        return ' | '.join(education_info[:3]) if education_info else "Not Specified"
    
    def _extract_experience_years(self, text: str) -> str:
        """Extract years of experience"""
        # Pattern to find experience mentions
        experience_patterns = [
            r'(\d+)\s*(?:\+)?\s*years?\s+(?:of\s+)?experience',
            r'(\d+)\s*(?:\+)?\s*yrs?\s+(?:of\s+)?experience',
            r'experience\s*:?\s*(\d+)\s*(?:\+)?\s*years?',
            r'(\d+)\s*years?\s+(?:in|of)',
            r'over\s+(\d+)\s+years?',
            r'more than\s+(\d+)\s+years?'
        ]
        
        text_lower = text.lower()
        years_found = []
        
        for pattern in experience_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                years = int(match.group(1))
                if 0 < years < 50:  # Reasonable range for experience
                    years_found.append(years)
        
        if years_found:
            # Return the maximum years found (most likely to be total experience)
            return str(max(years_found))
        
        # Fallback: count job positions as rough experience estimate
        job_indicators = ['worked at', 'employed at', 'position', 'role', 'job']
        job_count = sum(1 for indicator in job_indicators if indicator in text_lower)
        
        if job_count > 0:
            return f"~{job_count * 2}"  # Rough estimate: 2 years per job
        
        return "Not Specified"
