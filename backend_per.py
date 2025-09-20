# backend_per.py
import psycopg2

class Database:
    """
    A class to handle all database operations for the Performance Management System.
    Uses psycopg2 to connect to a PostgreSQL database.
    """
    def __init__(self, dbname, user, password, host):
        self.conn = None
        self.cursor = None
        self.db_params = {
            "dbname": dbname,
            "user": user,
            "password": password,
            "host": host
        }
        self.connect()

    def connect(self):
        """Establishes a connection to the PostgreSQL database."""
        try:
            self.conn = psycopg2.connect(**self.db_params)
            self.cursor = self.conn.cursor()
            print("Database connection successful.")
        except psycopg2.OperationalError as e:
            st.error(f"Error connecting to the database: {e}")
            st.stop() # Stop the Streamlit app if connection fails

    def close(self):
        """Closes the database connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("Database connection closed.")

    # --- C.R.U.D. PRINCIPLES ---

    ## Create operations ##
    def create_user(self, username, password, role, manager_id=None):
        """Inserts a new user into the database."""
        try:
            self.cursor.execute(
                "INSERT INTO users (username, password, role, manager_id) VALUES (%s, %s, %s, %s) RETURNING user_id;",
                (username, password, role, manager_id)
            )
            user_id = self.cursor.fetchone()[0]
            self.conn.commit()
            return user_id
        except psycopg2.Error as e:
            self.conn.rollback()
            st.error(f"Error creating user: {e}")
            return None

    def create_goal(self, goal_description, due_date, employee_id):
        """Inserts a new goal for an employee."""
        try:
            self.cursor.execute(
                "INSERT INTO goals (goal_description, due_date, status, employee_id) VALUES (%s, %s, %s, %s) RETURNING goal_id;",
                (goal_description, due_date, 'Draft', employee_id)
            )
            goal_id = self.cursor.fetchone()[0]
            self.conn.commit()
            return goal_id
        except psycopg2.Error as e:
            self.conn.rollback()
            st.error(f"Error creating goal: {e}")
            return None

    def create_task(self, task_description, goal_id):
        """Inserts a new task for a goal."""
        try:
            self.cursor.execute(
                "INSERT INTO tasks (task_description, goal_id) VALUES (%s, %s) RETURNING task_id;",
                (task_description, goal_id)
            )
            task_id = self.cursor.fetchone()[0]
            self.conn.commit()
            return task_id
        except psycopg2.Error as e:
            self.conn.rollback()
            st.error(f"Error creating task: {e}")
            return None

    def create_feedback(self, feedback_text, manager_id, employee_id, goal_id):
        """Inserts new feedback from a manager."""
        try:
            self.cursor.execute(
                "INSERT INTO feedback (feedback_text, manager_id, employee_id, goal_id) VALUES (%s, %s, %s, %s) RETURNING feedback_id;",
                (feedback_text, manager_id, employee_id, goal_id)
            )
            feedback_id = self.cursor.fetchone()[0]
            self.conn.commit()
            return feedback_id
        except psycopg2.Error as e:
            self.conn.rollback()
            st.error(f"Error creating feedback: {e}")
            return None

    ## Read operations ##
    def get_user_by_username(self, username):
        """Retrieves user information by username."""
        self.cursor.execute("SELECT * FROM users WHERE username = %s;", (username,))
        return self.cursor.fetchone()
    
    def get_user_by_id(self, user_id):
        """Retrieves user information by user_id."""
        self.cursor.execute("SELECT * FROM users WHERE user_id = %s;", (user_id,))
        return self.cursor.fetchone()

    def get_goals_by_employee(self, employee_id):
        """Retrieves all goals for a specific employee."""
        self.cursor.execute("SELECT * FROM goals WHERE employee_id = %s ORDER BY due_date DESC;", (employee_id,))
        return self.cursor.fetchall()
    
    def get_tasks_by_goal(self, goal_id):
        """Retrieves all tasks for a specific goal."""
        self.cursor.execute("SELECT * FROM tasks WHERE goal_id = %s;", (goal_id,))
        return self.cursor.fetchall()

    def get_feedback_by_employee(self, employee_id):
        """Retrieves all feedback for a specific employee."""
        self.cursor.execute("SELECT * FROM feedback WHERE employee_id = %s;", (employee_id,))
        return self.cursor.fetchall()
        
    def get_employee_goals_and_feedback(self, employee_id):
        """
        Retrieves all goals and associated feedback for a specific employee.
        """
        self.cursor.execute("""
            SELECT g.goal_id, g.goal_description, g.due_date, g.status, f.feedback_text, f.feedback_date
            FROM goals g
            LEFT JOIN feedback f ON g.goal_id = f.goal_id
            WHERE g.employee_id = %s
            ORDER BY g.due_date DESC;
        """, (employee_id,))
        return self.cursor.fetchall()
    
    def get_all_employees_of_manager(self, manager_id):
        """Retrieves all employees reporting to a specific manager."""
        self.cursor.execute("SELECT user_id, username FROM users WHERE manager_id = %s;", (manager_id,))
        return self.cursor.fetchall()

    ## Update operations ##
    def update_goal_status(self, goal_id, new_status):
        """Updates the status of a specific goal."""
        try:
            self.cursor.execute(
                "UPDATE goals SET status = %s WHERE goal_id = %s;",
                (new_status, goal_id)
            )
            self.conn.commit()
            return True
        except psycopg2.Error as e:
            self.conn.rollback()
            st.error(f"Error updating goal status: {e}")
            return False

    def approve_task(self, task_id):
        """Approves a task logged by an employee."""
        try:
            self.cursor.execute(
                "UPDATE tasks SET is_approved = TRUE WHERE task_id = %s;",
                (task_id,)