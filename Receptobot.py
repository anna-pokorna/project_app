import streamlit as st
from openai import OpenAI
import random
from dotenv import load_dotenv
import os
import pandas as pd

st.set_page_config(
    page_title="Receptobot",
    page_icon=":material/smart_toy:",
    layout="wide"
)

st.logo("data/banner.png")

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

api_klic = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_klic)
# recepty = "babiččina bábovka, klasická česnečka, hovězí guláš, svíčková, kuřecí vývar s játrovými knedlíčky, dršťková polévka, valašská kyselica, dokonalý domácí hamburger, babiččina sekaná, jednoduché palačinky"

df_recepty = pd.read_csv("data/recepty.csv")
recepty_list = df_recepty["nazev_recept"].tolist()
random.shuffle(recepty_list)
recepty_text = "\n".join(f"- {r}" for r in recepty_list)

# Seznam úvodních otázek
uvodni_otazky = [
    "Jak bys dnes popsal/a svůj den jedním slovem?",
    "Na co ses dnes nejvíc těšil/a?",
    "Co ti dnes udělalo radost?",
    "S čím ti můžu pomoci?",
    "Kolik procent baterky ti dnes zbývá?",
    "Kdybys byl/a dnes počasí, jaké by bylo?",
    "Co se ti dnes honí hlavou?"
]

if st.sidebar.button(":material/delete: Nová konverzace"):
    uvodni_otazka = random.choice(uvodni_otazky)
    st.session_state.uvodni_otazka = uvodni_otazka
    st.session_state.messages = [
        {"role": "assistant", "content": uvodni_otazka, "avatar": ":material/smart_toy:"}
    ]
    st.session_state.ukazat_tlacitko = False
    st.session_state.recept_doporuceny = ""
    st.session_state.presun_na_recept = False
    st.session_state.presun_na_seznam = False
    st.rerun()

jdemenato = "jdeme na to!"

# Vložení vlastního CSS pro barvy + zarovnání
st.markdown("""
    <style>
    div[data-testid="stChatMessage"]:nth-child(1) > div {
        background-color: #bcd4c1;
        border-radius: 10px;
        padding: 10px;
    }
    div[data-testid="stChatMessage"]:nth-child(2n) > div {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 10px;
    }
    div[data-testid="stChatMessage"]:nth-child(2n+1) > div {
        background-color: #bcd4c1;
        border-radius: 10px;
        padding: 10px;
    }
    div.stButton > button:first-child {
            background-color: #5C715E;
            color: white;
            font-weight: bold;
            border-radius: 10px;
    }
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


col1, col2 = st.columns([0.1, 0.9], vertical_alignment = "center")
with col1:
    st.image("data/receptobot.png")
with col2:
    st.title("Receptobot")

st.subheader("_Recept na každou náladu i problém_")

# Inicializace při prvním načtení
if "messages" not in st.session_state:
    uvodni_otazka = random.choice(uvodni_otazky)
    st.session_state.uvodni_otazka = uvodni_otazka  # uložíme otázku zvlášť
    st.session_state.messages = [
        {"role": "assistant", "content": uvodni_otazka, "avatar": ":material/smart_toy:"}
    ]
    st.session_state.ukazat_tlacitko = False
    st.session_state.recept_doporuceny = ""
    st.session_state.presun_na_recept = False
    st.session_state.presun_na_seznam = False

# Zobrazení historie
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=msg.get("avatar", None)):
        st.write(msg["content"])

# Uživatelský vstup
user_input = st.chat_input("Napiš odpověď...")

if user_input:
    # Přidáme zprávu uživatele
    user_msg = {"role": "user", "content": user_input, "avatar": ":material/face_3:"}
    st.session_state.messages.append(user_msg)

    with st.chat_message("user", avatar=":material/face_3:"):
        st.write(user_input)

    # Připravíme historii konverzace pro OpenAI
    messages_for_openai = []

    # Přidáme systémovou instrukci vždy na začátek
    messages_for_openai.append({
        "role": "system",
        "content": (
            f"Jsi chatbot, který odpovídá empaticky, ale s vtipem. Vždy odpovídej v návaznosti na předchozí zprávy. "
            f"Do první odpovědi kreativně zakomponuj doporučení jednoho z těchto receptů: \n {recepty_text} \n a zakonči odpověď otázkou, zda má zájem o daný recept. ()"
            f"Důležité! - Pokud je má uživatel zájem o recept, napiš pouze krátkou zprávu - přesný název receptu v prvním pádě tak, jak je v \n {recepty_text} \n a dále ', jdeme na to!'." 
            f"Pokud uživatel nemá zájem o recept a nechce vařit, snaž se ho i tak jemně přesvědčit a doporučovat nějaký z receptů."
        )
    })

    # Přidáme celou dosavadní historii (bez avatarů)
    for msg in st.session_state.messages:
        messages_for_openai.append({
            "role": msg["role"],
            "content": msg["content"]
        })

    # Zavoláme OpenAI
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages_for_openai,
        temperature=0.9,
        max_tokens=300
    )

    response_text = completion.choices[0].message.content

    # Přidáme odpověď asistenta do historie
    bot_msg = {"role": "assistant", "content": response_text, "avatar": ":material/smart_toy:"}
    st.session_state.messages.append(bot_msg)

    with st.chat_message("assistant", avatar=":material/smart_toy:"):
        st.write(response_text)

    if jdemenato in response_text.lower():
        st.session_state.recept_doporuceny = response_text.split(",")[0].lower()
        doporuceny_recept = response_text.split(",")[0].lower()
        st.session_state.ukazat_tlacitko = True
    else:
        st.session_state.ukazat_tlacitko = False
            
# Pokud máme ukázat tlačítko, zobrazíme ho mimo user_input blok
if st.session_state.ukazat_tlacitko:
    if st.button("Chci recept"):
        st.session_state.presun_na_recept = True
    if st.button("Chci rovnou nákupní seznam"):
        st.session_state.presun_na_seznam = True

# Přesměrování na jinou stránku
if st.session_state.presun_na_recept:
    st.switch_page("pages/1_Postup_receptu.py")

if st.session_state.presun_na_seznam:
    st.session_state['value_page1'] = st.session_state.recept_doporuceny
    st.session_state['last_page'] = "page1"
    st.switch_page("pages/2_Nakupni_seznam.py")