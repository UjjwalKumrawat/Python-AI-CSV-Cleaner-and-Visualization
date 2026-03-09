import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
def convert_value(df, column, value):
     if pd.api.types.is_numeric_dtype(df[column]):
          try:
               return float(value)
          except ValueError:
               st.error(f"{column} requires a numeric value")
               st.stop()
     else:
          return str(value)

st.set_page_config(page_title="AI CSV Cleaner and Visualization", layout="wide")

st.title("AI CSV Cleaner & Analyzer")
st.write("Upload a CSV file and clean missing values interactively.")

# -----------------------------
# STEP 1 : FILE UPLOAD
# -----------------------------

uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])

if uploaded_file:

    if "df" not in st.session_state or st.session_state.get("file_name") != uploaded_file.name:

        df = pd.read_csv(uploaded_file, low_memory=False)

        # convert numeric-like columns safely
        for col in df.columns:
            if df[col].dtype == "object":
                try:
                    df[col] = pd.to_numeric(df[col])
                except (ValueError, TypeError):
                    pass

        st.session_state.df = df
        st.session_state.file_name = uploaded_file.name

    df = st.session_state.df

    st.subheader("Dataset Preview")
    st.dataframe(df.head())

    # -----------------------------
    # STEP 2 : SHOW ROWS & COLUMNS
    # -----------------------------

    rows, cols = df.shape

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Total Rows", rows)

    with col2:
        st.metric("Total Columns", cols)

    # -----------------------------
    # STEP 3 : MISSING VALUE SUMMARY
    # -----------------------------
    # toggle to show/hide column summry
    # Initialize toggle state
    st.subheader("Column Summary")
    if "show_summary" not in st.session_state:
        st.session_state.show_summary = False
    
    # Button to toggle state
    if st.button("Show/Hide "):
        st.session_state.show_summary = not st.session_state.show_summary
    
    # Show summary if state is True
    if st.session_state.show_summary:

     missing_values = df.isnull().sum()

     summary_df = pd.DataFrame({
        "Column Name": df.columns,
        "Missing Values": missing_values.values,
        "Data Type": df.dtypes.astype(str)
     })

     st.dataframe(summary_df)

    # -----------------------------
    # STEP 4 : HANDLE MISSING VALUES
    # -----------------------------

    st.subheader("Fill Missing Values")

    column = st.selectbox("Select Column", df.columns)

    method = st.selectbox(
        "Select Method",
        ["Mean", "Median", "Mode", "Standard Deviation", "Custom Value"]
    )

    custom_value = None

    if method == "Custom Value":
        custom_value = st.text_input("Enter custom value")

    if st.button("Fill Missing Data"):

        try:
            if method in ["Mean", "Median", "Standard Deviation"]:

                if not pd.api.types.is_numeric_dtype(df[column]):
                    st.error("Selected column is not numeric.")
                    st.stop()

            if method == "Mean":
                value = df[column].mean()

            elif method == "Median":
                value = df[column].median()

            elif method == "Mode":
                value = df[column].mode()[0]

            elif method == "Standard Deviation":
                value = df[column].std()

            elif method == "Custom Value":

                if pd.api.types.is_numeric_dtype(df[column]):
                    value = float(custom_value)
                else:
                    value = str(custom_value)

            df[column] = df[column].fillna(value)

            st.session_state.df = df

            st.success(f"Missing values filled in {column}")
            st.rerun()

        except Exception as e:
            st.error(f"ERROR: {e}")

    # -----------------------------
    # SHOW UPDATED DATA
    # -----------------------------

    st.subheader("Updated Dataset")
    st.dataframe(df)

    # -----------------------------
    # STEP 5 : CREATE NEW COLUMN
    # -----------------------------

    st.subheader("Create Conditional Column")

    new_col_name = st.text_input("New Column Name")

    col1, col2, col3 = st.columns(3)

    with col1:
        column1 = st.selectbox("First Column", df.columns)

    if pd.api.types.is_numeric_dtype(df[column1]):
        operators = [">", "<", ">=", "<=", "==", "!="]
    else:
        operators = ["==", "!="]

    with col2:
        operator1 = st.selectbox("Condition Operator", operators)

    with col3:
        value1 = st.text_input("Comparison Value")

    logic = st.selectbox(
        "Logical Operator",
        ["None", "AND", "OR", "NOT"]
    )

    column2 = None
    value2 = None
    operator2 = None

    if logic in ["AND", "OR"]:

        col4, col5, col6 = st.columns(3)

        with col4:
            column2 = st.selectbox("Second Column", df.columns)

        if pd.api.types.is_numeric_dtype(df[column2]):
            operators2 = [">", "<", ">=", "<=", "==", "!="]
        else:
            operators2 = ["==", "!="]

        with col5:
            operator2 = st.selectbox("Second Condition Operator", operators2)

        with col6:
            value2 = st.text_input("Second Comparison Value")

    true_value = st.text_input("Value if True", "True")
    false_value = st.text_input("Value if False", "False")

    if st.button("Create Column"):

        if new_col_name.strip() == "":
            st.error("Please enter a column name")
            st.stop()

        try:

            v1 = convert_value(df, column1, value1)

            ops = {
                ">": lambda x, y: x > y,
                "<": lambda x, y: x < y,
                ">=": lambda x, y: x >= y,
                "<=": lambda x, y: x <= y,
                "==": lambda x, y: x == y,
                "!=": lambda x, y: x != y
            }

            cond1 = ops[operator1](df[column1], v1)

            if logic == "AND":

                v2 = convert_value(df, column2, value2)
                cond2 = ops[operator2](df[column2], v2)
                final_condition = cond1 & cond2

            elif logic == "OR":

                v2 = convert_value(df, column2, value2)
                cond2 = ops[operator2](df[column2], v2)
                final_condition = cond1 | cond2

            elif logic == "NOT":

                final_condition = ~cond1

            else:
                final_condition = cond1

            df[new_col_name] = np.where(final_condition, true_value, false_value)

            st.session_state.df = df

            st.success(f"Column '{new_col_name}' created successfully")

            st.rerun()

        except Exception as e:
            st.error(f"Error: {e}")

    # -----------------------------
    # STEP 6 : DATA STATISTICS
    # -----------------------------

    st.subheader("Dataset Statistics")

    # initialize state
    if "show_stats" not in st.session_state:
        st.session_state.show_stats = False
    
    # toggle button
    if st.button("Show / Hide "):
        st.session_state.show_stats = not st.session_state.show_stats
    
    # display stats
    if st.session_state.show_stats:
          numeric_cols = df.select_dtypes(include=np.number).columns

          if len(numeric_cols) > 0:

               st.success(f"{len(numeric_cols)} numeric column(s) detected")

               # user selects column
               selected_col = st.selectbox(
                    "Select column for statistics",
                    numeric_cols)
        

               st.write("Statistics for:", selected_col)

               stats = pd.DataFrame({"Metric": ["Mean","Median","Std Dev","Min","Max","Count"],
               "Value": [
                df[selected_col].mean(),
                df[selected_col].median(),
                df[selected_col].std(),
                df[selected_col].min(),
                df[selected_col].max(),
                df[selected_col].count()
            ]
        })

               st.dataframe(stats)

               st.divider()

        # option to show full dataset statistics
               if st.checkbox("Show Full Dataset Statistics"):
                    st.dataframe(df.describe())

 
          else:
               st.info("No numeric columns available for statistics")
               
    # -----------------------------
    # STEP 7 : SIMPLE VISUALIZATION
    # -----------------------------
    
    st.subheader("Quick Visualization")
    
    # initialize state
    if "show_chart" not in st.session_state:
        st.session_state.show_chart = False
    
    # toggle button
    if st.button("Show / Hide"):
        st.session_state.show_chart = not st.session_state.show_chart
    
    # show chart only if enabled
    if st.session_state.show_chart:
    
        numeric_columns = df.select_dtypes(include=np.number).columns
    
        if len(numeric_columns) > 0:
    
            chart_type = st.selectbox(
                "Select Chart Type",
                ["Bar Chart", "Line Chart", "Scatter Plot", "Histogram", "Pie Chart", "Box Plot"]
            )
            # allow user to control how many rows to plot
            top_n = st.slider("Number of rows to visualize", 10, 200, 50)
            # Charts that require X and Y axis
            if chart_type in ["Bar Chart", "Line Chart", "Scatter Plot"]:
  
              x_axis = st.selectbox("Select X Axis", df.columns, key="x_axis")
              y_axis = st.selectbox("Select Y Axis", numeric_columns, key="y_axis")
  
              plot_df = df[[x_axis, y_axis]].dropna().head(top_n)
  
              fig, ax = plt.subplots(figsize=(12,6))
  
              if chart_type == "Bar Chart":
                  ax.bar(plot_df[x_axis].astype(str), plot_df[y_axis])
  
              elif chart_type == "Line Chart":
                  ax.plot(plot_df[x_axis], plot_df[y_axis])
  
              elif chart_type == "Scatter Plot":
                  ax.scatter(plot_df[x_axis], plot_df[y_axis])
  
              ax.set_xlabel(x_axis)
              ax.set_ylabel(y_axis)
              ax.set_title(chart_type)
              ax.grid(True)   
              plt.xticks(rotation=45)
              plt.tight_layout()
  
              st.pyplot(fig)

            # Charts that require only one column
            elif chart_type in ["Histogram", "Pie Chart", "Box Plot"]:

               column = st.selectbox("Select Column", numeric_columns, key="single_col")

               fig, ax = plt.subplots(figsize=(10,6))

               if chart_type == "Histogram":
                   ax.hist(df[column].dropna(), bins=20)
                   ax.set_title(f"Histogram of {column}")

               elif chart_type == "Pie Chart":
                   pie_data = df[column].value_counts().head(10)
                   ax.pie(pie_data, labels=pie_data.index, autopct="%1.1f%%")
                   ax.set_title(f"Pie Chart of {column}")

               elif chart_type == "Box Plot":
                   ax.boxplot(df[column].dropna())
                   ax.set_title(f"Box Plot of {column}")

               plt.tight_layout()
               st.pyplot(fig)

        else:
          st.info("No numeric columns available for visualization")
          
          
    # -----------------------------
    # STEP 7 : SIMPLE VISUALIZATION
    # -----------------------------
    
    st.subheader("Outlier Detection")
    # initialize state
    if "show_outliers" not in st.session_state:
        st.session_state.show_outliers = False
    
    # toggle button
    if st.button("Show/Hide"):
        st.session_state.show_outliers = not st.session_state.show_outliers
    
    # display section
    if st.session_state.show_outliers:
    
        numeric_cols = df.select_dtypes(include=np.number).columns
    
        if len(numeric_cols) > 0:
    
            col = st.selectbox("Select column", numeric_cols)
    
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
    
            outliers = df[(df[col] < Q1 - 1.5 * IQR) | (df[col] > Q3 + 1.5 * IQR)]
    
            st.write("Outliers found:", len(outliers))
            st.dataframe(outliers)
    
        else:
            st.info("No numeric columns available for outlier detection")      
                        
    # -----------------------------
    # STEP 8 : DOWNLOAD CLEANED DATA
    # -----------------------------

    st.subheader("Download Cleaned Dataset")

    csv = df.to_csv(index=False)

    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="cleaned_dataset.csv",
        mime="text/csv"
    )

else:
    st.info("Please upload a CSV file to begin.")