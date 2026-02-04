import streamlit as st
import pandas as pd
import mysql.connector
from mysql.connector import Error
import json
import openpyxl
from io import BytesIO

# Page configuration
st.set_page_config(
    page_title="Course Management System",
    page_icon="📚",
    layout="wide"
)

# Custom CSS for Excel-like appearance
st.markdown("""
<style>
    .stDataFrame {
        border: 1px solid #ddd;
    }
    div[data-testid="stDataFrameResizable"] {
        border: 2px solid #4CAF50;
    }
    .main {
        padding: 2rem;
    }
    h1 {
        color: #2C3E50;
        border-bottom: 3px solid #4CAF50;
        padding-bottom: 10px;
    }
    .success-box {
        padding: 10px;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 4px;
        color: #155724;
        margin: 10px 0;
    }
    .error-box {
        padding: 10px;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 4px;
        color: #721c24;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'phpmyadmin',
    'password': '123',  # Change this to your MySQL password
    'database': 'test'
}

# Initialize session state
if 'refresh' not in st.session_state:
    st.session_state.refresh = 0

def get_db_connection():
    """Create and return a database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        st.error(f"Error connecting to MySQL: {e}")
        return None

def create_database_and_table():
    """Create database and table if they don't exist"""
    try:
        # Connect without database
        conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        cursor = conn.cursor()
        
        # Create database
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        cursor.execute(f"USE {DB_CONFIG['database']}")
        
        # Create table
        create_table_query = """
        CREATE TABLE IF NOT EXISTS tbl_courses (
            row_id INT AUTO_INCREMENT PRIMARY KEY,
            course_code VARCHAR(10) NOT NULL,
            course_name VARCHAR(50) NOT NULL,
            course_credits INT NOT NULL,
            sessions_per_week INT NOT NULL
        )
        """
        cursor.execute(create_table_query)
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Error as e:
        st.error(f"Error creating database/table: {e}")
        return False

def fetch_all_courses():
    """Fetch all courses from database"""
    conn = get_db_connection()
    if conn:
        try:
            query = "SELECT row_id, course_code, course_name, course_credits, sessions_per_week FROM tbl_courses ORDER BY row_id"
            df = pd.read_sql(query, conn)
            conn.close()
            return df
        except Error as e:
            st.error(f"Error fetching data: {e}")
            conn.close()
            return pd.DataFrame()
    return pd.DataFrame()

def insert_course(course_code, course_name, course_credits, sessions_per_week):
    """Insert a new course record"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            query = """
            INSERT INTO tbl_courses (course_code, course_name, course_credits, sessions_per_week)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (course_code, course_name, course_credits, sessions_per_week))
            conn.commit()
            cursor.close()
            conn.close()
            return True, "Course added successfully!"
        except Error as e:
            conn.close()
            return False, f"Error inserting course: {e}"
    return False, "Database connection failed"

def update_course(row_id, course_code, course_name, course_credits, sessions_per_week):
    """Update an existing course record"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            query = """
            UPDATE tbl_courses 
            SET course_code = %s, course_name = %s, course_credits = %s, sessions_per_week = %s
            WHERE row_id = %s
            """
            cursor.execute(query, (course_code, course_name, course_credits, sessions_per_week, row_id))
            conn.commit()
            cursor.close()
            conn.close()
            return True, "Course updated successfully!"
        except Error as e:
            conn.close()
            return False, f"Error updating course: {e}"
    return False, "Database connection failed"

def delete_course(row_id):
    """Delete a course record"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            query = "DELETE FROM tbl_courses WHERE row_id = %s"
            cursor.execute(query, (row_id,))
            conn.commit()
            cursor.close()
            conn.close()
            return True, "Course deleted successfully!"
        except Error as e:
            conn.close()
            return False, f"Error deleting course: {e}"
    return False, "Database connection failed"

