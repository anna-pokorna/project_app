import streamlit as st
import pandas as pd

st.session_state.presun_na_recept = False

st.set_page_config(
    page_title="Postup receptu",
    page_icon=":material/chef_hat:",
    layout="wide"
)

st.logo("data/banner.png")

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

# Výběr receptu
st.title("Pracovní postup receptu")

recepty = df["nazev_recept"].tolist()

doporuceny_recept = st.session_state.get("recept_doporuceny", None)
# určíme výchozí index
if doporuceny_recept in recepty:
    default_index = recepty.index(doporuceny_recept)
else:
    default_index = 0  # můžeš zvolit jakýkoli jiný výchozí recept
# vykreslíme selectbox s bezpečným defaultem
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
    #st.markdown(f'<img src="{data["url_obrazek"]}" height="250">', unsafe_allow_html=True)
    #st.image(data["url_obrazek"]) #, use_column_width=True, caption=vybrany_recept)

    # Vyhledat ingredience a vytvořit nákupní seznam

    if st.button("Vyhledat ingredience a vytvořit nákupní seznam"):
        st.session_state.default_recept = vybrany_recept
        st.switch_page("pages/Nákupní seznam.py")


    # Postup
    st.subheader(":material/chef_hat: Postup")
    st.write(data["pracovni_postup"])

    

    # Výživové údaje (volitelně)
    st.subheader(":material/nutrition: Výživové hodnoty (na porci)")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Energie (kcal)", f"{data['energie_1_porce_kcal']}")
    col2.metric("Bílkoviny (g)", f"{data['bilkoviny_v_gramech']}")
    col3.metric("Sacharidy (g)", f"{data['sacharidy_v_gramech']}")
    col4.metric("Tuky (g)", f"{data['tuky_v_gramech']}")

    if st.button("Zobrazit recept na webu"):
        st.markdown(f'<meta http-equiv="refresh" content="0;URL={data["url_recept"]}">', unsafe_allow_html=True)
   