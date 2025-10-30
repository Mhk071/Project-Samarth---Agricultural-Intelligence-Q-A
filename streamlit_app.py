import streamlit as st
import requests
import json
import time

# Configure the page
st.set_page_config(
    page_title="Project Samarth - Agricultural Q&A",
    page_icon="🌾",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E8B57;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #228B22;
        margin-bottom: 1rem;
    }
    .answer-box {
        background-color: #f0f8f0;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #2E8B57;
        margin: 1rem 0;
    }
    .source-box {
        background-color: #e6f3ff;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        font-size: 0.9rem;
    }
    .argument-box {
        background-color: #fffacd;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #ffd700;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #28a745;
    }
    .error-box {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #dc3545;
    }
</style>
""", unsafe_allow_html=True)

# Backend configuration
BACKEND_URL = "http://localhost:8000"

def check_backend_health():
    """Check if backend server is running"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def send_question_to_backend(question: str):
    """Send question to backend API and get response"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/ask",
            json={"question": question},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"Backend error: {response.status_code} - {response.text}"
    
    except requests.exceptions.ConnectionError:
        return None, "Backend service is not running. Please start the backend server first."
    except requests.exceptions.Timeout:
        return None, "Request timeout. The backend is taking too long to respond."
    except Exception as e:
        return None, f"Error connecting to backend: {str(e)}"

def display_answer(result):
    """Display the answer and sources in a formatted way"""
    if not result:
        return
    
    # Display answer
    st.markdown("## 📊 Analysis Results")
    st.markdown(f'<div class="answer-box">{result["answer"]}</div>', unsafe_allow_html=True)
    
    # Display sources
    if result.get("sources"):
        st.markdown("## 📚 Data Sources")
        for source in result["sources"]:
            st.markdown(f'''
            <div class="source-box">
                <strong>{source["name"]}</strong><br>
                {source["description"]}<br>
                <em>URL: {source["url"]}</em>
            </div>
            ''', unsafe_allow_html=True)
    
    # Show raw data points (collapsible)
    if result.get("data_points"):
        with st.expander("🔍 View Detailed Data Points"):
            st.json(result["data_points"])

def display_backend_status():
    """Display backend connection status"""
    if check_backend_health():
        st.markdown('<div class="success-box">✅ Backend server is connected and running</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'''
        <div class="error-box">
            ❌ Backend server is not available
            <br><br>
            <strong>To fix this:</strong>
            <ol>
            <li>Make sure your backend server is running on {BACKEND_URL}</li>
            <li>Run the backend with: <code>python app.py</code></li>
            <li>Check that port 8000 is not being used by another application</li>
            </ol>
        </div>
        ''', unsafe_allow_html=True)
        return False
    return True

# Main Streamlit UI
def main():
    st.markdown('<div class="main-header">🌾 Project Samarth - Agricultural Intelligence Q&A</div>', unsafe_allow_html=True)
    st.markdown("### Ask complex questions about Indian agriculture and climate data")
    
    # Display backend status
    st.markdown("### 🔌 Connection Status")
    is_backend_ready = display_backend_status()
    
    # Sidebar with information
    with st.sidebar:
        st.header("ℹ️ About Project Samarth")
        st.info("""
        **Integrated Data Sources:**
        - Ministry of Agriculture & Farmers Welfare
        - India Meteorological Department (IMD)
        - data.gov.in portals
        
        **Architecture:**
        - Frontend: Streamlit UI
        - Backend: FastAPI Server
        - Data: Real-time from government portals
        """)
        
        st.header("🎯 Sample Questions")
        sample_questions = [
            "What are arguments to promote drought-resistant crops in Rajasthan?",
            "Compare crop production in Rajasthan and Punjab",
            "Analyze rainfall trends in Rajasthan over the last 5 years",
            "Which crops are most suitable for arid regions?",
            "Compare water requirements of Bajra vs Rice in Rajasthan"
        ]
        
        for i, question in enumerate(sample_questions):
            if st.button(question, key=f"sample_{i}"):
                st.session_state.question = question
                st.rerun()
        
        st.header("⚙️ Backend Info")
        st.write(f"**Backend URL:** {BACKEND_URL}")
        st.write("**Status:** ✅ Connected" if is_backend_ready else "**Status:** ❌ Disconnected")
        
        if st.button("🔄 Check Connection"):
            st.rerun()
    
    # Main interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Question input
        question = st.text_area(
            "**Ask your question:**",
            placeholder="e.g., What are arguments to promote drought-resistant crops in Rajasthan?",
            height=100,
            key="question_input"
        )
        
        # Process question
        if st.button("🚀 Get Data-Backed Answer", type="primary", disabled=not is_backend_ready):
            if question.strip():
                with st.spinner("🔍 Analyzing data sources and generating insights..."):
                    result, error = send_question_to_backend(question)
                    
                    if error:
                        st.markdown(f'<div class="error-box">{error}</div>', unsafe_allow_html=True)
                    else:
                        display_answer(result)
            else:
                st.warning("⚠️ Please enter a question")
    
    with col2:
        st.markdown("### 💡 Question Tips")
        st.write("""
        **Best practices:**
        - Mention specific states or crops
        - Ask for comparisons or trends  
        - Request policy arguments with data
        - Use terms like 'drought-resistant'
        - Include time periods when relevant
        """)
        
        st.markdown("### 🌾 Available Data")
        st.write("""
        **States:** Rajasthan, Punjab, Gujarat
        **Crops:** Bajra, Wheat, Rice, Cotton
        **Years:** 2018-2022
        **Metrics:** Production, Rainfall, Water use
        """)
    
    # Handle session state for sample questions
    if 'question' in st.session_state:
        # This will automatically populate the text area on the next run
        # We use JavaScript to set the value (via a hack since Streamlit doesn't directly support this)
        st.components.v1.html(f"""
        <script>
            var textArea = document.querySelector("textarea");
            if (textArea) {{
                textArea.value = `{st.session_state.question}`;
                textArea.dispatchEvent(new Event('input', {{ bubbles: true }}));
            }}
        </script>
        """, height=0)
        
        # Clear the session state after setting
        del st.session_state.question
    
    # Footer
    st.markdown("---")
    st.markdown(
        "**🌾 Project Samarth** - Intelligent Q&A System | "
        "Frontend: Streamlit | Backend: FastAPI | "
        "Data: Ministry of Agriculture & IMD"
    )

if __name__ == "__main__":
    main()