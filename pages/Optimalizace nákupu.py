import streamlit as st
import pandas as pd
import math

# --- DATA ---
@st.cache_data

def load_data():
    df_rohlik = pd.read_csv("data/p_04_ingredience_rohlik_final.csv")
    df_kosik = pd.read_csv("data/p_04_ingredience_kosik_final.csv")
    df_recepty = pd.read_csv("data/recept_seznam_ingredienci.csv")

    df_recepty["mnozstvi_prepoctene"] = (
        df_recepty["mnozstvi_prepoctene"].str.replace(",", ".").astype(float)
    )
    df_recepty["pocet_porci"] = df_recepty["pocet_porci"].astype(int)
    return df_rohlik, df_kosik, df_recepty

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

st.title("Optimalizace nákupu")

# --- DOPLŇUJÍCÍ NASTAVENÍ ---
rohlik_xtra = st.sidebar.checkbox("**Mám členství Rohlík Xtra** (doprava zdarma, 4x měsíčně bez minima)")
kosik_novy = st.sidebar.checkbox("**Jsem nový zákazník Košíku** (doprava zdarma po 60 dní)")

st.markdown("Porovnáme, zda je výhodnější nakoupit vše v jednom e-shopu, nebo nákup rozdělit.")

# --- PARAMETRY ---
MIN_ORDER = 749
ROHLIK_SHIPPING = [(1500, 0), (1199, 49), (999, 69), (0, 89)]
KOSIK_SHIPPING = [(1200, 0), (0, 89)]

# --- NAČTENÍ DAT ---
df_rohlik, df_kosik, df_recepty = load_data()

recepty_list = df_recepty["recept_nazev"].unique().tolist()

default_recepty = st.session_state.get("vybrane_recepty", [])
vybrane_recepty = st.multiselect("Vyber recepty", recepty_list, default=default_recepty)

#vybrane_recepty = st.multiselect("Vyber recepty", recepty_list)
if "pocet_porci" in st.session_state:
    default_porce = st.session_state.pocet_porci
else:
    default_porce = 4
pocet_porci = st.slider("Počet porcí", 1, 10, default_porce)

if vybrane_recepty:
    dostupne_ingredience = df_recepty[df_recepty["recept_nazev"].isin(vybrane_recepty)]["ingredience_nazev"].unique().tolist()
    #suroviny_doma = st.multiselect("Vyber suroviny, které UŽ máš doma a nechceš je nakupovat", dostupne_ingredience)

    default_suroviny_doma = st.session_state.get("nepotrebuju", [])
    suroviny_doma = st.multiselect("Vyber suroviny, které UŽ máš doma a nechceš je nakupovat", dostupne_ingredience, default=default_suroviny_doma)



    df_filtered = df_recepty[df_recepty["recept_nazev"].isin(vybrane_recepty) & ~df_recepty["ingredience_nazev"].isin(suroviny_doma)].copy()
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

        # Výpočet nerozděleného nákupu - toto je blbost !!! předělat
        cena_rohlik_full = total_rohlik + total_rohlik + (0 if rohlik_xtra else next(v for k, v in ROHLIK_SHIPPING if total_rohlik + total_rohlik >= k))
        cena_kosik_full = total_kosik + total_kosik + (0 if kosik_novy else next(v for k, v in KOSIK_SHIPPING if total_kosik + total_kosik >= k))


        

        if "kosik_total" in st.session_state and "rohlik_total" in st.session_state:
            if vybrane_recepty == default_recepty:
                #st.markdown(f"Rohlík: {st.session_state.kosik_total:.2f} Kč")
                #st.markdown(f"Košík: {st.session_state.rohlik_total:.2f} Kč")
                #st.markdown("Úspora oproti nákupu pouze na **Košíku**:")
                #st.success(f"{st.session_state.kosik_total - total_kosik - total_rohlik:.2f} Kč")
                st.markdown(f"Úspora oproti nákupu pouze na **Košíku**: :green-badge[{st.session_state.kosik_total - total_kosik - total_rohlik:.2f} Kč]")
                st.markdown(f"Úspora oproti nákupu pouze na **Rohlíku**: :green-badge[{st.session_state.rohlik_total - total_kosik - total_rohlik:.2f} Kč]")

                #st.markdown("Úspora oproti nákupu pouze na **Rohlíku**:")
                #st.success(f"{st.session_state.rohlik_total - total_kosik - total_rohlik:.2f} Kč")
    else:
        st.info("Rozdělený nákup není možný – některý košík nesplňuje minimální hodnotu objednávky.")
else:
    st.info("Vyber alespoň jeden recept pro výpočet optimalizovaného nákupu.")

