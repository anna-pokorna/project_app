import streamlit as st
import pandas as pd


st.set_page_config(
    page_title="Postup receptu",
    page_icon=":material/chef_hat:",
    #layout="wide"
)
# Načtení dat
@st.cache_data
def load_data():
    df = pd.read_csv("data/recepty.csv")
    return df

df = load_data()

# Výběr receptu
st.title("Pracovní postup receptu")
recepty = df["nazev_recept"].tolist()
vybrany_recept = st.sidebar.selectbox("Vyber recept", recepty)

# Zobrazení informací
if vybrany_recept:
    data = df[df["nazev_recept"] == vybrany_recept].iloc[0]

    st.header(vybrany_recept.capitalize())

    # Obrázek receptu
    st.image(data["url_obrazek"]) #, use_column_width=True, caption=vybrany_recept)

    # Postup
    st.subheader(":material/chef_hat: Postup")
    st.write(data["pracovni_postup"])

    if st.button("Zobrazit recept na webu"):
        st.markdown(f'<meta http-equiv="refresh" content="0;URL={data["url_recept"]}">', unsafe_allow_html=True)

    # Výživové údaje (volitelně)
    st.subheader(":material/nutrition: Výživové hodnoty (na porci)")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Energie (kcal)", f"{data['energie_1_porce_kcal']}")
    col2.metric("Bílkoviny (g)", f"{data['bilkoviny_v_gramech']}")
    col3.metric("Sacharidy (g)", f"{data['sacharidy_v_gramech']}")
    col4.metric("Tuky (g)", f"{data['tuky_v_gramech']}")

   