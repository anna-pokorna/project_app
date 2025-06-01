import streamlit as st
import pandas as pd

st.session_state.presun_na_recept = False

# Title stránky a rozložení
st.set_page_config(
    page_title="Postup receptu",
    page_icon=":material/chef_hat:",
    layout="wide"
)

# Vložení loga
st.logo("data/banner.png")

# Vložení vlastního stylu (tlačítka)
st.markdown("""
    <style>
        div.stButton > button:first-child {
            background-color: #5C715E;
            color: white;
            font-weight: bold;
            border-radius: 10px;
        }
        div.stButton > button:first-child:hover {
            background-color: #4A5B4A;
            color: white;
        }

        div.stButton > button:first-child:active {
            background-color: #3B4A3B;
            color: white;
        }

        div.stButton > button:first-child:focus {
            background-color: #5C715E;
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

# Načtení dat
@st.cache_data
def load_data():
    df = pd.read_csv("data/recepty.csv")
    return df

df = load_data()

postupy = pd.read_csv("data/recept_postup.csv")
nazvy = postupy.columns.tolist()

# Výběr receptu
st.title("Pracovní postup receptu")

recepty = df["nazev_recept"].tolist()

# Přenesení default výběru z doporučení chatbota
doporuceny_recept = st.session_state.get("recept_doporuceny", None)

if doporuceny_recept in recepty:
    default_index = recepty.index(doporuceny_recept)
else:
    default_index = 0   

vybrany_recept = st.sidebar.selectbox("Vyber recept", recepty, index=default_index)


# Zobrazení informací
if vybrany_recept:
    data = df[df["nazev_recept"] == vybrany_recept].iloc[0]

    st.header(vybrany_recept.capitalize())

    # Obrázek receptu
    st.markdown(f"""
        <div style="margin-bottom: 40px;">
            <img src="{data["url_obrazek"]}" height="300">
        </div>
    """, unsafe_allow_html=True)
   
    # Tlačítko pro přesun na nákupní sezna,
    if st.button("Vyhledat ingredience a vytvořit nákupní seznam"):
        st.session_state['value_page2'] = vybrany_recept
        st.session_state['last_page'] = "page2"
        st.switch_page("pages/2_Nakupni_seznam.py")


    # Výpis postupu po krocích
    st.subheader(":material/chef_hat: Postup")
    kroky = postupy[vybrany_recept].dropna().tolist()
    
    for i, krok in enumerate(kroky, start=1):
        st.markdown(
            f"""
            <div style="background-color:#ffffff; padding:10px; border-radius:10px; margin-bottom:15px;">
                <b>{i}.</b> {krok}
            </div>
            """,
            unsafe_allow_html=True
        )

    # Výživové údaje
    st.subheader(":material/nutrition: Výživové hodnoty (na porci)")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Energie (kcal)", f"{data['energie_1_porce_kcal']}")
    col2.metric("Bílkoviny (g)", f"{data['bilkoviny_v_gramech']}")
    col3.metric("Sacharidy (g)", f"{data['sacharidy_v_gramech']}")
    col4.metric("Tuky (g)", f"{data['tuky_v_gramech']}")

    # Tlačítko pro zobrazení na původním webu
    if st.button("Zobrazit recept na webu"):
        st.markdown(f'<meta http-equiv="refresh" content="0;URL={data["url_recept"]}">', unsafe_allow_html=True)
   