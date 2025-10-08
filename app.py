import streamlit as st
import pandas as pd
import os
import tempfile
from datetime import datetime
import base64
from resume_processor import ResumeProcessor
from nlp_analyzer import NLPAnalyzer
from scoring_engine import ScoringEngine
from email_notifier import EmailNotifier

# Page configuration
st.set_page_config(
    page_title="Resume Screening System",
    page_icon="📄",
    layout="wide"
)

# Initialize components
@st.cache_resource
def init_components():
    nlp_analyzer = NLPAnalyzer()
    scoring_engine = ScoringEngine()
    resume_processor = ResumeProcessor()
    email_notifier = EmailNotifier()
    return nlp_analyzer, scoring_engine, resume_processor, email_notifier

nlp_analyzer, scoring_engine, resume_processor, email_notifier = init_components()

# Initialize session state
if 'processed_resumes' not in st.session_state:
    st.session_state.processed_resumes = []
if 'job_description' not in st.session_state:
    st.session_state.job_description = ""
if 'scored_candidates' not in st.session_state:
    st.session_state.scored_candidates = []
if 'custom_weights' not in st.session_state:
    st.session_state.custom_weights = {
        'skills_match': 35,
        'experience_match': 20,
        'education_match': 15,
        'keyword_relevance': 15,
        'text_similarity': 10,
        'semantic_similarity': 5
    }
if 'email_configured' not in st.session_state:
    st.session_state.email_configured = False

# Main app
st.title("🎯 Automated Resume Screening System")
st.markdown("Upload resumes and job descriptions to automatically screen and rank candidates using NLP.")

# Sidebar for job description
with st.sidebar:
    st.header("📋 Job Description")
    job_description = st.text_area(
        "Enter the job description with required skills and qualifications:",
        value=st.session_state.job_description,
        height=300,
        placeholder="Enter job requirements, skills, qualifications, and responsibilities..."
    )
    
    if job_description != st.session_state.job_description:
        st.session_state.job_description = job_description
        # Clear previous scores when job description changes
        st.session_state.scored_candidates = []
    
    st.markdown("---")
    
    # Scoring weights configuration
    st.header("⚖️ Scoring Weights")
    with st.expander("Customize Scoring Criteria", expanded=False):
        st.markdown("Adjust the importance of each scoring criterion (total must equal 100%):")
        
        skills_weight = st.slider("Skills Match", 0, 100, st.session_state.custom_weights['skills_match'], 
                                   key="skills_weight_slider",
                                   help="Weight for matching candidate skills with job requirements")
        experience_weight = st.slider("Experience Match", 0, 100, st.session_state.custom_weights['experience_match'],
                                       key="experience_weight_slider",
                                       help="Weight for matching years of experience")
        education_weight = st.slider("Education Match", 0, 100, st.session_state.custom_weights['education_match'],
                                      key="education_weight_slider",
                                      help="Weight for matching education level")
        keyword_weight = st.slider("Keyword Relevance", 0, 100, st.session_state.custom_weights['keyword_relevance'],
                                    key="keyword_weight_slider",
                                    help="Weight for presence of important keywords")
        text_similarity_weight = st.slider("Text Similarity", 0, 100, st.session_state.custom_weights['text_similarity'],
                                           key="text_similarity_weight_slider",
                                           help="Weight for overall text similarity")
        semantic_weight = st.slider("Semantic Similarity", 0, 100, st.session_state.custom_weights['semantic_similarity'],
                                     key="semantic_weight_slider",
                                     help="Weight for advanced semantic matching")
        
        total_weight = skills_weight + experience_weight + education_weight + keyword_weight + text_similarity_weight + semantic_weight
        
        if total_weight != 100:
            st.warning(f"⚠️ Total weight is {total_weight}%. Please adjust to equal 100%.")
        else:
            st.success("✅ Weights are balanced!")
            
            # Update weights if changed
            new_weights = {
                'skills_match': skills_weight,
                'experience_match': experience_weight,
                'education_match': education_weight,
                'keyword_relevance': keyword_weight,
                'text_similarity': text_similarity_weight,
                'semantic_similarity': semantic_weight
            }
            
            if new_weights != st.session_state.custom_weights:
                st.session_state.custom_weights = new_weights
                # Clear scores to trigger re-scoring with new weights
                st.session_state.scored_candidates = []
        
        if st.button("Reset to Default Weights", key="reset_weights_btn"):
            # Reset the weights in session state
            default_weights = {
                'skills_match': 35,
                'experience_match': 20,
                'education_match': 15,
                'keyword_relevance': 15,
                'text_similarity': 10,
                'semantic_similarity': 5
            }
            st.session_state.custom_weights = default_weights
            st.session_state.scored_candidates = []
            
            # Reset slider states with correct keys
            st.session_state['skills_weight_slider'] = 35
            st.session_state['experience_weight_slider'] = 20
            st.session_state['education_weight_slider'] = 15
            st.session_state['keyword_weight_slider'] = 15
            st.session_state['text_similarity_weight_slider'] = 10
            st.session_state['semantic_weight_slider'] = 5
            
            st.success("✅ Weights reset to defaults!")
            st.rerun()
    
    st.markdown("---")
    
    # Processing controls
    if st.button("🔄 Clear All Data", type="secondary"):
        st.session_state.processed_resumes = []
        st.session_state.scored_candidates = []
        st.session_state.job_description = ""
        st.rerun()

