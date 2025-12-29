import streamlit as st
from utils.auth import AuthManager
from database.db_manager import DatabaseManager
from datetime import datetime, timedelta


def show_planner_page(db: DatabaseManager, auth: AuthManager, navigate_to):
    """
    Display the study planner page
    
    Args:
        db: DatabaseManager instance
        auth: AuthManager instance
        navigate_to: Navigation function
    """
    
    # Page header
    st.markdown("""
        <div style='padding: 1rem 0;'>
            <h1 style='color: #667eea;'> Study Planner</h1>
            <p style='color: #764ba2; font-size: 1.1rem;'>Organize your study tasks and deadlines</p>
        </div>
    """, unsafe_allow_html=True)
    
    user_id = auth.get_current_user_id()
    
    # Get subjects for linking tasks
    subjects = db.get_user_subjects(user_id)
    
    # Action buttons
    col1, col2, col3 = st.columns([2, 2, 6])
    
    with col1:
        if st.button("➕ Add Task", type="primary", use_container_width=True):
            st.session_state.show_add_task = True
    
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    st.markdown("---")
    
    # Add task form
    if st.session_state.get('show_add_task', False):
        st.markdown("### ➕ Add New Task")
        
        with st.form("add_task_form", clear_on_submit=True):
            task_title = st.text_input(
                "Task Title *",
                placeholder="e.g., Study Chapter 5, Complete Assignment",
                max_chars=200
            )
            
            task_description = st.text_area(
                "Description (optional)",
                placeholder="Add details about this task...",
                max_chars=500,
                height=100
            )
            
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                # Subject selector (optional)
                subject_options = ["None"] + [s['name'] for s in subjects]
                selected_subject = st.selectbox(
                    "Link to Subject (optional)",
                    options=subject_options
                )
            
            with col_b:
                due_date = st.date_input(
                    "Due Date",
                    value=datetime.now().date() + timedelta(days=7),
                    min_value=datetime.now().date()
                )
            
            with col_c:
                priority = st.selectbox(
                    "Priority",
                    options=["low", "medium", "high"],
                    index=1
                )
            
            col_submit, col_cancel = st.columns(2)
            
            with col_submit:
                submit = st.form_submit_button("Add Task", type="primary", use_container_width=True)
            
            with col_cancel:
                cancel = st.form_submit_button("Cancel", use_container_width=True)
            
            if submit:
                if not task_title:
                    st.error("⚠️ Please enter a task title")
                else:
                    # Get subject_id if selected
                    subject_id = None
                    if selected_subject != "None":
                        subject_id = next((s['id'] for s in subjects if s['name'] == selected_subject), None)
                    
                    try:
                        task_id = db.create_task(
                            user_id=user_id,
                            title=task_title,
                            description=task_description,
                            due_date=due_date.strftime('%Y-%m-%d'),
                            priority=priority,
                            subject_id=subject_id
                        )
                        
                        if task_id:
                            st.success(f"✅ Task '{task_title}' created successfully!")
                            st.session_state.show_add_task = False
                            import time
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Failed to create task")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
            
            if cancel:
                st.session_state.show_add_task = False
                st.rerun()
        
        st.markdown("---")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📋 All Tasks", "⏰ Upcoming", "✅ Completed", "📊 Statistics"])
    
    # ==================== TAB 1: All Tasks ====================
    with tab1:
        st.markdown("###  All Tasks")
        
        # Filter options
        col_filter1, col_filter2 = st.columns(2)
        
        with col_filter1:
            status_filter = st.selectbox(
                "Filter by Status",
                options=["all", "pending", "in_progress", "completed"],
                format_func=lambda x: x.replace("_", " ").title(),
                key="all_status_filter"
            )
        
        with col_filter2:
            priority_filter = st.selectbox(
                "Filter by Priority",
                options=["all", "low", "medium", "high"],
                format_func=lambda x: x.title(),
                key="all_priority_filter"
            )
        
        # Get tasks
        if status_filter == "all":
            tasks = db.get_user_tasks(user_id)
        else:
            tasks = db.get_user_tasks(user_id, status=status_filter)
        
        # Apply priority filter
        if priority_filter != "all":
            tasks = [t for t in tasks if t['priority'] == priority_filter]
        
        if tasks:
            # Sort by due date
            tasks.sort(key=lambda x: x['due_date'] if x['due_date'] else '9999-12-31')
            
            for task in tasks:
                # Priority colors
                priority_colors = {
                    'low': '#4caf50',
                    'medium': '#ff9800',
                    'high': '#f44336'
                }
                priority_color = priority_colors.get(task['priority'], '#9e9e9e')
                
                # Status colors
                status_colors = {
                    'pending': '#2196f3',
                    'in_progress': '#ff9800',
                    'completed': '#4caf50'
                }
                status_color = status_colors.get(task['status'], '#9e9e9e')
                
                # Calculate days until due
                if task['due_date']:
                    due_date = datetime.strptime(task['due_date'], '%Y-%m-%d').date()
                    today = datetime.now().date()
                    days_until = (due_date - today).days
                    
                    if days_until < 0:
                        due_text = f"⚠️ Overdue by {abs(days_until)} days"
                        due_color = "#f44336"
                    elif days_until == 0:
                        due_text = "📌 Due Today!"
                        due_color = "#f44336"
                    elif days_until == 1:
                        due_text = "⚠️ Due Tomorrow"
                        due_color = "#ff9800"
                    else:
                        due_text = f"📆 Due in {days_until} days"
                        due_color = "#666"
                else:
                    due_text = "No due date"
                    due_color = "#999"
                
                # Get subject name if linked
                subject_name = ""
                if task['subject_id']:
                    subject = next((s for s in subjects if s['id'] == task['subject_id']), None)
                    if subject:
                        subject_name = f"📚 {subject['name']}"
                
                # Task card
                st.markdown(f"""
                    <div style='background-color: #f8f9fa; padding: 1.5rem; border-radius: 10px; 
                                border-left: 5px solid {priority_color}; margin-bottom: 1rem;'>
                        <div style='display: flex; justify-content: space-between; align-items: start;'>
                            <div style='flex: 1;'>
                                <h3 style='margin: 0 0 0.5rem 0; color: #333;'>{task['title']}</h3>
                                <p style='color: #666; font-size: 0.9rem; margin: 0.3rem 0;'>
                                    {task['description'] if task['description'] else '<em>No description</em>'}
                                </p>
                                <p style='color: {due_color}; font-size: 0.9rem; margin: 0.5rem 0 0 0; font-weight: 500;'>
                                    {due_text}
                                </p>
                                {f'<p style="color: #888; font-size: 0.85rem; margin: 0.3rem 0 0 0;">{subject_name}</p>' if subject_name else ''}
                            </div>
                            <div style='display: flex; gap: 0.5rem; align-items: center;'>
                                <span style='background-color: {priority_color}; color: white; padding: 0.3rem 0.8rem; 
                                            border-radius: 15px; font-size: 0.8rem; font-weight: bold;'>
                                    {task['priority'].upper()}
                                </span>
                                <span style='background-color: {status_color}; color: white; padding: 0.3rem 0.8rem; 
                                            border-radius: 15px; font-size: 0.8rem;'>
                                    {task['status'].replace('_', ' ').title()}
                                </span>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                # Action buttons
                # pages/dashboard/planner.py - Complete fix with edit and delete in loop

# Replace the entire action buttons section in the task loop with this:

            # Action buttons
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if task['status'] != 'completed':
                        if st.button("✅ Complete", key=f"complete_{task['id']}", use_container_width=True):
                            db.update_task_status(task['id'], 'completed')
                            st.success("Task completed!")
                            st.rerun()
                
                with col2:
                    if task['status'] == 'pending':
                        if st.button("▶️ Start", key=f"start_{task['id']}", use_container_width=True):
                            db.update_task_status(task['id'], 'in_progress')
                            st.rerun()
                
                with col3:
                    if st.button("✏️ Edit", key=f"edit_{task['id']}", use_container_width=True):
                        st.session_state.editing_task_id = task['id']
                        st.rerun()
                
                with col4:
                    if st.button("🗑️ Delete", key=f"delete_{task['id']}", use_container_width=True):
                        st.session_state.deleting_task_id = task['id']
                        st.rerun()
                
                # EDIT confirmation - INSIDE THE LOOP (matching quiz pattern)
                if st.session_state.get('editing_task_id') == task['id']:
                    st.markdown("---")
                    st.markdown(f"### ✏️ Edit Task: {task['title']}")
                    
                    with st.form(f"edit_task_form_{task['id']}"):  # Unique form key per task
                        edit_title = st.text_input("Title *", value=task['title'])
                        edit_description = st.text_area(
                            "Description", 
                            value=task['description'] if task['description'] else ""
                        )
                        
                        col_a, col_b, col_c = st.columns(3)
                        
                        with col_a:
                            edit_due_date = st.date_input(
                                "Due Date",
                                value=datetime.strptime(task['due_date'], '%Y-%m-%d').date() if task['due_date'] else datetime.now().date()
                            )
                        
                        with col_b:
                            edit_priority = st.selectbox(
                                "Priority",
                                options=["low", "medium", "high"],
                                index=["low", "medium", "high"].index(task['priority'])
                            )
                        
                        with col_c:
                            edit_status = st.selectbox(
                                "Status",
                                options=["pending", "in_progress", "completed"],
                                index=["pending", "in_progress", "completed"].index(task['status'])
                            )
                        
                        col_save, col_cancel = st.columns(2)
                        
                        with col_save:
                            if st.form_submit_button("Save Changes", type="primary", use_container_width=True):
                                if not edit_title:
                                    st.error("⚠️ Please enter a task title")
                                else:
                                    try:
                                        db.update_task(
                                            task_id=task['id'],
                                            title=edit_title,
                                            description=edit_description if edit_description else None,
                                            due_date=edit_due_date.strftime('%Y-%m-%d'),
                                            priority=edit_priority,
                                            status=edit_status
                                        )
                                        
                                        st.success(f"✅ Task '{edit_title}' updated successfully!")
                                        st.session_state.editing_task_id = None
                                        import time
                                        time.sleep(1)
                                        st.rerun()
                                        
                                    except Exception as e:
                                        st.error(f"❌ Error updating task: {str(e)}")
                        
                        with col_cancel:
                            if st.form_submit_button("Cancel", use_container_width=True):
                                st.session_state.editing_task_id = None
                                st.rerun()
                
                # DELETE confirmation - INSIDE THE LOOP (matching quiz pattern)
                if st.session_state.get('deleting_task_id') == task['id']:
                    st.markdown("---")
                    st.error("⚠️ **Delete this task?** This action cannot be undone!")
                    col_yes, col_no = st.columns(2)
                    
                    with col_yes:
                        if st.button(
                            "Yes, Delete",
                            key=f"confirm_delete_task_{task['id']}",
                            type="primary",
                            use_container_width=True
                        ):
                            try:
                                db.delete_task(task['id'])
                                st.success("✅ Task deleted successfully!")
                            except Exception as e:
                                st.error(f"❌ Error deleting task: {str(e)}")
                            finally:
                                st.session_state.deleting_task_id = None
                                st.rerun()
                    
                    with col_no:
                        if st.button(
                            "Cancel",
                            key=f"cancel_delete_task_{task['id']}",
                            use_container_width=True
                        ):
                            st.session_state.deleting_task_id = None
                            st.rerun()
                
                st.markdown("---")
            
        else:
            st.info("📝 No tasks found. Create your first task to get started!")
                
    # ==================== TAB 2: Upcoming ====================
    with tab2:
        st.markdown("### ⏰ Upcoming Tasks (Next 7 Days)")
        
        all_tasks = db.get_user_tasks(user_id)
        today = datetime.now().date()
        week_later = today + timedelta(days=7)
        
        upcoming_tasks = []
        for task in all_tasks:
            if task['status'] != 'completed' and task['due_date']:
                due_date = datetime.strptime(task['due_date'], '%Y-%m-%d').date()
                if today <= due_date <= week_later:
                    upcoming_tasks.append(task)
        
        if upcoming_tasks:
            # Sort by due date
            upcoming_tasks.sort(key=lambda x: x['due_date'])
            
            for task in upcoming_tasks:
                due_date = datetime.strptime(task['due_date'], '%Y-%m-%d').date()
                days_until = (due_date - today).days
                
                if days_until == 0:
                    urgency = "🔴 DUE TODAY!"
                    color = "#f44336"
                elif days_until == 1:
                    urgency = "🟠 Due Tomorrow"
                    color = "#ff9800"
                else:
                    urgency = f"🟢 Due in {days_until} days"
                    color = "#4caf50"
                
                st.markdown(f"""
                    <div style='background-color: #f5f5f5; padding: 1rem; border-radius: 8px; 
                                margin-bottom: 0.5rem; border-left: 4px solid {color};'>
                        <p style='margin: 0; font-weight: bold; font-size: 1.1rem;'>{task['title']}</p>
                        <p style='margin: 0.5rem 0 0 0; color: {color}; font-weight: 500;'>{urgency}</p>
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown("")
        else:
            st.info("🎉 No upcoming tasks in the next 7 days!")
    
    # ==================== TAB 3: Completed ====================
    with tab3:
        st.markdown("### ✅ Completed Tasks")
        
        completed_tasks = db.get_user_tasks(user_id, status='completed')
        
        if completed_tasks:
            # Sort by completion date (most recent first)
            completed_tasks.sort(key=lambda x: x['completed_at'] if x['completed_at'] else '', reverse=True)
            
            for task in completed_tasks:
                completed_date = task['completed_at'][:10] if task['completed_at'] else 'Unknown'
                
                with st.expander(f"✅ {task['title']}", expanded=False):
                    st.write(f"**Completed:** {completed_date}")
                    if task['description']:
                        st.write(f"**Description:** {task['description']}")
                    if task['due_date']:
                        st.write(f"**Was due:** {task['due_date']}")
                    
                    if st.button("🗑️ Delete", key=f"delete_completed_{task['id']}", use_container_width=True):
                        db.delete_task(task['id'])
                        st.rerun()
        else:
            st.info("No completed tasks yet. Keep studying! 📚")
    
    # ==================== TAB 4: Statistics ====================
    with tab4:
        st.markdown("### 📊 Task Statistics")
        
        all_tasks = db.get_user_tasks(user_id)
        
        if all_tasks:
            total_tasks = len(all_tasks)
            pending_tasks = len([t for t in all_tasks if t['status'] == 'pending'])
            in_progress_tasks = len([t for t in all_tasks if t['status'] == 'in_progress'])
            completed_tasks = len([t for t in all_tasks if t['status'] == 'completed'])
            
            # Overdue tasks
            today = datetime.now().date()
            overdue_tasks = 0
            for task in all_tasks:
                if task['status'] != 'completed' and task['due_date']:
                    due_date = datetime.strptime(task['due_date'], '%Y-%m-%d').date()
                    if due_date < today:
                        overdue_tasks += 1
            
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Tasks", total_tasks)
            
            with col2:
                st.metric("Pending", pending_tasks)
            
            with col3:
                st.metric("Completed", completed_tasks)
            
            with col4:
                st.metric("Overdue", overdue_tasks, delta=None if overdue_tasks == 0 else f"-{overdue_tasks}")
            
            st.markdown("---")
            
            # Completion rate
            if total_tasks > 0:
                completion_rate = (completed_tasks / total_tasks) * 100
                st.markdown(f"### 📈 Completion Rate: {completion_rate:.1f}%")
                st.progress(completion_rate / 100)
            
            st.markdown("---")
            
            # Priority breakdown
            high_priority = len([t for t in all_tasks if t['priority'] == 'high' and t['status'] != 'completed'])
            medium_priority = len([t for t in all_tasks if t['priority'] == 'medium' and t['status'] != 'completed'])
            low_priority = len([t for t in all_tasks if t['priority'] == 'low' and t['status'] != 'completed'])
            
            st.markdown("### 🎯 Active Tasks by Priority")
            
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                st.metric("🔴 High", high_priority)
            with col_b:
                st.metric("🟠 Medium", medium_priority)
            with col_c:
                st.metric("🟢 Low", low_priority)
        else:
            st.info("📊 No statistics yet. Create some tasks to see your progress!")
    
    # Back to dashboard
    st.markdown("---")
    if st.button("← Back to Dashboard", use_container_width=True):
        navigate_to('dashboard')
        