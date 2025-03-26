import streamlit as st
import pandas as pd
import plotly.express as px

# Load the dataset
file_path = "nielsen_holidays_trunc.csv"  # Ensure this file is in the same directory
df = pd.read_csv(file_path)

# Ensure Year and Week are numeric
df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
df['Week'] = pd.to_numeric(df['Week'], errors='coerce')

# Generate a date column (Monday of the given Year & Week)
df['date'] = pd.to_datetime(df['Year'].astype(str) + df['Week'].astype(str) + '-1', format='%Y%W-%w', errors='coerce')

# Remove spaces from manufacturer names
df["WELLS_KEY MANUFACTURER(C)"] = df["WELLS_KEY MANUFACTURER(C)"].astype(str).str.strip()

# Convert promo vs. non-promo into categories
df["Promo Type"] = df["ANY PROMO UNITS"].apply(lambda x: "Promo" if x > 0 else "Non-Promo")

# Convert holiday column (Include 'All' Option)
df["Is Holiday"] = df["holiday"].apply(lambda x: "Holiday" if isinstance(x, str) and len(x) > 0 else "Non-Holiday")

# Sidebar Filters
st.sidebar.header("Filters")

# Manufacturer filter
manufacturers = df["WELLS_KEY MANUFACTURER(C)"].dropna().unique()
selected_manufacturers = st.sidebar.multiselect("Select Manufacturer(s)", manufacturers, default=manufacturers[:6])

# Year filter
years = df["Year"].dropna().unique()
selected_years = st.sidebar.multiselect("Select Year(s)", years, default=years[:3])

# Package Type filter
package_types = df["WELLS_PACKAGE TYPE(C)"].dropna().unique()
selected_package_types = st.sidebar.multiselect("Select Package Type(s)", package_types, default=package_types[:3])

# Segment filter
segments = df["WELLS_SEGMENT(C)"].dropna().unique()
selected_segments = st.sidebar.multiselect("Select Segment(s)", segments, default=segments[:3])

# Holiday filter with "All" option
holiday_options = ["All"] + list(df["Is Holiday"].unique())
selected_holiday = st.sidebar.selectbox("Select Holiday Filter", holiday_options)

# Toggle for Weekly or Monthly Aggregation
view_option = st.sidebar.radio("View Sales Data By:", ["Weekly", "Monthly"])

# Apply filters
filtered_df = df[
    (df["WELLS_KEY MANUFACTURER(C)"].isin(selected_manufacturers)) &
    (df["Year"].isin(selected_years)) &
    (df["WELLS_PACKAGE TYPE(C)"].isin(selected_package_types)) &
    (df["WELLS_SEGMENT(C)"].isin(selected_segments))
]

# Apply Holiday Filter
if selected_holiday != "All":
    filtered_df = filtered_df[filtered_df["Is Holiday"] == selected_holiday]

# Display filtered records count
st.write(f"Showing **{len(filtered_df)}** records based on selected filters:")

# Display filtered dataframe
st.dataframe(filtered_df)

# Sales Trends Over Time by Manufacturer (Weekly or Monthly)
st.title("Sales Trends Over Time by Manufacturer")

if view_option == "Weekly":
    df_trends = filtered_df.groupby(["Week", "WELLS_KEY MANUFACTURER(C)"])["SALES DOLLARS"].sum().reset_index()
    x_col = "Week"
    x_axis_label = "Week Number"
else:
    filtered_df["Month"] = filtered_df["date"].dt.to_period("M").astype(str)
    df_trends = filtered_df.groupby(["Month", "WELLS_KEY MANUFACTURER(C)"])["SALES DOLLARS"].sum().reset_index()
    x_col = "Month"
    x_axis_label = "Month"

if not df_trends.empty:
    fig = px.line(
        df_trends, x=x_col, y="SALES DOLLARS",
        color="WELLS_KEY MANUFACTURER(C)", markers=True,
        title=f"Sales Trends Over Time by Manufacturer ({view_option})",
        labels={"SALES DOLLARS": "Total Sales ($)", x_col: x_axis_label, "WELLS_KEY MANUFACTURER(C)": "Manufacturer"}
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning(f"No data available for the selected {view_option} view.")

# Promo vs. Non-Promo Sales for Each Manufacturer by Week
st.title("Promo vs. Non-Promo Sales by Manufacturer (Weekly)")
df_promo_trends = filtered_df.groupby(["Week", "WELLS_KEY MANUFACTURER(C)", "Promo Type"])["SALES DOLLARS"].sum().reset_index()
if not df_promo_trends.empty:
    fig2 = px.bar(
        df_promo_trends, x="Week", y="SALES DOLLARS",
        color="Promo Type", barmode="group",
        facet_col="WELLS_KEY MANUFACTURER(C)",
        title="Promo vs. Non-Promo Sales by Manufacturer (Weekly)",
        labels={"SALES DOLLARS": "Total Sales ($)", "Week": "Week Number", "Promo Type": "Promotion Status"},
        category_orders={"Promo Type": ["Non-Promo", "Promo"]}
    )
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.warning("No data available for Promo vs. Non-Promo comparison.")

# Download Filtered Data
st.download_button(
    label="Download Filtered Data as CSV",
    data=filtered_df.to_csv(index=False).encode("utf-8"),
    file_name="filtered_nielsen_holidays.csv",
    mime="text/csv"
)
