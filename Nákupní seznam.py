import streamlit as st
import pandas as pd
import math

# --- DATA ---
@st.cache_data
def load_data():
    df_rohlik = pd.read_csv("data/p_04_ingredience_rohlik_final.csv")
    df_kosik = pd.read_csv("data/p_04_ingredience_kosik_final.csv")
    df_recepty = pd.read_csv("data/recept_seznam_ingredienci.csv")

    # Čištění
    df_recepty["prepocet_mnozstvi_na_katalogovou_jednotku"] = (
        df_recepty["prepocet_mnozstvi_na_katalogovou_jednotku"].str.replace(",", ".").astype(float)
    )
    df_recepty["mnozstvi_prepoctene"] = (
        df_recepty["mnozstvi_prepoctene"].str.replace(",", ".").astype(float)
    )
    df_recepty["mnozstvi"] = (
        df_recepty["mnozstvi"].str.replace(",", ".").astype(float)
    )
    return df_rohlik, df_kosik, df_recepty

df_rohlik, df_kosik, df_recepty = load_data()

# --- FUNKCE ---
def convert_units(quantity, from_unit, to_unit):
    conversions = {
        ("g", "kg"): lambda x: x / 1000,
        ("kg", "g"): lambda x: x * 1000,
        ("ml", "l"): lambda x: x / 1000,
        ("l", "ml"): lambda x: x * 1000
    }
    if from_unit == to_unit:
        return quantity
    return conversions.get((from_unit, to_unit), lambda x: None)(quantity)

def get_ingredients_for_recepty(df_recepty, recepty, pocet_porci=1):
    filt = df_recepty["recept_nazev"].isin(recepty)
    df = df_recepty[filt].copy()
    df["mnozstvi_surovina"] = (df["mnozstvi"] / df["pocet_porci"]) * pocet_porci
    df["mnozstvi_final"] = (df["mnozstvi_prepoctene"] / df["pocet_porci"]) * pocet_porci
    df = df.groupby(["ingredience_nazev", "unit_katalog"], as_index=False).agg({
        "mnozstvi_surovina": "sum",
        "mnozstvi_final": "sum"
    })
    return df

def get_products(df_shop, ingredient_list):
    df = df_shop[df_shop["Ingredience"].isin(ingredient_list)]
    return df[["Ingredience", "Produkt", "Jednotková cena", "Cena", "Velikost balení", "Jednotka balení", "URL"]]

# --- UI ---
st.title("Nákupní seznam podle receptů")

st.sidebar.header("Nastavení")

recepty_list = df_recepty["recept_nazev"].unique().tolist()
vybrane_recepty = st.multiselect("Vyber recepty", recepty_list)
#st.session_state.vybrane_recepty = vybrane_recepty
pocet_porci = st.sidebar.slider("Vyber počet porcí:", 1, 10, 4)
#zobrazeni = st.radio("Způsob výpočtu cen:", ["Cena za balení", "Cena za recept"])