def delete_multiple_courses(row_ids):
    """Delete multiple course records"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            query = "DELETE FROM tbl_courses WHERE row_id IN (%s)" % ','.join(['%s'] * len(row_ids))
            cursor.execute(query, row_ids)
            conn.commit()
            cursor.close()
            conn.close()
            return True, f"{len(row_ids)} course(s) deleted successfully!"
        except Error as e:
            conn.close()
            return False, f"Error deleting courses: {e}"
    return False, "Database connection failed"

def import_courses_from_excel(df, mode='append'):
    """
    Import courses from Excel dataframe
    mode: 'append' - add to existing data, 'replace' - clear table first
    """
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # If replace mode, clear existing data
            if mode == 'replace':
                cursor.execute("DELETE FROM tbl_courses")
                conn.commit()
            
            # Prepare data for insertion
            success_count = 0
            error_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # Handle different possible column names
                    course_code = None
                    course_name = None
                    course_credits = None
                    sessions_per_week = None
                    
                    # Try to find course_code column (case-insensitive)
                    for col in df.columns:
                        if col.lower().strip() in ['course_code', 'coursecode', 'code']:
                            course_code = str(row[col]).strip()
                        if col.lower().strip() in ['course_name', 'coursename', 'name']:
                            course_name = str(row[col]).strip()
                        elif col.lower().strip() in ['course_credits', 'credits', 'credit']:
                            course_credits = int(row[col])
                        elif col.lower().strip() in ['sessions_per_week', 'sessions', 'sessionsperweek']:
                            sessions_per_week = int(row[col])
                    
                    # Validate data
                    if not course_code or pd.isna(course_code) or course_code == 'nan':
                        errors.append(f"Row {index + 2}: Missing course code")
                        error_count += 1
                        continue
                    
                    # Validate data
                    if not course_name or pd.isna(course_name) or course_name == 'nan':
                        errors.append(f"Row {index + 2}: Missing course name")
                        error_count += 1
                        continue

                    if course_credits is None or pd.isna(course_credits):
                        errors.append(f"Row {index + 2}: Missing course credits")
                        error_count += 1
                        continue
                    
                    if sessions_per_week is None or pd.isna(sessions_per_week):
                        errors.append(f"Row {index + 2}: Missing sessions per week")
                        error_count += 1
                        continue
                    
                    # Validate ranges
                    if course_credits < 1 or course_credits > 10:
                        errors.append(f"Row {index + 2}: Credits must be between 1 and 10")
                        error_count += 1
                        continue
                    
                    if sessions_per_week < 1 or sessions_per_week > 10:
                        errors.append(f"Row {index + 2}: Sessions must be between 1 and 7")
                        error_count += 1
                        continue
                    
                    # Insert the record
                    query = """
                    INSERT INTO tbl_courses (course_code, course_name, course_credits, sessions_per_week)
                    VALUES (%s, %s, %s, %s)
                    """
                    cursor.execute(query, (course_code, course_name, course_credits, sessions_per_week))
                    success_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {index + 2}: {str(e)}")
                    error_count += 1
                    continue
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True, success_count, error_count, errors
            
        except Error as e:
            conn.close()
            return False, 0, 0, [f"Database error: {e}"]
    return False, 0, 0, ["Database connection failed"]

def validate_excel_file(df):
    """Validate if the Excel file has the required structure"""
    if df.empty:
        return False, "Excel file is empty"
    
    # Check for required columns (case-insensitive)
    columns_lower = [col.lower().strip() for col in df.columns]
    
    has_code = any(col in columns_lower for col in ['course_code', 'coursecode', 'code'])
    has_name = any(col in columns_lower for col in ['course_name', 'coursename', 'name'])
    has_credits = any(col in columns_lower for col in ['course_credits', 'credits', 'credit'])
    has_sessions = any(col in columns_lower for col in ['sessions_per_week', 'sessions', 'sessionsperweek'])
    
    if not has_code:
        return False, "Missing column: course_code (or 'code')"
    if not has_name:
        return False, "Missing column: course_name (or 'name')"
    if not has_credits:
        return False, "Missing column: course_credits (or 'credits')"
    if not has_sessions:
        return False, "Missing column: sessions_per_week (or 'sessions')"
    
    return True, "Valid format"

def create_sample_excel():
    """Create a sample Excel file for download"""
    sample_data = {
        'course_code': ['CS101', 'MATH201'],
        'course_name': ['Introduction to Computers', 'Mathematics 1'],
        'course_credits': [3, 2],
        'sessions_per_week': [3, 2]
    }
    df = pd.DataFrame(sample_data)
    
    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Courses')
    
    return output.getvalue()

# Main application
def main():
    st.title("📚 Course Management System")
    st.markdown("### Excel-like Interface for Managing Courses")
    
    # Initialize database
    if create_database_and_table():
        
        # Sidebar for operations
        st.sidebar.header("Operations")
        operation = st.sidebar.radio(
            "Select Operation:",
            ["View All Courses", "Insert New Course", "Update Course", "Delete Course(s)", "Import from Excel"]
        )
        
        # View All Courses
        if operation == "View All Courses":
            st.subheader("📋 All Courses")
            df = fetch_all_courses()
            
            if not df.empty:
                st.info(f"Total Courses: {len(df)}")
                
                # Display as editable dataframe
                st.dataframe(
                    df,
                    use_container_width=True,
                    height=400,
                    hide_index=True
                )
                
                # Export options
                st.markdown("---")
                col1, col2 = st.columns(2)
                with col1:
                    df1 = df.drop(columns=['row_id'])
                    csv = df1.to_csv(index=False)
                    st.download_button(
                        label="📥 Download as CSV",
                        data=csv,
                        file_name="courses.csv",
                        mime="text/csv"
                    )
                with col2:
                    if st.button("🔄 Refresh Data"):
                        st.session_state.refresh += 1
                        st.rerun()
            else:
                st.warning("No courses found in the database.")
        
        # Insert New Course
        elif operation == "Insert New Course":
            st.subheader("➕ Insert New Course")
            
            with st.form("insert_form", clear_on_submit=True):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    course_code = st.text_input("Course Code*", placeholder="BA101")
                with col2:
                    course_name = st.text_input("Course Name*", placeholder="Business Statistics")
                with col3:
                    course_credits = st.number_input("Course Credits*", min_value=1, max_value=10, value=3)
                with col4:
                    sessions_per_week = st.number_input("Sessions Per Week*", min_value=1, max_value=10, value=3)
                
                submitted = st.form_submit_button("➕ Add Course", use_container_width=True)
                
                if submitted:
                    if course_code.strip():
                        success, message = insert_course(course_code, course_name, course_credits, sessions_per_week)
                        if success:
                            st.success(message)
                            st.balloons()
                        else:
                            st.error(message)
                    else:
                        st.error("Course Code is required!")
            
            # Show current courses
            st.markdown("---")
            st.markdown("#### Current Courses")
            df = fetch_all_courses()
            if not df.empty:
                st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Update Course
        elif operation == "Update Course":
            st.subheader("✏️ Update Course")
            
            df = fetch_all_courses()
            
            if not df.empty:
                # Select course to update
                course_options = {f"ID: {row['row_id']} - {row['course_code']}": row['row_id'] 
                                 for _, row in df.iterrows()}
                
                selected_course = st.selectbox(
                    "Select Course to Update:",
                    options=list(course_options.keys())
                )
                
                if selected_course:
                    row_id = course_options[selected_course]
                    current_course = df[df['row_id'] == row_id].iloc[0]
                    
                    with st.form("update_form"):
                        st.info(f"Updating Course ID: {row_id}")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            course_code = st.text_input(
                                "Course Code*", 
                                value=current_course['course_code']
                            )
                        with col2:
                            course_name = st.text_input(
                                "Course Name*", 
                                value=current_course['course_name']
                            )
                        with col3:
                            course_credits = st.number_input(
                                "Course Credits*", 
                                min_value=1, 
                                max_value=10, 
                                value=int(current_course['course_credits'])
                            )
                        with col4:
                            sessions_per_week = st.number_input(
                                "Sessions Per Week*", 
                                min_value=1, 
                                max_value=10, 
                                value=int(current_course['sessions_per_week'])
                            )
                        
                        submitted = st.form_submit_button("💾 Update Course", use_container_width=True)
                        
                        if submitted:
                            if course_code.strip():
                                success, message = update_course(
                                    row_id, course_code, course_name, course_credits, sessions_per_week
                                )
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
                            else:
                                st.error("Course Code is required!")
            else:
                st.warning("No courses available to update.")
        
        # Delete Course(s)
        elif operation == "Delete Course(s)":
            st.subheader("🗑️ Delete Course(s)")
            
            df = fetch_all_courses()
            
            if not df.empty:
                # Delete mode selection
                delete_mode = st.radio(
                    "Delete Mode:",
                    ["Delete Single Course", "Delete Multiple Courses"],
                    horizontal=True
                )
                
                if delete_mode == "Delete Single Course":
                    course_options = {f"ID: {row['row_id']} - {row['course_code']}": row['row_id'] 
                                     for _, row in df.iterrows()}
                    
                    selected_course = st.selectbox(
                        "Select Course to Delete:",
                        options=list(course_options.keys())
                    )
                    
                    if selected_course:
                        row_id = course_options[selected_course]
                        
                        # Show course details
                        course_details = df[df['row_id'] == row_id].iloc[0]
                        st.warning("⚠️ You are about to delete:")
                        st.json({
                            "ID": int(course_details['row_id']),
                            "Course Code": course_details['course_code'],
                            "Course Name": course_details['course_name'],
                            "Credits": int(course_details['course_credits']),
                            "Sessions/Week": int(course_details['sessions_per_week'])
                        })
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("🗑️ Confirm Delete", type="primary", use_container_width=True):
                                success, message = delete_course(row_id)
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
                        with col2:
                            if st.button("❌ Cancel", use_container_width=True):
                                st.info("Delete operation cancelled.")
                
                else:  # Delete Multiple Courses
                    st.markdown("Select courses to delete:")
                    
                    # Create checkboxes for each course
                    selected_ids = []
                    for _, row in df.iterrows():
                        if st.checkbox(
                            f"ID: {row['row_id']} - {row['course_code']} {row['course_name']} name,{row['course_credits']} credits,{row['sessions_per_week']} sessions/week)",
                            key=f"delete_{row['row_id']}"
                        ):
                            selected_ids.append(row['row_id'])
                    
                    if selected_ids:
                        st.warning(f"⚠️ {len(selected_ids)} course(s) selected for deletion")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(f"🗑️ Delete {len(selected_ids)} Course(s)", type="primary", use_container_width=True):
                                success, message = delete_multiple_courses(selected_ids)
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
                        with col2:
                            if st.button("❌ Cancel", use_container_width=True):
                                st.info("Delete operation cancelled.")
            else:
                st.warning("No courses available to delete.")


        # Import from Excel
        elif operation == "Import from Excel":
            st.subheader("📥 Import Courses from Excel")
            
            # Download sample template
            st.markdown("### Step 1: Download Template")
            st.info("Download the sample Excel template to see the required format")
            
            sample_excel = create_sample_excel()
            st.download_button(
                label="📥 Download Sample Excel Template",
                data=sample_excel,
                file_name="course_template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
            st.markdown("### Excel File Requirements")
            st.markdown("""
            Your Excel file must contain these columns (case-insensitive):
            - **course_code** (or 'code') - Text, required
            - **course_name** (or 'name') - Text, required
            - **course_credits** (or 'credits') - Number 1-10, required
            - **sessions_per_week** (or 'sessions') - Number 1-10, required
            
            💡 **Note**: The row_id column should NOT be in your Excel file - it will be auto-generated.
            """)
            
            st.markdown("---")
            st.markdown("### Step 2: Upload Your Excel File")
            
            # File uploader
            uploaded_file = st.file_uploader(
                "Choose an Excel file (.xlsx or .xls)",
                type=['xlsx', 'xls'],
                help="Upload your Excel file with course data"
            )
            
            if uploaded_file is not None:
                try:
                    # Read the Excel file
                    df = pd.read_excel(uploaded_file)
                    
                    # Validate the file
                    is_valid, message = validate_excel_file(df)
                    
                    if not is_valid:
                        st.error(f"❌ Invalid file format: {message}")
                    else:
                        st.success(f"✅ {message}")
                        
                        # Preview the data
                        st.markdown("### Preview Data")
                        st.info(f"Found {len(df)} course(s) in the Excel file")
                        st.dataframe(df, use_container_width=True)
                        
                        # Import mode selection
                        st.markdown("---")
                        st.markdown("### Step 3: Choose Import Mode")
                        
                        import_mode = st.radio(
                            "How would you like to import?",
                            ["Append to Existing Data", "Replace All Data"],
                            help="Append adds to current data. Replace deletes all existing courses first."
                        )
                        
                        # Warning for replace mode
                        if import_mode == "Replace All Data":
                            st.warning("⚠️ **WARNING**: This will delete ALL existing courses before importing!")
                            
                            # Show current count
                            current_df = fetch_all_courses()
                            if not current_df.empty:
                                st.error(f"🗑️ {len(current_df)} existing course(s) will be deleted!")
                        
                        # Import button
                        st.markdown("---")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("📤 Import Courses", type="primary", use_container_width=True):
                                with st.spinner("Importing courses..."):
                                    mode = 'replace' if import_mode == "Replace All Data" else 'append'
                                    success, success_count, error_count, errors = import_courses_from_excel(df, mode)
                                    
                                    if success:
                                        if success_count > 0:
                                            st.success(f"✅ Successfully imported {success_count} course(s)!")
                                            st.balloons()
                                        
                                        if error_count > 0:
                                            st.warning(f"⚠️ {error_count} row(s) had errors and were skipped")
                                            with st.expander("View Errors"):
                                                for error in errors[:20]:  # Show first 20 errors
                                                    st.error(error)
                                                if len(errors) > 20:
                                                    st.info(f"... and {len(errors) - 20} more errors")
                                        
                                        # Refresh to show new data
                                        st.session_state.refresh += 1
                                        
                                        # Show updated data
                                        st.markdown("---")
                                        st.markdown("### Updated Course List")
                                        updated_df = fetch_all_courses()
                                        st.dataframe(updated_df, use_container_width=True)
                                    else:
                                        st.error("❌ Import failed!")
                                        for error in errors:
                                            st.error(error)
                        
                        with col2:
                            if st.button("❌ Cancel", use_container_width=True):
                                st.info("Import cancelled")
                                uploaded_file = None
                                st.rerun()
                
                except Exception as e:
                    st.error(f"❌ Error reading Excel file: {str(e)}")
                    st.info("Please make sure your file is a valid Excel file (.xlsx or .xls)")
            
            # Show current data
            st.markdown("---")
            st.markdown("### Current Courses in Database")
            df = fetch_all_courses()
            if not df.empty:
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No courses in database yet")
               
        # Footer
        st.sidebar.markdown("---")
        st.sidebar.markdown("### Database Info")
        st.sidebar.info(f"**Database:** {DB_CONFIG['database']}\n**Table:** tbl_courses")
        
        # Show statistics
        df = fetch_all_courses()
        if not df.empty:
            st.sidebar.markdown("### Statistics")
            st.sidebar.metric("Total Courses", len(df))
            st.sidebar.metric("Avg Credits", f"{df['course_credits'].mean():.1f}")
            st.sidebar.metric("Avg Sessions/Week", f"{df['sessions_per_week'].mean():.1f}")

if __name__ == "__main__":
    main()
