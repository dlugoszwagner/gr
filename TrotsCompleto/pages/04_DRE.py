from pathlib import Path

import streamlit as st
import pandas as pd


pasta_datasets = Path(__file__).parent.parent / 'datasets'

df_dre = pd.read_csv(
    pasta_datasets / 'DRE.csv', 
    encoding='latin-1', 
    parse_dates=True, 
    sep=';', 
)


# Replace None (NaN) values with empty strings
df_dre = df_dre.fillna('')



st.dataframe(df_dre)