if vybrane_recepty:
    st.subheader("Suroviny dle vybraných receptů")
    with st.container(height=300, border=True):
        for recept in vybrane_recepty:
            st.markdown(f"**{recept}**")
            ingred = df_recepty[df_recepty["recept_nazev"] == recept][[
                "ingredience_nazev", "mnozstvi", "jednotka",
                "mnozstvi_prepoctene", "unit_katalog", "pocet_porci"]]
            ingred["mnozstvi_surovina"] = (ingred["mnozstvi"] / ingred["pocet_porci"]) * pocet_porci
            ingred["mnozstvi_final"] = (ingred["mnozstvi_prepoctene"] / ingred["pocet_porci"]) * pocet_porci
            for _, row in ingred.iterrows():
                st.markdown(f"- :orange-badge[{row['ingredience_nazev']}] — :blue[{row['mnozstvi_surovina']:.2f} {row['jednotka']}]")

    ingredience_df = get_ingredients_for_recepty(df_recepty, vybrane_recepty, pocet_porci)
    suroviny = ingredience_df["ingredience_nazev"].tolist()

    nepotrebuju = st.sidebar.multiselect("Vyber suroviny, které UŽ máš doma", suroviny)
    k_nakupu = [s for s in suroviny if s not in nepotrebuju]

    zobrazeni = st.sidebar.radio("Způsob výpočtu cen:", ["Cena za balení", "Cena za recept"])

    

    

    if k_nakupu:
        st.subheader("Nákupní seznam")

        produkty_rohlik = get_products(df_rohlik, k_nakupu)
        produkty_kosik = get_products(df_kosik, k_nakupu)

        mnozstvi_dict = dict(zip(zip(ingredience_df["ingredience_nazev"], ingredience_df["unit_katalog"]), ingredience_df["mnozstvi_final"]))

        col1, col2 = st.columns(2)

        with col1:
            st.header("Košík")
            kosik_total = 0
            with st.container(border=True):
                for surovina in k_nakupu:
                    unit_key = ingredience_df[ingredience_df["ingredience_nazev"] == surovina]["unit_katalog"].values[0]
                    mnozstvi = mnozstvi_dict.get((surovina, unit_key), 0)
                    items = df_kosik[df_kosik["Ingredience"] == surovina]
                    for _, row in items.iterrows():
                        if zobrazeni == "Cena za balení":
                            baleni = row["Velikost balení"]
                            jednotka = row["Jednotka balení"]
                            mnozstvi_prep = convert_units(mnozstvi, unit_key, jednotka)
                            if mnozstvi_prep is None:
                                continue
                            kusu = math.ceil(mnozstvi_prep / baleni) if baleni > 0 else 0
                            cena = row["Cena"] * kusu
                            kosik_total += cena
                            st.markdown(f"- [{row['Produkt']}]({row['URL']})\n  {cena:.2f} Kč ({kusu}×)")
                        else:
                            cena = row["Jednotková cena"] * mnozstvi
                            kosik_total += cena
                            st.markdown(f"- [{row['Produkt']}]({row['URL']})\n  {cena:.2f} Kč")
            st.markdown(f"**Celkem za {'celý nákup' if zobrazeni == 'Cena za balení' else 'množství dle receptu'}: {kosik_total:.2f} Kč**")
            if zobrazeni == 'Cena za balení':
                st.session_state.kosik_total = kosik_total

        with col2:
            st.header("Rohlík")
            rohlik_total = 0
            with st.container(border=True):
                for surovina in k_nakupu:
                    unit_key = ingredience_df[ingredience_df["ingredience_nazev"] == surovina]["unit_katalog"].values[0]
                    mnozstvi = mnozstvi_dict.get((surovina, unit_key), 0)
                    items = df_rohlik[df_rohlik["Ingredience"] == surovina]
                    for _, row in items.iterrows():
                        if zobrazeni == "Cena za balení":
                            baleni = row["Velikost balení"]
                            jednotka = row["Jednotka balení"]
                            mnozstvi_prep = convert_units(mnozstvi, unit_key, jednotka)
                            if mnozstvi_prep is None:
                                continue
                            kusu = math.ceil(mnozstvi_prep / baleni) if baleni > 0 else 0
                            cena = row["Cena"] * kusu
                            rohlik_total += cena
                            st.markdown(f"- [{row['Produkt']}]({row['URL']})\n  {cena:.2f} Kč ({kusu}×)")
                        else:
                            cena = row["Jednotková cena"] * mnozstvi
                            rohlik_total += cena
                            st.markdown(f"- [{row['Produkt']}]({row['URL']})\n  {cena:.2f} Kč")
            st.markdown(f"**Celkem za {'celý nákup' if zobrazeni == 'Cena za balení' else 'množství dle receptu'}: {rohlik_total:.2f} Kč**")
            if zobrazeni == 'Cena za balení':
                st.session_state.rohlik_total = rohlik_total

        if st.button("Chci optimalizovat nákup."):
            st.session_state.vybrane_recepty = vybrane_recepty
            st.session_state.pocet_porci = pocet_porci
            st.session_state.nepotrebuju = nepotrebuju
            st.switch_page("pages/Optimalizace nákupu.py")
    
    else:
        st.info("Vyber suroviny, které nemáš doma, abychom ti mohli vytvořit nákupní seznam.")
else:
    st.info("Vyber alespoň jeden recept, aby se zobrazil nákupní seznam.")
