import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import os
import calplot # Added for heatmap
import matplotlib.pyplot as plt # Added for heatmap

# --- Streak Calculation Function ---
def calculate_streak(csv_path="data/mood_data.csv"):
    try:
        # Ensure data directory and file path are correct
        data_dir = os.path.dirname(csv_path)
        if not data_dir: # Handle case where csv_path might be just a filename
            data_dir = "." # Assume current directory
            
        actual_csv_path = os.path.join(data_dir, os.path.basename(csv_path))

        if not os.path.exists(actual_csv_path) or os.path.getsize(actual_csv_path) == 0:
            return 0
        
        df = pd.read_csv(actual_csv_path)
        if df.empty:
            return 0
            
    except FileNotFoundError:
        return 0
    except pd.errors.EmptyDataError:
        return 0 
    except Exception as e:
        st.error(f"Error reading mood data for streak: {e}")
        return 0

    timestamp_col_name = None
    if 'timestamp' in df.columns: # Standard name used by this app
        timestamp_col_name = 'timestamp'
    elif 'Date and Time' in df.columns: # Check for user's existing format
        timestamp_col_name = 'Date and Time'
    elif len(df.columns) > 0: # Fallback: try the first column if it looks like a date
        try:
            pd.to_datetime(df.iloc[:, 0], errors='raise')
            timestamp_col_name = df.columns[0]
        except (ValueError, TypeError, AttributeError):
            st.warning("Streak: Could not identify a suitable timestamp column.")
            return 0
    else:
        st.warning("Streak: CSV file has no columns.")
        return 0
    
    if not timestamp_col_name:
        st.warning("Streak: Timestamp column could not be determined.")
        return 0

    try:
        df['parsed_timestamp'] = pd.to_datetime(df[timestamp_col_name], errors='coerce')
    except Exception as e:
        st.warning(f"Streak: Error parsing timestamp column '{timestamp_col_name}': {e}")
        return 0
        
    df.dropna(subset=['parsed_timestamp'], inplace=True)
    if df.empty:
        return 0

    df['date'] = df['parsed_timestamp'].dt.date
    unique_dates = sorted(df['date'].unique(), reverse=True)

    if not unique_dates:
        return 0

    today = date.today()
    current_streak = 0
    
    if unique_dates[0] == today or unique_dates[0] == (today - timedelta(days=1)):
        current_streak = 1
        last_streak_date = unique_dates[0]
        
        for i in range(1, len(unique_dates)):
            if (last_streak_date - unique_dates[i]) == timedelta(days=1):
                current_streak += 1
                last_streak_date = unique_dates[i]
            else:
                break 
    
    return current_streak
# --- End Streak Calculation Function ---

# --- Activity Heatmap Function ---
def create_activity_heatmap(csv_path="data/mood_data.csv"):
    try:
        data_dir = os.path.dirname(csv_path)
        if not data_dir:
            data_dir = "."
        actual_csv_path = os.path.join(data_dir, os.path.basename(csv_path))

        if not os.path.exists(actual_csv_path) or os.path.getsize(actual_csv_path) == 0:
            # st.info("No data for heatmap yet.") # Optional: can be handled by calplot
            return None 
        
        df = pd.read_csv(actual_csv_path)
        if df.empty:
            # st.info("Mood log is empty, no heatmap to display.") # Optional
            return None

    except Exception as e:
        st.error(f"Error reading data for heatmap: {e}")
        return None

    timestamp_col_name = None
    if 'timestamp' in df.columns:
        timestamp_col_name = 'timestamp'
    elif 'Date and Time' in df.columns:
        timestamp_col_name = 'Date and Time'
    elif len(df.columns) > 0:
        try:
            pd.to_datetime(df.iloc[:, 0], errors='raise')
            timestamp_col_name = df.columns[0]
        except (ValueError, TypeError, AttributeError):
            st.warning("Heatmap: Could not identify a suitable timestamp column.")
            return None
    else:
        st.warning("Heatmap: CSV file has no columns.")
        return None
    
    if not timestamp_col_name:
        st.warning("Heatmap: Timestamp column could not be determined.")
        return None

    try:
        df['parsed_timestamp'] = pd.to_datetime(df[timestamp_col_name], errors='coerce')
    except Exception as e:
        st.warning(f"Heatmap: Error parsing timestamp column '{timestamp_col_name}': {e}")
        return None
        
    df.dropna(subset=['parsed_timestamp'], inplace=True)
    if df.empty:
        return None

    # Count entries per day
    daily_counts = df['parsed_timestamp'].dt.date.value_counts().sort_index()
    
    # Convert dates to datetime objects for calplot
    events = pd.Series(daily_counts.values, index=pd.to_datetime(daily_counts.index))

    if events.empty:
        return None

    # Create the plot - styled to be more like GitHub's contribution graph
    fig, ax = calplot.calplot(
        events,
        cmap='Greens',
        figsize=(12, 2.5),  # Adjust as needed, this is a common wide aspect ratio
        suptitle="Mood Log Activity",
        yearlabel_kws={'fontsize': 10, 'color': 'darkgray'}, # Less prominent year
        # monthlabels=[datetime(2000, i, 1).strftime('%b') for i in range(1,13)], # Default is usually fine
        daylabels=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], # Standard day names
        dayticks=[0, 2, 4],  # Display only Mon, Wed, Fri (0=Mon, 2=Wed, 4=Fri)
        linewidth=0.5,       # Thinner lines for the grid cells
        linecolor='lightgray', # Lighter color for grid lines
        fillcolor='#ebedf0',  # GitHub-like light gray for empty days
        tight_layout=True    # Adjust layout to prevent overlap
    )
    return fig
