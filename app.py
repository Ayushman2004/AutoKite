import streamlit as st
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

from config import get_config
from email_client import EmailClient
from bucket_manager import BucketManager
from categorizer import EmailCategorizer


st.set_page_config(
    page_title="Smart Email Client",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_resource
def initialize_managers():
    config = get_config()
    return {
        'config': config,
        'bucket_manager': BucketManager(config.chroma),
        'categorizer': EmailCategorizer(config.ollama)
    }


class EmailApp:

    def __init__(self):
        self.managers = initialize_managers()
        self.config = self.managers['config']
        self.bucket_manager = self.managers['bucket_manager']
        self.categorizer = self.managers['categorizer']
        
        if 'buckets' not in st.session_state:
            st.session_state.buckets = self.bucket_manager.get_all_buckets()
        
        if 'categorized_emails' not in st.session_state:
            st.session_state.categorized_emails = []
        
        if 'emails_loaded' not in st.session_state:
            st.session_state.emails_loaded = False
        
        if 'selected_email' not in st.session_state:
            st.session_state.selected_email = None
    
    def render_sidebar(self):
        with st.sidebar:
            st.title("📧 Smart Email Client")
            st.markdown("---")
            
            #email
            st.subheader("📮 Account")
            st.text(f"Email: {self.config.email.email}")
            st.markdown("---")
            
            #bucket management 
            st.subheader("🗂️ Manage Buckets")
            
            #buckets
            if st.button("🔄 Refresh Buckets", use_container_width=True):
                self._load_buckets()
            
            #bucket count
            st.metric("Total Buckets", len(st.session_state.buckets))
            
            #bucket creation
            with st.expander("➕ Create New Bucket", expanded=False):
                with st.form("create_bucket_form", clear_on_submit=True):
                    new_title = st.text_input("Bucket Title", placeholder="e.g., Resignations")
                    new_prompt = st.text_area(
                        "Categorization Prompt",
                        placeholder="e.g., All emails related to employee resignations or exit formalities",
                        height=100
                    )
                    
                    submitted = st.form_submit_button("Create Bucket", use_container_width=True)
                    
                    if submitted:
                        if new_title and new_prompt:
                            self._create_bucket(new_title, new_prompt)
                        else:
                            st.error("Please fill in both title and prompt")
            
            st.markdown("---")
            
            if st.session_state.buckets:
                st.subheader("📋 Existing Buckets")
                
                for bucket in st.session_state.buckets:
                    with st.expander(f"🗂️ {bucket.title}"):
                        st.text(f"ID: {bucket.id[:8]}...")
                        st.text_area(
                            "Prompt",
                            value=bucket.prompt,
                            height=80,
                            disabled=True,
                            key=f"prompt_{bucket.id}"
                        )
                        
                        if st.button(
                            "🗑️ Delete",
                            key=f"del_{bucket.id}",
                            use_container_width=True
                        ):
                            self._delete_bucket(bucket.id)
    
    def render_main_area(self):
        if st.session_state.selected_email is not None:
            self._render_full_email()
        else:
            self._render_email_list()
    
    def _render_email_list(self):
        st.title("📬 Unread Emails")
        
        col1, col2, col3 = st.columns([2, 2, 3])
        
        with col1:
            fetch_button = st.button(
                "📥 Fetch Unread Emails",
                use_container_width=True,
                type="primary"
            )
        
        with col2:
            clear_button = st.button(
                "🗑️ Clear Display",
                use_container_width=True
            )
        
        with col3:
            if st.session_state.emails_loaded:
                st.success(f"✅ {len(st.session_state.categorized_emails)} emails loaded")
        
        #fetch emails
        if fetch_button:
            self._fetch_and_categorize_emails()
        
        #clear display
        if clear_button:
            st.session_state.categorized_emails = []
            st.session_state.emails_loaded = False
            st.session_state.selected_email = None
        
        st.markdown("---")
        
        if st.session_state.categorized_emails:
            self._render_categorized_emails()
        else:
            st.info("👆 Click 'Fetch Unread Emails' to load and categorize your emails")
    
    def _render_categorized_emails(self):
        sorted_emails = sorted(
            st.session_state.categorized_emails,
            key=lambda x: x.email.date,
            reverse=True
        )
        
        for idx, cat_email in enumerate(sorted_emails):
            email = cat_email.email
            
            with st.container():
                col1, col2, col3 = st.columns([6, 2, 1])
                
                with col1:
                    
                    
                    st.markdown(f"📧 {email.subject}")
                    st.caption(f"From: {email.sender}")
                    st.caption(f"Summary: {cat_email.summary}")

                    if st.button(f"Open Email", key=f"open_{idx}", help="Click to open"):
                        st.session_state.selected_email = cat_email
                        st.rerun()
                
                with col2:
                    st.caption(f"📁 {cat_email.bucket_title}")
                
                with col3:
                    #confidence
                    if cat_email.confidence > 0.7:
                        confidence_icon = "🟢"
                    elif cat_email.confidence > 0.4:
                        confidence_icon = "🟡"
                    else:
                        confidence_icon = "🔴"
                    st.caption(f"{confidence_icon} {cat_email.confidence:.0%}")
                
                st.markdown("---")
    
    def _render_full_email(self):
        cat_email = st.session_state.selected_email
        email = cat_email.email
        
        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("⬅️ Back to Inbox", use_container_width=True):
                st.session_state.selected_email = None
                st.rerun()
        
        st.markdown("---")
        
        st.title(f"✉️ {email.subject}")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"**From:** {email.sender}")
            st.markdown(f"**Date:** {email.date.strftime('%A, %B %d, %Y at %I:%M %p')}")
        
        with col2:
            st.markdown(f"**📁 Category:** {cat_email.bucket_title}")
            
            #confidence 
            if cat_email.confidence > 0.7:
                confidence_color = "🟢"
                confidence_label = "High"
            elif cat_email.confidence > 0.4:
                confidence_color = "🟡"
                confidence_label = "Medium"
            else:
                confidence_color = "🔴"
                confidence_label = "Low"
            
            st.markdown(f"**Confidence:** {confidence_color} {confidence_label} ({cat_email.confidence:.0%})")
        
        st.markdown("---")

        st.markdown("##### 📄 Summary")

        st.caption(f"{cat_email.summary}")


        st.markdown("---")
        
        st.markdown("### 📄 Email Content")
        
        st.text_area(
            label="",
            value=email.body,
            height=500,
            disabled=True,
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 1, 3]) #-------------------------------------------  why are there 3 cols
        
        with col1:
            if st.button("⬅️ Back", use_container_width=True, type="primary"):
                st.session_state.selected_email = None
                st.rerun()
    
    def _load_buckets(self):
        try:
            with st.spinner("Loading buckets..."):
                st.session_state.buckets = self.bucket_manager.get_all_buckets()
            st.success(f"Loaded {len(st.session_state.buckets)} buckets")
        except Exception as e:
            st.error(f"Failed to load buckets: {str(e)}")
    
    def _create_bucket(self, title: str, prompt: str):
        try:
            if st.session_state.get("creating_bucket", False):
                return
            st.session_state["creating_bucket"] = True
            with st.spinner("Creating bucket..."):
                bucket = self.bucket_manager.create_bucket(title, prompt)
                st.session_state.buckets.append(bucket)
            st.success(f"✅ Created bucket: {title}")
        except Exception as e:
            st.error(f"Failed to create bucket: {str(e)}")
        finally:
            st.session_state["creating_bucket"] = False
    
    def _delete_bucket(self, bucket_id: str):
        try:
            with st.spinner("Deleting bucket..."):
                if self.bucket_manager.delete_bucket(bucket_id):
                    st.session_state.buckets = [
                        b for b in st.session_state.buckets if b.id != bucket_id
                    ]
            st.success("✅ Bucket deleted")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to delete bucket: {str(e)}")
    
    def _fetch_and_categorize_emails(self):
        try:
            buckets = self.bucket_manager.get_all_buckets()
            st.session_state.buckets = buckets
            
            if not buckets:
                st.warning("⚠️ No buckets found. Create buckets first to categorize emails.")
                return
            
            with st.spinner("📥 Fetching unread emails..."):
                with EmailClient(self.config.email) as client:
                    emails = client.fetch_unread_emails(limit=50)
            
            if not emails:
                st.info("📭 No unread emails found")
                return
            
            st.info(f"📬 Found {len(emails)} unread emails")
            
            #categorize emails
            with st.spinner("🤖 Categorizing emails with AI..."):
                progress_bar = st.progress(0)
                categorized = []
                
                for i, email in enumerate(emails):
                    cat_email = self.categorizer.categorize_email(email, buckets)
                    categorized.append(cat_email)
                    progress_bar.progress((i + 1) / len(emails))
                
                progress_bar.empty()
            
            st.session_state.categorized_emails = categorized
            st.session_state.emails_loaded = True
            
            st.success(f"✅ Categorized {len(categorized)} emails successfully!")
        
        except Exception as e:
            st.error(f"Error: {str(e)}")
            logging.exception("Email fetch/categorization error")
    
    def run(self):
        self.render_sidebar()
        self.render_main_area()


def main():
    try:
        app = EmailApp()
        app.run()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        logging.exception("Application startup error")


if __name__ == "__main__":
    main()
