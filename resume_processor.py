import PyPDF2
import docx
import os
import re
from typing import Dict, Optional, List
from data_extractor import DataExtractor

class ResumeProcessor:
    """Handles resume file processing and text extraction"""
    
    def __init__(self):
        self.data_extractor = DataExtractor()
    
    def extract_resume_data(self, file_path: str, filename: str) -> Optional[Dict]:
        """
        Extract data from resume file
        
        Args:
            file_path: Path to the resume file
            filename: Original filename
            
        Returns:
            Dictionary containing extracted resume data
        """
        try:
            # Extract text based on file type
            text = self._extract_text_from_file(file_path)
            
            if not text or len(text.strip()) < 50:
                return None
            
            # Extract structured data using NLP
            extracted_data = self.data_extractor.extract_candidate_data(text)
            
            # Add metadata
            extracted_data.update({
                'filename': filename,
                'raw_text': text,
                'file_size': os.path.getsize(file_path) if os.path.exists(file_path) else 0
            })
            
            return extracted_data
            
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
            return None
    
    def _extract_text_from_file(self, file_path: str) -> str:
        """
        Extract text from PDF or Word document
        
        Args:
            file_path: Path to the document
            
        Returns:
            Extracted text content
        """
        text = ""
        file_extension = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_extension == '.pdf':
                text = self._extract_from_pdf(file_path)
            elif file_extension in ['.docx', '.doc']:
                text = self._extract_from_docx(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")
                
        except Exception as e:
            print(f"Error extracting text from {file_path}: {str(e)}")
            
        return text
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        text = ""
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
                    
        except Exception as e:
            print(f"Error reading PDF {file_path}: {str(e)}")
            # Fallback: try with pdfplumber if PyPDF2 fails
            try:
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            except ImportError:
                print("pdfplumber not available for fallback PDF extraction")
            except Exception as e2:
                print(f"Fallback PDF extraction also failed: {str(e2)}")
        
        return text
    
    def _extract_from_docx(self, file_path: str) -> str:
        """Extract text from Word document"""
        text = ""
        
        try:
            doc = docx.Document(file_path)
            
            # Extract text from paragraphs
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            # Extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        text += cell.text + " "
                    text += "\n"
                    
        except Exception as e:
            print(f"Error reading Word document {file_path}: {str(e)}")
        
        return text
    
    def validate_resume_content(self, text: str) -> bool:
        """
        Validate if the extracted text appears to be a resume
        
        Args:
            text: Extracted text content
            
        Returns:
            True if content appears to be a resume
        """
        if not text or len(text.strip()) < 100:
            return False
        
        # Check for common resume indicators
        resume_indicators = [
            'experience', 'education', 'skills', 'work', 'employment',
            'university', 'college', 'degree', 'job', 'position',
            'resume', 'cv', 'curriculum vitae', 'qualifications'
        ]
        
        text_lower = text.lower()
        indicator_count = sum(1 for indicator in resume_indicators if indicator in text_lower)
        
        # Should have at least 3 resume indicators
        return indicator_count >= 3
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize extracted text
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\@\(\)\[\]\/]', '', text)
        
        # Remove multiple consecutive dots or dashes
        text = re.sub(r'\.{3,}', '...', text)
        text = re.sub(r'-{3,}', '---', text)
        
        return text.strip()
