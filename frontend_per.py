# frontend_per.py
import streamlit as st
import backend_per as db
from datetime import date

# Initialize database connection
# Replace with your actual PostgreSQL connection details
try:
    db_conn = db.Database(
        dbname="Performance management system",
        user="postgres",
        password="Sakshi@299",
        host="localhost"
    )
except psycopg2.OperationalError:
    st.error("Could not connect to the database. Please check your backend configuration.")
    st.stop()


# --- Main application logic ---
st.title("Performance Management System")

# Using session_state for user session management
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.role = None
    st.session_state.manager_id = None
    st.session_state.username = None

# Login/Logout section
if not st.session_state.logged_in:
    st.sidebar.header("Login")
    login_username = st.sidebar.text_input("Username", key="login_username")
    login_password = st.sidebar.text_input("Password", type="password", key="login_password")

    if st.sidebar.button("Login"):
        user = db_conn.get_user_by_username(login_username)
        if user and user[2] == login_password:  # Simple password check for this example
            st.session_state.logged_in = True
            st.session_state.user_id = user[0]
            st.session_state.username = user[1]
            st.session_state.role = user[3]
            st.session_state.manager_id = user[4]
            st.success(f"Welcome, {st.session_state.username}!")
            st.experimental_rerun()
        else:
            st.error("Invalid username or password.")
