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

    st.sidebar.caption("Členství na eshopech:")
    rohlik_xtra = st.sidebar.checkbox("**Mám členství Rohlík Xtra** (doprava zdarma, 4x měsíčně bez minima)")
    kosik_novy = st.sidebar.checkbox("**Jsem nový zákazník Košíku** (doprava zdarma po 60 dní)")

    

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

        if st.button("Chci optimalizovat nákup"):
            st.session_state.vybrane_recepty = vybrane_recepty
            st.session_state.pocet_porci = pocet_porci
            st.session_state.nepotrebuju = nepotrebuju
            #st.switch_page("pages/Optimalizace nákupu.py")

            st.title("Optimalizace nákupu")

            # --- DOPLŇUJÍCÍ NASTAVENÍ ---
            # rohlik_xtra = st.sidebar.checkbox("**Mám členství Rohlík Xtra** (doprava zdarma, 4x měsíčně bez minima)")
            # kosik_novy = st.sidebar.checkbox("**Jsem nový zákazník Košíku** (doprava zdarma po 60 dní)")

            st.markdown("Porovnáme, zda je výhodnější nakoupit vše v jednom e-shopu, nebo nákup rozdělit.")

            # --- PARAMETRY ---
            MIN_ORDER = 749
            ROHLIK_SHIPPING = [(1500, 0), (1199, 49), (999, 69), (0, 89)]
            KOSIK_SHIPPING = [(1200, 0), (0, 89)]

            # # --- NAČTENÍ DAT ---
            # df_rohlik, df_kosik, df_recepty = load_data()

            # recepty_list = df_recepty["recept_nazev"].unique().tolist()

            default_recepty = st.session_state.get("vybrane_recepty", [])
            # vybrane_recepty = st.multiselect("Vyber recepty", recepty_list, default=default_recepty)

            # if "pocet_porci" in st.session_state:
            #     default_porce = st.session_state.pocet_porci
            # else:
            #     default_porce = 4
            # pocet_porci = st.slider("Počet porcí", 1, 10, default_porce)

            if vybrane_recepty:
                dostupne_ingredience = df_recepty[df_recepty["recept_nazev"].isin(vybrane_recepty)]["ingredience_nazev"].unique().tolist()
                
                df_filtered = df_recepty[df_recepty["recept_nazev"].isin(vybrane_recepty) & ~df_recepty["ingredience_nazev"].isin(nepotrebuju)].copy()
                df_filtered["mnozstvi_final"] = (df_filtered["mnozstvi_prepoctene"] / df_filtered["pocet_porci"]) * pocet_porci
                df_agg = df_filtered.groupby(["ingredience_nazev", "unit_katalog"], as_index=False)["mnozstvi_final"].sum()

                total_rohlik = 0
                total_kosik = 0
                best_total = 0
                rohlik_items = []
                kosik_items = []

                for _, row in df_agg.iterrows():
                    ingred = row["ingredience_nazev"]
                    unit = row["unit_katalog"]
                    mnozstvi = row["mnozstvi_final"]

                    kosik_opt = df_kosik[df_kosik["Ingredience"] == ingred]
                    rohlik_opt = df_rohlik[df_rohlik["Ingredience"] == ingred]

                    best_price = float("inf")
                    best_source = None
                    best_cena = 0
                    best_label = ""

                    for _, r in kosik_opt.iterrows():
                        converted = convert_units(mnozstvi, unit, r["Jednotka balení"])
                        if converted is not None and r["Velikost balení"] > 0:
                            kusu = math.ceil(converted / r["Velikost balení"])
                            cena = r["Cena"] * kusu
                            if cena < best_price:
                                best_price = cena
                                best_source = "Košík"
                                best_cena = cena
                                best_label = f'<a href="{r["URL"]}" target="_blank">{r["Produkt"]}</a> ({kusu}×)'

                    for _, r in rohlik_opt.iterrows():
                        converted = convert_units(mnozstvi, unit, r["Jednotka balení"])
                        if converted is not None and r["Velikost balení"] > 0:
                            kusu = math.ceil(converted / r["Velikost balení"])
                            cena = r["Cena"] * kusu
                            if cena < best_price:
                                best_price = cena
                                best_source = "Rohlík"
                                best_cena = cena
                                best_label = f'<a href="{r["URL"]}" target="_blank">{r["Produkt"]}</a> ({kusu}×)'

                    if best_source == "Košík":
                        total_kosik += best_cena
                        kosik_items.append((ingred, round(best_cena, 2), best_label))
                    elif best_source == "Rohlík":
                        total_rohlik += best_cena
                        rohlik_items.append((ingred, round(best_cena, 2), best_label))

                if total_kosik < MIN_ORDER:
                    st.warning(f"Košík: hodnota nákupu {total_kosik:.2f} Kč je pod minimem {MIN_ORDER} Kč — nelze objednat samostatně.")
                if total_rohlik < MIN_ORDER and not rohlik_xtra:
                    st.warning(f"Rohlík: hodnota nákupu {total_rohlik:.2f} Kč je pod minimem {MIN_ORDER} Kč — nelze objednat samostatně.")

                if total_kosik >= MIN_ORDER and (total_rohlik >= MIN_ORDER or rohlik_xtra):
                    doprava_rohlik = 0 if rohlik_xtra else next(v for k, v in ROHLIK_SHIPPING if total_rohlik >= k)
                    doprava_kosik = 0 if kosik_novy else next(v for k, v in KOSIK_SHIPPING if total_kosik >= k)

                    st.subheader("Rozdělený nákup")
                    st.markdown(f"**Košík:** {total_kosik:.2f} Kč + doprava {doprava_kosik:.0f} Kč = {total_kosik + doprava_kosik:.2f} Kč")
                    with st.expander("Detaily nákupu v Košíku"):
                        df_k = pd.DataFrame(kosik_items, columns=["Ingredience", "Cena", "Produkt"])
                        st.markdown('<style>th { text-align: left !important; }</style>', unsafe_allow_html=True)
                        st.markdown('<style>table { width: 100% !important; } th { text-align: left !important; }</style>', unsafe_allow_html=True)
                        st.markdown(df_k.to_html(escape=False, index=False), unsafe_allow_html=True)

                    st.markdown(f"**Rohlík:** {total_rohlik:.2f} Kč + doprava {doprava_rohlik:.0f} Kč = {total_rohlik + doprava_rohlik:.2f} Kč")
                    with st.expander("Detaily nákupu v Rohlíku"):
                        df_r = pd.DataFrame(rohlik_items, columns=["Ingredience", "Cena", "Produkt"])
                        st.markdown('<style>th { text-align: left !important; }</style>', unsafe_allow_html=True)
                        st.markdown('<style>table { width: 100% !important; } th { text-align: left !important; }</style>', unsafe_allow_html=True)
                        st.markdown(df_r.to_html(escape=False, index=False), unsafe_allow_html=True)

                    # redundant st.markdown removed {label} – {cena:.2f} Kč")

                    st.markdown("**Celková cena rozděleného nákupu:**")
                    total_rozdeleny = total_kosik + doprava_kosik + total_rohlik + doprava_rohlik
                    st.success(f"{total_rozdeleny:.2f} Kč")

                    st.markdown(f"Úspora oproti nákupu pouze na **Košíku**: :green-badge[{kosik_total - total_kosik - total_rohlik:.2f} Kč]")
                    st.markdown(f"Úspora oproti nákupu pouze na **Rohlíku**: :green-badge[{rohlik_total - total_kosik - total_rohlik:.2f} Kč]")

                


                else:
                    st.info("Rozdělený nákup není možný – některý košík nesplňuje minimální hodnotu objednávky.")
            else:
                st.info("Vyber alespoň jeden recept pro výpočet optimalizovaného nákupu.")
    
    else:
        st.info("Vyber suroviny, které nemáš doma, abychom ti mohli vytvořit nákupní seznam.")
else:
    st.info("Vyber alespoň jeden recept, aby se zobrazil nákupní seznam.")
