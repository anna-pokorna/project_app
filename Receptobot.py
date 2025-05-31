import streamlit as st
from openai import OpenAI
import random
from dotenv import load_dotenv
import os

st.set_page_config(
    page_title="Receptobot",
    page_icon=":material/smart_toy:",
    layout="wide"
)

load_dotenv()  # toto načte proměnné z .env

api_klic = os.getenv("OPENAI_API_KEY")
#api_klic = "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"
client = OpenAI(api_key=api_klic)
recepty = "babiččina bábovka, klasická česnečka, hovězí guláš, svíčková, kuřecí vývar s játrovými knedlíčky, dršťková polévka, valašská kyselica, dokonalý domácí hamburger, babiččina sekaná, jednoduché palačinky"

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
    st.rerun()

jdemenato = "jdeme na to"

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
    </style>
""", unsafe_allow_html=True)


st.title("Receptobot")
st.subheader("_Recept na každou náladu_")

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
            "Jsi chatbot, který odpovídá empaticky, ale s vtipem. Vždy odpovídej v návaznosti na předchozí zprávy. "
            "Do první odpovědi kreativně zakomponuj doporučení jednoho z těchto receptů: " + recepty + "a zakonči odpověď otázkou, zda má zájem o recept. ()"
            "Důležité! - Pokud je má uživatel zájem o recept, napiš pouze krátkou zprávu - přesný název receptu v prvním pádě tak, jak je v " + recepty + " a dále ', jdeme na to!'." 
            "Pokud uživatel nemá zájem o recept a nechce vařit, snaž se ho i tak jemně přesvědčit a doporučovat nějaký z receptů."
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
        st.session_state.ukazat_tlacitko = True
    else:
        st.session_state.ukazat_tlacitko = False
            
# Pokud máme ukázat tlačítko, zobrazíme ho mimo user_input blok
if st.session_state.ukazat_tlacitko:
    if st.button("Chci recept"):
        st.session_state.presun_na_recept = True

# Přesměrování na jinou stránku
if st.session_state.presun_na_recept:
    st.switch_page("pages/Postup receptu.py")