# --- End Activity Heatmap Function ---

st.title("Log Your Mood")

# --- Display Streak ---
# Ensure the path passed to calculate_streak is consistent
csv_file_path_for_streak = "data/mood_data.csv"
current_streak_value = calculate_streak(csv_path=csv_file_path_for_streak)
st.metric(label="Current Mood Log Streak 🔥", value=f"{current_streak_value} Day{'s' if current_streak_value != 1 else ''}")
# --- End Display Streak ---

# --- Display Activity Heatmap ---
st.subheader("Your Mood Log Activity")
heatmap_fig = create_activity_heatmap(csv_path=csv_file_path_for_streak) # Use the same path
if heatmap_fig:
    st.pyplot(heatmap_fig)
else:
    st.info("Log some moods to see your activity heatmap!")
# --- End Display Activity Heatmap ---

mood_options = ["Happy", "Angry", "Sad", "Anxious", "Neutral"]
mood = st.selectbox("How are you feeling today", mood_options, index=mood_options.index("Neutral"))
reason = st.text_input("Why do you feel like that?", placeholder="Enter Your Thoughts here ...")

if st.button("Submit"):
    if mood and reason: 
        new_entry = {
            "timestamp": datetime.now(),
            "mood": mood,
            "reason": reason
        }
        df_entry = pd.DataFrame([new_entry])
        
        # Define file path and ensure directory exists
        data_dir = "data"
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        file_path = os.path.join(data_dir, "mood_data.csv")
        
        header_needed = not os.path.exists(file_path) or os.path.getsize(file_path) == 0
        
        df_entry.to_csv(file_path, mode='a', header=header_needed, index=False)
        st.success("Mood logged successfully!")
        st.balloons()
        st.rerun() 
    else:
        st.warning("Please select a mood and provide a reason.")

if st.button("View Mood Log"):
    file_path = "data/mood_data.csv" 
    try:
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            st.info("No mood log found or log is empty. Please log your mood first.")
        else:
            df_log = pd.read_csv(file_path)
            if df_log.empty:
                 st.info("Mood log is empty.")
            else:
                timestamp_col_display = None
                if 'timestamp' in df_log.columns:
                    timestamp_col_display = 'timestamp'
                elif 'Date and Time' in df_log.columns:
                    timestamp_col_display = 'Date and Time'
                elif len(df_log.columns) > 0: 
                    timestamp_col_display = df_log.columns[0]

                df_display = df_log.copy() 
                if timestamp_col_display:
                    try:
                        df_display[timestamp_col_display] = pd.to_datetime(df_display[timestamp_col_display], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
                    except Exception:
                        pass 
                
                st.dataframe(df_display.fillna("N/A"))
    except pd.errors.EmptyDataError:
        st.info("Mood log is empty or corrupted.")
    except Exception as e:
        st.error(f"An error occurred while trying to display the mood log: {e}")

# To run -> streamlit run app.py