# Main content area
col1, col2 = st.columns([1, 2])

with col1:
    st.header("📁 Upload Resumes")
    
    uploaded_files = st.file_uploader(
        "Choose resume files",
        type=['pdf', 'docx', 'doc'],
        accept_multiple_files=True,
        help="Upload PDF or Word documents containing candidate resumes"
    )
    
    if uploaded_files:
        if st.button("📤 Process Uploaded Resumes", type="primary"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            processed_count = 0
            total_files = len(uploaded_files)
            
            for i, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"Processing {uploaded_file.name}...")
                
                try:
                    # Create temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_file_path = tmp_file.name
                    
                    # Process resume
                    extracted_data = resume_processor.extract_resume_data(tmp_file_path, uploaded_file.name)
                    
                    if extracted_data:
                        # Check if resume already processed (by filename)
                        existing_resume = next((r for r in st.session_state.processed_resumes if r['filename'] == uploaded_file.name), None)
                        
                        if not existing_resume:
                            st.session_state.processed_resumes.append(extracted_data)
                            processed_count += 1
                    
                    # Clean up temp file
                    os.unlink(tmp_file_path)
                    
                except Exception as e:
                    st.error(f"Error processing {uploaded_file.name}: {str(e)}")
                
                progress_bar.progress((i + 1) / total_files)
            
            status_text.text(f"Processed {processed_count} new resumes!")
            
            if processed_count > 0:
                st.success(f"Successfully processed {processed_count} resumes!")
                # Clear scored candidates to trigger re-scoring
                st.session_state.scored_candidates = []

with col2:
    st.header("📊 Resume Analysis")
    
    if st.session_state.processed_resumes and st.session_state.job_description:
        if not st.session_state.scored_candidates or st.button("🎯 Score Resumes", type="primary"):
            with st.spinner("Scoring resumes against job description..."):
                # Update scoring engine weights
                scoring_engine.weights = {k: v/100 for k, v in st.session_state.custom_weights.items()}
                
                scored_candidates = scoring_engine.score_candidates(
                    st.session_state.processed_resumes,
                    st.session_state.job_description
                )
                st.session_state.scored_candidates = scored_candidates
        
        if st.session_state.scored_candidates:
            st.success(f"Analyzed {len(st.session_state.scored_candidates)} candidates")
            
            # Display summary statistics
            scores = [c['overall_score'] for c in st.session_state.scored_candidates]
            col_stats1, col_stats2, col_stats3 = st.columns(3)
            
            with col_stats1:
                st.metric("Average Score", f"{sum(scores)/len(scores):.1f}%")
            with col_stats2:
                st.metric("Top Score", f"{max(scores):.1f}%")
            with col_stats3:
                qualified_candidates = len([s for s in scores if s >= 70])
                st.metric("Qualified (≥70%)", qualified_candidates)
    
    elif not st.session_state.job_description:
        st.info("Please enter a job description in the sidebar to start scoring resumes.")
    elif not st.session_state.processed_resumes:
        st.info("Please upload and process resumes to begin analysis.")

