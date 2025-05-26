import streamlit as st
import pandas as pd
from rapidfuzz import process, fuzz

# Page config
st.set_page_config(page_title="Customer Integrity Checker", layout="wide")
st.title("🔍 Customer Integrity Checker")

st.markdown("""
Upload your **Existing Customers** and **New Customers** lists below.  
The tool will check if any of the new customers are already in your database — even if their name has slightly changed.
""")

# --- Sidebar ---
with st.sidebar:
    st.header("📋 Instructions")
    st.markdown("""
    1. Upload your existing customers CSV (must include "Customer Name")
    2. Upload your new customers CSV (must include "Customer Name")
    3. Results show matched customers and classification
    """)
    st.markdown("---")
    st.markdown("🛠️ Built with [Streamlit](https://streamlit.io ) + `rapidfuzz`")

# --- File Upload Section ---
col1, col2 = st.columns(2)

with col1:
    existing_file = st.file_uploader("📂 Upload Existing Customers (CSV)", type=["csv"])

with col2:
    new_file = st.file_uploader("🆕 Upload New Customers (CSV)", type=["csv"])

if existing_file and new_file:
    try:
        # Load CSVs with error handling
        existing_df = pd.read_csv(existing_file, on_bad_lines='skip')
        new_df = pd.read_csv(new_file, on_bad_lines='skip')

        # Validate required column
        if 'Customer Name' not in existing_df.columns or 'Customer Name' not in new_df.columns:
            st.error("⚠️ Both CSVs must contain a column named 'Customer Name'")
        else:
            with st.spinner("Matching customers..."):
                # Common business terms to ignore during matching
                COMMON_WORDS = {
                    "private limited", "pvt ltd", "limited", "company", "corporation",
                    "group", "ltd", "inc", "llc", "plc", "pte", "gmbh", "ag"
                }

                # Normalize names: remove common words and standardize format
                def normalize(name):
                    name = str(name).lower()
                    tokens = [w for w in name.split() if w not in COMMON_WORDS]
                    return " ".join(tokens).strip()

                existing_df['normalized'] = existing_df['Customer Name'].apply(normalize)
                new_df['normalized'] = new_df['Customer Name'].apply(normalize)

                existing_names = existing_df['normalized'].tolist()
                existing_full = existing_df.to_dict(orient='records')

                results = []

                for idx, row in new_df.iterrows():
                    new_name = row['normalized']
                    new_customer = row['Customer Name']

                    match_result = process.extractOne(new_name, existing_names, scorer=fuzz.token_set_ratio)

                    if match_result:
                        match_name, score, _ = match_result
                        matched_row = next((item for item in existing_full if item['normalized'] == match_name), None)
                    else:
                        match_name = score = matched_row = None

                    match_type = "Genuine New"
                    if score and score >= 85:
                        partial_score = fuzz.partial_ratio(new_name, match_name)
                        if partial_score >= 85:
                            match_type = "Exact Match"
                        else:
                            match_type = "Name Change / Variation"

                    results.append({
                        "New Customer": new_customer,
                        "Matched Existing": matched_row['Customer Name'] if matched_row else "None",
                        "Match Score": round(score, 2) if score else "N/A",
                        "Match Type": match_type
                    })

                result_df = pd.DataFrame(results)

                # Display results
                st.success("✅ Matching complete!")
                st.dataframe(result_df, use_container_width=True)

                # Download buttons
                csv = result_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Results as CSV",
                    data=csv,
                    file_name="matched_customers.csv",
                    mime="text/csv"
                )

                excel_buffer = pd.ExcelWriter("matched_customers.xlsx", engine='openpyxl')
                result_df.to_excel(excel_buffer, index=False)
                excel_buffer.close()
                with open("matched_customers.xlsx", "rb") as f:
                    excel_data = f.read()

                st.download_button(
                    label="📄 Download Results as Excel",
                    data=excel_data,
                    file_name="matched_customers.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    except Exception as e:
        st.error(f"❌ An error occurred: {str(e)}")
else:
    st.info("ℹ️ Please upload both files to begin matching.")

# Footer
st.markdown("---")
st.markdown("© 2025 Customer Integrity Checker | Made with ❤️ using Streamlit")