else:
    st.sidebar.header("User Menu")
    st.sidebar.write(f"Logged in as: **{st.session_state.username}** ({st.session_state.role})")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.experimental_rerun()

    # --- Manager View ---
    if st.session_state.role == 'Manager':
        st.header("Manager Dashboard")
        
        # Business Insights Section
        insights = db_conn.get_business_insights()
        with st.expander("Business Insights 📈"):
            st.write("Here are some high-level metrics for your team's performance:")
            st.metric(label="Total Goals Set", value=insights.get('total_goals', 0))
            st.metric(label="Goals Completed", value=insights.get('completed_goals', 0))
            st.metric(label="Total Tasks Approved", value=insights.get('approved_tasks', 0))
            st.write(f"Average days to complete a goal: **{insights.get('avg_completion_days', 'N/A')}**")
            st.write(f"Minimum days to complete a goal: **{insights.get('min_completion_days', 'N/A')}**")
            st.write(f"Maximum days to complete a goal: **{insights.get('max_completion_days', 'N/A')}**")
        
        st.write("---")
        st.subheader("Set Goals for Employees")
        employees = db_conn.get_all_employees_of_manager(st.session_state.user_id)
        if employees:
            employee_options = {emp[1]: emp[0] for emp in employees}
            selected_employee_name = st.selectbox("Select Employee", list(employee_options.keys()), key="set_goal_employee_select")
            selected_employee_id = employee_options[selected_employee_name]

            with st.form("set_goal_form"):
                goal_description = st.text_area("Goal Description")
                due_date = st.date_input("Due Date", date.today())
                submitted = st.form_submit_button("Set Goal")
                if submitted:
                    db_conn.create_goal(goal_description, due_date, selected_employee_id)
                    st.success(f"Goal set successfully for {selected_employee_name}!")
                    st.experimental_rerun()
        else:
            st.info("You don't have any employees to set goals for.")

        st.write("---")
        st.subheader("Employee Performance History & Feedback")
        if employees:
            review_employee_options = {emp[1]: emp[0] for emp in employees}
            selected_review_employee_name = st.selectbox("Select an employee to review:", list(review_employee_options.keys()), key="review_select")
            review_emp_id = review_employee_options[selected_review_employee_name]
            
            st.markdown("### Goals and Feedback")
            goals_and_feedback = db_conn.get_employee_goals_and_feedback(review_emp_id)
            if goals_and_feedback:
                for goal in goals_and_feedback:
                    st.write(f"**Goal ID**: {goal[0]} - **{goal[1]}**")
                    st.write(f"**Due Date**: {goal[2]}")
                    st.write(f"**Status**: {goal[3]}")
                    
                    # Update status section
                    new_status = st.selectbox("Update Status:", ['Draft', 'In Progress', 'Completed', 'Cancelled'], index=['Draft', 'In Progress', 'Completed', 'Cancelled'].index(goal[3]), key=f"status_select_{goal[0]}_{review_emp_id}")
                    if st.button("Save Status", key=f"save_status_{goal[0]}_{review_emp_id}"):
                        db_conn.update_goal_status(goal[0], new_status)
                        st.success("Goal status updated!")
                        st.experimental_rerun()
                    
                    # Show tasks for this goal
                    st.markdown("##### Tasks")
                    tasks_for_goal = db_conn.get_tasks_by_goal(goal[0])
                    if tasks_for_goal:
                        for task in tasks_for_goal:
                            status_text = "Approved" if task[2] else "Pending Approval"
                            st.write(f"- {task[1]} ({status_text})")
                            if not task[2]:
                                if st.button("Approve Task", key=f"approve_task_{task[0]}"):
                                    db_conn.approve_task(task[0])
                                    st.success("Task approved!")
                                    st.experimental_rerun()
                    
                    # Add feedback section
                    st.markdown("##### Feedback")
                    if goal[4]:
                        st.write(f"**Feedback**: {goal[4]}")
                        st.write(f"**Date**: {goal[5]}")
                    else:
                        st.info("No feedback yet.")
                    
                    with st.form(f"add_feedback_{goal[0]}_{review_emp_id}"):
                        feedback_text = st.text_area(f"Add new feedback for Goal {goal[0]}", key=f"feedback_text_{goal[0]}_{review_emp_id}")
                        feedback_submit = st.form_submit_button("Submit Feedback")
                        if feedback_submit:
                            if feedback_text:
                                db_conn.create_feedback(feedback_text, st.session_state.user_id, review_emp_id, goal[0])
                                st.success("Feedback submitted!")
                                st.experimental_rerun()

                    st.write("---")

            else:
                st.info("No goals or feedback found for this employee.")
        else:
            st.info("No employees to review.")
    
    # --- Employee View ---
    elif st.session_state.role == 'Employee':
        st.header("Employee Dashboard")
        
        st.subheader("My Goals & Tasks")
        my_goals = db_conn.get_goals_by_employee(st.session_state.user_id)
        if my_goals:
            for goal in my_goals:
                st.write(f"**Goal**: {goal[1]}")
                st.write(f"**Due Date**: {goal[2]}")
                st.write(f"**Status**: {goal[3]}")
                st.write(f"Manager: {db_conn.get_user_by_id(st.session_state.manager_id)[1]}")

                # Log tasks for a goal
                with st.expander(f"Log tasks for Goal ID: {goal[0]}"):
                    task_description = st.text_input("Task Description", key=f"task_desc_{goal[0]}")
                    if st.button("Log Task", key=f"log_task_{goal[0]}"):
                        if task_description:
                            db_conn.create_task(task_description, goal[0])
                            st.success("Task logged, awaiting manager approval.")
                            st.experimental_rerun()
                        else:
                            st.warning("Task description cannot be empty.")
                
                # Show tasks for this goal
                st.write("Tasks Logged:")
                goal_tasks = db_conn.get_tasks_by_goal(goal[0])
                if goal_tasks:
                    for task in goal_tasks:
                        status_text = "Approved" if task[2] else "Pending Approval"
                        st.write(f"- {task[1]} ({status_text})")
                st.write("---")
        else:
            st.info("No goals have been assigned to you yet.")
        
        st.subheader("My Feedback History")
        my_feedback = db_conn.get_feedback_by_employee(st.session_state.user_id)
        if my_feedback:
            for feedback_item in my_feedback:
                st.write(f"**Goal ID**: {feedback_item[5]}")
                st.write(f"**Feedback**: {feedback_item[1]}")
                st.write(f"**Date**: {feedback_item[2]}")
                st.write(f"**Manager**: {db_conn.get_user_by_id(feedback_item[3])[1]}")
                st.write("---")
        else:
            st.info("No feedback available yet.")