# Results section
if st.session_state.scored_candidates:
    st.header("🏆 Candidate Rankings")
    
    # Filter and sort options
    col_filter1, col_filter2, col_filter3 = st.columns(3)
    
    with col_filter1:
        min_score = st.slider("Minimum Score", 0, 100, 0, help="Filter candidates by minimum score")
    
    with col_filter2:
        sort_by = st.selectbox("Sort by", ["Overall Score", "Skills Match", "Experience Match"], index=0)
    
    with col_filter3:
        show_top_n = st.selectbox("Show top", [5, 10, 20, "All"], index=1)
    
    # Filter candidates
    filtered_candidates = [c for c in st.session_state.scored_candidates if c['overall_score'] >= min_score]
    
    # Sort candidates
    sort_key_map = {
        "Overall Score": "overall_score",
        "Skills Match": "skills_score",
        "Experience Match": "experience_score"
    }
    filtered_candidates.sort(key=lambda x: x[sort_key_map[sort_by]], reverse=True)
    
    # Limit results
    if show_top_n != "All":
        filtered_candidates = filtered_candidates[:show_top_n]
    
    if filtered_candidates:
        # Create results DataFrame for display
        results_data = []
        for i, candidate in enumerate(filtered_candidates, 1):
            results_data.append({
                'Rank': i,
                'Name': candidate.get('name', 'N/A'),
                'Email': candidate.get('email', 'N/A'),
                'Overall Score': f"{candidate['overall_score']:.1f}%",
                'Skills Score': f"{candidate['skills_score']:.1f}%",
                'Experience Score': f"{candidate['experience_score']:.1f}%",
                'Education': candidate.get('education', 'N/A'),
                'Experience Years': candidate.get('experience_years', 'N/A'),
                'Top Skills': ', '.join(candidate.get('skills', [])[:5])  # Show top 5 skills
            })
        
        df_results = pd.DataFrame(results_data)
        st.dataframe(df_results, use_container_width=True, hide_index=True)
        
        # Export functionality
        st.header("📥 Export Results")
        col_export1, col_export2 = st.columns(2)
        
        with col_export1:
            # CSV Export
            csv_data = []
            for candidate in filtered_candidates:
                csv_data.append({
                    'Name': candidate.get('name', 'N/A'),
                    'Email': candidate.get('email', 'N/A'),
                    'Phone': candidate.get('phone', 'N/A'),
                    'Overall_Score': round(candidate['overall_score'], 1),
                    'Skills_Score': round(candidate['skills_score'], 1),
                    'Experience_Score': round(candidate['experience_score'], 1),
                    'Education': candidate.get('education', 'N/A'),
                    'Experience_Years': candidate.get('experience_years', 'N/A'),
                    'Skills': '; '.join(candidate.get('skills', [])),
                    'Filename': candidate.get('filename', 'N/A'),
                    'Analysis_Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            
            df_export = pd.DataFrame(csv_data)
            csv_string = df_export.to_csv(index=False)
            
            st.download_button(
                label="📊 Download CSV Report",
                data=csv_string,
                file_name=f"resume_screening_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                type="primary"
            )
        
        with col_export2:
            # Shortlisted candidates (score >= 70%)
            shortlisted = [c for c in filtered_candidates if c['overall_score'] >= 70]
            if shortlisted:
                shortlisted_df = pd.DataFrame([{
                    'Name': c.get('name', 'N/A'),
                    'Email': c.get('email', 'N/A'),
                    'Phone': c.get('phone', 'N/A'),
                    'Overall_Score': round(c['overall_score'], 1),
                    'Skills': '; '.join(c.get('skills', [])),
                    'Education': c.get('education', 'N/A')
                } for c in shortlisted])
                
                shortlisted_csv = shortlisted_df.to_csv(index=False)
                
                st.download_button(
                    label="⭐ Download Shortlisted Only",
                    data=shortlisted_csv,
                    file_name=f"shortlisted_candidates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        # Email Notification Section
        shortlisted = [c for c in filtered_candidates if c['overall_score'] >= 70]
        if shortlisted:
            st.header("📧 Email Notifications")
            st.markdown(f"Send automated notifications to {len(shortlisted)} shortlisted candidates")
            
            with st.expander("Configure Email Settings"):
                col_email1, col_email2 = st.columns(2)
                
                with col_email1:
                    job_title = st.text_input("Job Title", placeholder="e.g., Senior Software Engineer")
                    company_name = st.text_input("Company Name", placeholder="e.g., Tech Company Inc.")
                    smtp_server = st.text_input("SMTP Server", placeholder="e.g., smtp.gmail.com", help="Your email provider's SMTP server")
                    smtp_port = st.number_input("SMTP Port", value=587, min_value=1, max_value=65535)
                
                with col_email2:
                    sender_email = st.text_input("Sender Email", placeholder="recruiter@company.com")
                    sender_password = st.text_input("Email Password", type="password", help="Use app-specific password for Gmail")
                    custom_message = st.text_area("Custom Message (Optional)", placeholder="Additional message for candidates...")
                
                if st.button("✉️ Send Notifications to Shortlisted Candidates", type="primary"):
                    if not all([job_title, company_name, smtp_server, sender_email, sender_password]):
                        st.error("Please fill in all required email configuration fields")
                    else:
                        with st.spinner("Configuring email settings..."):
                            if email_notifier.configure_smtp(smtp_server, smtp_port, sender_email, sender_password):
                                st.session_state.email_configured = True
                                
                                with st.spinner(f"Sending emails to {len(shortlisted)} candidates..."):
                                    results = email_notifier.send_batch_notifications(
                                        shortlisted,
                                        job_title,
                                        company_name,
                                        custom_message
                                    )
                                    
                                    if results['success'] > 0:
                                        st.success(f"✅ Successfully sent {results['success']} email(s)")
                                    if results['failed'] > 0:
                                        st.warning(f"⚠️ Failed to send {results['failed']} email(s)")
                            else:
                                st.error("Failed to configure email settings. Please check your SMTP credentials.")
                
                st.info("💡 **Tip:** For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833) instead of your regular password")
        
        # Detailed candidate view
        st.header("🔍 Detailed Candidate Analysis")
        
        if filtered_candidates:
            selected_candidate_index = st.selectbox(
                "Select candidate for detailed view:",
                range(len(filtered_candidates)),
                format_func=lambda x: f"{filtered_candidates[x].get('name', 'N/A')} ({filtered_candidates[x]['overall_score']:.1f}%)"
            )
            
            if selected_candidate_index is not None:
                candidate = filtered_candidates[selected_candidate_index]
                
                col_detail1, col_detail2 = st.columns(2)
                
                with col_detail1:
                    st.subheader("📋 Basic Information")
                    st.write(f"**Name:** {candidate.get('name', 'N/A')}")
                    st.write(f"**Email:** {candidate.get('email', 'N/A')}")
                    st.write(f"**Phone:** {candidate.get('phone', 'N/A')}")
                    st.write(f"**Education:** {candidate.get('education', 'N/A')}")
                    st.write(f"**Experience:** {candidate.get('experience_years', 'N/A')} years")
                    
                    st.subheader("🎯 Scoring Breakdown")
                    st.write(f"**Overall Score:** {candidate['overall_score']:.1f}%")
                    st.write(f"**Skills Match:** {candidate['skills_score']:.1f}%")
                    st.write(f"**Experience Match:** {candidate['experience_score']:.1f}%")
                
                with col_detail2:
                    st.subheader("💼 Skills")
                    skills = candidate.get('skills', [])
                    if skills:
                        for skill in skills[:10]:  # Show top 10 skills
                            st.write(f"• {skill}")
                    else:
                        st.write("No skills extracted")
                    
                    st.subheader("📄 Resume Content Preview")
                    content_preview = candidate.get('raw_text', '')[:500]
                    if content_preview:
                        st.text_area("Content Preview", content_preview, height=200, disabled=True)
                    else:
                        st.write("No content preview available")
    
    else:
        st.warning(f"No candidates found with score >= {min_score}%")

else:
    st.info("Process resumes and enter a job description to see candidate rankings.")

# Candidate Comparison View
if st.session_state.scored_candidates and len(st.session_state.scored_candidates) >= 2:
    st.markdown("---")
    st.header("⚖️ Candidate Comparison")
    st.markdown("Compare multiple candidates side-by-side to make better hiring decisions")
    
    # Select candidates to compare
    col_comp1, col_comp2, col_comp3 = st.columns(3)
    
    with col_comp1:
        candidate1_idx = st.selectbox(
            "Candidate 1",
            range(len(st.session_state.scored_candidates)),
            format_func=lambda x: f"{st.session_state.scored_candidates[x].get('name', 'N/A')} ({st.session_state.scored_candidates[x]['overall_score']:.1f}%)",
            key="compare_candidate_1"
        )
    
    with col_comp2:
        candidate2_idx = st.selectbox(
            "Candidate 2",
            range(len(st.session_state.scored_candidates)),
            format_func=lambda x: f"{st.session_state.scored_candidates[x].get('name', 'N/A')} ({st.session_state.scored_candidates[x]['overall_score']:.1f}%)",
            index=min(1, len(st.session_state.scored_candidates)-1),
            key="compare_candidate_2"
        )
    
    with col_comp3:
        # Optional third candidate
        compare_three = st.checkbox("Add 3rd candidate", key="compare_three_toggle")
        if compare_three and len(st.session_state.scored_candidates) >= 3:
            candidate3_idx = st.selectbox(
                "Candidate 3",
                range(len(st.session_state.scored_candidates)),
                format_func=lambda x: f"{st.session_state.scored_candidates[x].get('name', 'N/A')} ({st.session_state.scored_candidates[x]['overall_score']:.1f}%)",
                index=min(2, len(st.session_state.scored_candidates)-1),
                key="compare_candidate_3"
            )
        else:
            candidate3_idx = None
    
    # Get selected candidates
    candidates_to_compare = [
        st.session_state.scored_candidates[candidate1_idx],
        st.session_state.scored_candidates[candidate2_idx]
    ]
    if candidate3_idx is not None:
        candidates_to_compare.append(st.session_state.scored_candidates[candidate3_idx])
    
    # Display comparison
    st.markdown("### 📊 Score Comparison")
    
    # Create comparison columns
    comp_cols = st.columns(len(candidates_to_compare))
    
    for idx, (col, candidate) in enumerate(zip(comp_cols, candidates_to_compare)):
        with col:
            st.markdown(f"#### {candidate.get('name', 'N/A')}")
            st.metric("Overall Score", f"{candidate['overall_score']:.1f}%")
            
            # Score breakdown chart
            st.markdown("**Score Breakdown:**")
            score_data = {
                'Skills': candidate['skills_score'],
                'Experience': candidate['experience_score'],
                'Education': candidate['education_score'],
                'Keywords': candidate['keyword_score'],
                'Similarity': candidate['similarity_score']
            }
            
            for criterion, score in score_data.items():
                st.progress(score / 100, text=f"{criterion}: {score:.1f}%")
    
    # Detailed comparison table
    st.markdown("### 📋 Detailed Comparison")
    
    comparison_data = {
        'Criterion': []
    }
    
    # Create unique column names for each candidate
    for idx, candidate in enumerate(candidates_to_compare):
        name = candidate.get('name', 'Unknown')
        # Add index or email to make unique if needed
        if name in comparison_data:
            # If name exists, add email or index to make it unique
            email = candidate.get('email', '')
            if email and email != 'Not Found':
                unique_name = f"{name} ({email})"
            else:
                unique_name = f"{name} (#{idx+1})"
        else:
            unique_name = name
        comparison_data[unique_name] = []
    
    # Add comparison rows
    criteria = [
        ('Name', 'name'),
        ('Email', 'email'),
        ('Phone', 'phone'),
        ('Education', 'education'),
        ('Experience', 'experience_years'),
        ('Overall Score', 'overall_score'),
        ('Skills Score', 'skills_score'),
        ('Experience Score', 'experience_score'),
        ('Education Score', 'education_score'),
        ('Top 5 Skills', 'skills')
    ]
    
    for criterion_name, key in criteria:
        comparison_data['Criterion'].append(criterion_name)
        
        for idx, candidate in enumerate(candidates_to_compare):
            if key == 'skills':
                value = ', '.join(candidate.get(key, [])[:5])
            elif key in ['overall_score', 'skills_score', 'experience_score', 'education_score']:
                value = f"{candidate.get(key, 0):.1f}%"
            else:
                value = str(candidate.get(key, 'N/A'))
            
            # Get the unique column name for this candidate
            name = candidate.get('name', 'Unknown')
            col_name = None
            for col in comparison_data.keys():
                if col == 'Criterion':
                    continue
                if col.startswith(name):
                    # Check if this is the right candidate by index
                    candidate_idx = list(comparison_data.keys()).index(col) - 1
                    if candidate_idx == idx:
                        col_name = col
                        break
            
            if col_name:
                comparison_data[col_name].append(value)
    
    df_comparison = pd.DataFrame(comparison_data)
    st.dataframe(df_comparison, use_container_width=True, hide_index=True)
    
    # Strengths and weaknesses comparison
    st.markdown("### 💡 Analysis Summary")
    
    analysis_cols = st.columns(len(candidates_to_compare))
    
    for col, candidate in zip(analysis_cols, candidates_to_compare):
        with col:
            st.markdown(f"**{candidate.get('name', 'N/A')}**")
            
            # Strengths
            st.markdown("**Strengths:**")
            if candidate['skills_score'] >= 80:
                st.success("✓ Excellent skill match")
            if candidate['experience_score'] >= 80:
                st.success("✓ Strong experience level")
            if candidate['education_score'] >= 80:
                st.success("✓ Good educational fit")
            
            # Areas for improvement
            st.markdown("**Areas to Consider:**")
            if candidate['skills_score'] < 50:
                st.warning("⚠ Limited skill overlap")
            if candidate['experience_score'] < 50:
                st.warning("⚠ Experience gap")
            if candidate['education_score'] < 50:
                st.warning("⚠ Education mismatch")

# Footer
st.markdown("---")
st.markdown(
    "Built with ❤️ using Streamlit, spaCy, and scikit-learn | "
    "📧 For support or questions, please contact your system administrator"
)
