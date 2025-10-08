# Overview

This is an automated resume screening system built with Streamlit that helps recruiters efficiently evaluate and rank job candidates. The system uses natural language processing (NLP) and machine learning techniques to analyze resumes against job descriptions, extract relevant information, calculate matching scores, and notify shortlisted candidates via email.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Framework**: Streamlit web application
- **State Management**: Streamlit session state for managing processed resumes, job descriptions, scored candidates, custom scoring weights, and email configuration
- **UI Components**: Wide layout with caching for component initialization to improve performance

## Backend Architecture

### Core Processing Pipeline
1. **Resume Processing** (`ResumeProcessor`)
   - Handles file extraction from PDF and DOCX formats
   - Preprocesses text for better data extraction
   - Validates resume content before processing
   - Integrates with DataExtractor for structured data extraction

2. **NLP Analysis** (`NLPAnalyzer`)
   - Uses spaCy for natural language processing
   - Implements fallback model loading strategy (en_core_web_sm → en_core_web_md → blank model)
   - Categorizes technical skills by domain (programming, web, databases, cloud, data science)
   - Provides stopword filtering and text preprocessing
   - Performs semantic analysis on job requirements

3. **Data Extraction** (`DataExtractor`)
   - Extracts structured information from unstructured resume text
   - Identifies skills, education, experience, and contact information
   - Uses predefined keyword dictionaries for common technical skills
   - Validates extracted data (e.g., email validation)

4. **Scoring System** (`ScoringEngine`)
   - Multi-factor scoring algorithm with configurable weights:
     - Skills match (35%)
     - Experience match (20%)
     - Education match (15%)
     - Keyword relevance (15%)
     - Text similarity (10%)
     - Semantic similarity (5%)
   - Uses TF-IDF vectorization and cosine similarity for text comparison
   - Implements scikit-learn for machine learning-based similarity calculations
   - Ranks candidates by overall score

5. **Notification System** (`EmailNotifier`)
   - SMTP-based email delivery
   - Configurable SMTP settings (server, port, credentials)
   - Connection validation before sending
   - Personalized notification messages for shortlisted candidates

### Design Patterns
- **Component Caching**: Uses `@st.cache_resource` to initialize components once and reuse across sessions
- **Modular Architecture**: Separation of concerns with dedicated modules for each functionality
- **Graceful Degradation**: Fallback mechanisms for missing NLP models and libraries
- **Error Handling**: Try-except blocks throughout for robust error management

## External Dependencies

### NLP and Machine Learning Libraries
- **spaCy**: Core NLP processing with English language models (en_core_web_sm/md)
- **scikit-learn**: TF-IDF vectorization and cosine similarity calculations
- **NumPy**: Numerical operations for scoring algorithms

### Document Processing
- **PyPDF2**: PDF text extraction
- **python-docx**: DOCX file parsing

### Web Framework
- **Streamlit**: Interactive web application framework

### Data Processing
- **Pandas**: Data manipulation and analysis
- **email-validator**: Email address validation

### Email Integration
- **smtplib**: SMTP protocol implementation for email sending
- **email.mime**: Email message formatting (text and multipart)

### Potential Database Integration
- Currently uses in-memory session state
- Architecture supports future integration with databases for persistent storage of:
  - Processed resumes
  - Scoring history
  - Job descriptions
  - Candidate pools