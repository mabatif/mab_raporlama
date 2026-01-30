import streamlit as st
import pandas as pd

st.set_page_config(page_title="Test", layout="wide")
st.title("✅ BEYKOZ TEST - ÇALIŞIYOR!")

# Veritabanı
data = {"Tarih": ["2024-01-01"], "Müdürlük": ["Test"], "Sayı": [1]}
df = pd.DataFrame(data)
st.dataframe(df)

st.success("Sistem çalışıyor!")
