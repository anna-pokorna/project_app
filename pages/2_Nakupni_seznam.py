import streamlit as st
import pandas as pd
import math

st.session_state.presun_na_seznam = False

# Title stránky a rozložení
st.set_page_config(
    page_title="Nákupní seznam",
    page_icon=":material/grocery:",
    layout="wide"
)

# Vložení vlastního stylu (tlačítka)
st.markdown("""
    <style>
    /* Sidebar tlačítko - normal */
    section[data-testid="stSidebar"] button[kind="secondary"] {
        background-color: #5C715E;
        color: white;
        font-weight: bold;
        border-radius: 10px;
    }

    /* Sidebar tlačítko - hover */
    section[data-testid="stSidebar"] button[kind="secondary"]:hover {
        background-color: #4A5B4A;
        color: white;
    }

    /* Sidebar tlačítko - active */
    section[data-testid="stSidebar"] button[kind="secondary"]:active {
        background-color: #3B4A3B;
        color: white;
    }

    /* Sidebar tlačítko - focus */
    section[data-testid="stSidebar"] button[kind="secondary"]:focus {
        background-color: #5C715E;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

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

def format_number(n):
    if n == int(n):
        return str(int(n))  # celé číslo, bez desetinných míst
    else:
        return f"{n:.2f}"  # číslo s dvěma desetinnými místy


# Vložení loga
st.logo("data/banner.png")

# Název stránky
st.title("Nákupní seznam podle receptů")

st.sidebar.header(":material/settings: Možnosti")

# Výběr receptů
recepty_list = df_recepty["recept_nazev"].unique().tolist()

# Přenesení default výběru z doporučení chatbota nebo z postupu
default_recept = []

if 'last_page' in st.session_state:
    if st.session_state['last_page'] == "page1":
        default_recept = st.session_state.get('value_page1', [])
    elif st.session_state['last_page'] == "page2":
        default_recept = st.session_state.get('value_page2', [])

vybrane_recepty = st.multiselect("Vyber recepty", recepty_list, default=default_recept)

# Výběr dalších možností, do sidebaru
pocet_porci = st.sidebar.slider("Vyber počet porcí:", 1, 10, 4)

st.sidebar.write("Členství na eshopech:")
rohlik_xtra = st.sidebar.checkbox("**Mám členství Rohlík Xtra** (doprava zdarma, 4x měsíčně bez minima)")
kosik_novy = st.sidebar.checkbox("**Jsem nový zákazník Košíku** (doprava zdarma po 60 dní)")

optimalizace_help = '''
    Vyplatí se nakoupit vše na jednom e-shopu, nebo je výhodnější nákup rozdělit? 
    '''
optimalizace = st.sidebar.button("Chci optimalizovat nákup", help=optimalizace_help)

# Nastavení parametrů
MIN_ORDER = 749
ROHLIK_SHIPPING = [(1500, 0), (1199, 49), (999, 69), (1, 89), (0, 0)]
KOSIK_SHIPPING = [(1200, 0), (1, 89), (0, 0)]


if vybrane_recepty:
    ingredience_df = get_ingredients_for_recepty(df_recepty, vybrane_recepty, pocet_porci)
    suroviny = ingredience_df["ingredience_nazev"].tolist()

    st.subheader(":material/grocery: Suroviny dle vybraných receptů")

    with st.container(height=250, border=True):
        for recept in vybrane_recepty:
            st.markdown(f"""
            <span style="text-transform: uppercase;color: #5c715e;font-size: 1.2rem;">
                {recept}
            </span>
            """, unsafe_allow_html=True)
            ingred = df_recepty[df_recepty["recept_nazev"] == recept][[
                "ingredience_nazev", "mnozstvi", "jednotka",
                "mnozstvi_prepoctene", "unit_katalog", "pocet_porci"]]
            ingred["mnozstvi_surovina"] = (ingred["mnozstvi"] / ingred["pocet_porci"]) * pocet_porci
            ingred["mnozstvi_final"] = (ingred["mnozstvi_prepoctene"] / ingred["pocet_porci"]) * pocet_porci
            for _, row in ingred.iterrows():
                st.markdown(f"- **{row['ingredience_nazev']}** — {format_number(row['mnozstvi_surovina'])} {row['jednotka']}")
    
    # Možnost vyřazení některých surovin z nákupu
    nepotrebuju = st.multiselect("Vyber suroviny, které **už máš doma** - budou vyřazeny z nákupního seznamu.", suroviny)  
    
    k_nakupu = [s for s in suroviny if s not in nepotrebuju]

    zobrazeni_help =  '''
    Cena za balení - porovnávají se **prodejní ceny** jednotlivých produktů, počet balení se vypočítá podle zvoleného počtu porcí. 
    
    Cena za recept - porovnávají se **ceny za jednotku** (např. za kg nebo l), ceny se vypočítají podle množství potřebného do receptu dle zvoleného počtu porcí.
    '''
    zobrazeni = st.sidebar.radio("Způsob výpočtu cen:", ["Cena za balení", "Cena za recept"], help=zobrazeni_help)

    # Sestavení nákupního seznamu
    if k_nakupu:
        st.subheader(":material/shopping_cart: Nákupní seznam")

        produkty_rohlik = get_products(df_rohlik, k_nakupu)
        produkty_kosik = get_products(df_kosik, k_nakupu)

        mnozstvi_dict = dict(zip(zip(ingredience_df["ingredience_nazev"], ingredience_df["unit_katalog"]), ingredience_df["mnozstvi_final"]))

        kosik_rows = []
        rohlik_rows = []
        kosik_total = 0
        rohlik_total = 0
        
        #součty celkových cen za balení pro výpočet dopravy při rozděleném nákupu
        kosik_pomocny = 0
        rohlik_pomocny = 0

        # KOŠÍK
        for surovina in k_nakupu:
            unit_key = ingredience_df[ingredience_df["ingredience_nazev"] == surovina]["unit_katalog"].values[0]
            mnozstvi = mnozstvi_dict.get((surovina, unit_key), 0)
            items = df_kosik[df_kosik["Ingredience"] == surovina]
            for _, row in items.iterrows():
                baleni = row["Velikost balení"]
                jednotka = row["Jednotka balení"]
                mnozstvi_prep = convert_units(mnozstvi, unit_key, jednotka)
                if mnozstvi_prep is None:
                    continue
                kusu = math.ceil(mnozstvi_prep / baleni) if baleni > 0 else 0
                cena_baleni = row["Cena"] * kusu
                cena_mnozstvi = row["Jednotková cena"] * mnozstvi
                if zobrazeni == "Cena za balení":    
                    kosik_total += cena_baleni
                    kosik_rows.append({
                        "Ingredience": surovina,
                        " ": f'<img src="{row["IMG"]}" class="centered" height="50">',
                        "Produkt Košík": f'<a href="{row["URL"]}" target="_blank">{row["Produkt"]}</a> ({kusu}×)',
                        "Cena": round(cena_baleni, 2),
                    })
                else:
                    kosik_total += cena_mnozstvi   
                    kosik_pomocny += cena_baleni    
                    kosik_rows.append({
                        "Ingredience": surovina,
                        " ": f'<img src="{row["IMG"]}" class="centered" height="50">',
                        "Produkt Košík": f'<a href="{row["URL"]}" target="_blank">{row["Produkt"]}</a>',
                        "Cena": round(cena_mnozstvi, 2),
                    })

        # ROHLÍK
        for surovina in k_nakupu:
            unit_key = ingredience_df[ingredience_df["ingredience_nazev"] == surovina]["unit_katalog"].values[0]
            mnozstvi = mnozstvi_dict.get((surovina, unit_key), 0)
            items = df_rohlik[df_rohlik["Ingredience"] == surovina]
            for _, row in items.iterrows():
                baleni = row["Velikost balení"]
                jednotka = row["Jednotka balení"]
                obrazek = f'<img src="{row["IMG"]}" width="50">' 
                mnozstvi_prep = convert_units(mnozstvi, unit_key, jednotka)
                if mnozstvi_prep is None:
                    continue
                kusu = math.ceil(mnozstvi_prep / baleni) if baleni > 0 else 0
                cena_baleni = row["Cena"] * kusu
                cena_mnozstvi = row["Jednotková cena"] * mnozstvi
                if zobrazeni == "Cena za balení":
                    rohlik_total += cena_baleni 
                    rohlik_rows.append({
                        "Ingredience": surovina,
                        "  ": f'<img src="{row["IMG"]}" class="centered" height="50">',
                        "Produkt Rohlík": f'<a href="{row["URL"]}" target="_blank">{row["Produkt"]}</a> ({kusu}×)',
                        "Cena ": round(cena_baleni, 2), 
                    })
                else:
                    rohlik_total += cena_mnozstvi
                    rohlik_pomocny += cena_baleni 
                    rohlik_rows.append({
                        "Ingredience": surovina,
                        "  ": f'<img src="{row["IMG"]}" class="centered" height="50">',
                        "Produkt Rohlík": f'<a href="{row["URL"]}" target="_blank">{row["Produkt"]}</a>',
                        "Cena ": round(cena_mnozstvi, 2),
                    })
            if zobrazeni == 'Cena za balení':
                st.session_state.rohlik_total = rohlik_total
                rohlik_total_baleni = rohlik_total        
                
                
        df_kosik_rows = pd.DataFrame(kosik_rows)
        df_rohlik_rows = pd.DataFrame(rohlik_rows)

        # Spojení nákupních seznamů pro oba eshopy do jedné tabulky 
        spojene = pd.merge(df_kosik_rows, df_rohlik_rows, on="Ingredience", how="outer")


        st.markdown(f"**Celkem za {'celý nákup' if zobrazeni == 'Cena za balení' else 'množství dle receptu'}:**")

        # Zobrazení součtů
        col1, col2 = st.columns(2)
        
        with col1:
            if kosik_total <= rohlik_total:
                st.success(f"**Košík**: {kosik_total:.2f} Kč")
            else:
                st.error(f"**Košík**: {kosik_total:.2f} Kč")
        with col2:
            if rohlik_total <= kosik_total:
                st.success(f"**Rohlík**: {rohlik_total:.2f} Kč")
            else:
                st.error(f"**Rohlík**: {rohlik_total:.2f} Kč")

        # Vlastní styl pro tabulku
        st.markdown("""
        <style>
        .table-scroll-wrapper {
            max-height: 400px;
            overflow-y: auto;
            overflow-x: scroll; 
            -webkit-overflow-scrolling: touch;
            border: 2px solid #f4f1ee;  /* jemný rámeček */
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
            padding: 0;  /* důležité: žádné odsazení */
        }

        /* Tabulka */
        .custom-card-table {
            background-color: #ffffff;
            width: 100%;
            border-collapse: collapse;
            border-spacing: 0;
            font-family: 'Source Sans Pro', sans-serif;
            border: none;
            border-radius: 12px;
        }

        /* Hlavička */
        .custom-card-table th {
            background-color: #5c715e;
            color: white;
            text-align: left;
            padding: 0.75rem;
            position: sticky;
            top: 0;
            border: none;
        }
        .custom-card-table th:first-child {
            border-top-left-radius: 12px;
        }
        .custom-card-table th:last-child {
            border-top-right-radius: 12px;
        }

        /* Tělo */
        .custom-card-table td {
            padding: 0.75rem;
            border: none;
        }

        /* Aby se obrázky centrovaly a nemizely */
        .custom-card-table td img {
            display: block;
            margin: 0 auto;
            max-height: 50px;
            width: auto;
        }
                    
        /* Řádky */
        .custom-card-table tr:nth-child(even) {
            background-color: #f4f1ee;
        }
        .custom-card-table tr:nth-child(odd) {
            background-color: #ffffff;
        }

        /* Dolní rohy */
        .custom-card-table tr:last-child td:first-child {
            border-bottom-left-radius: 12px;
        }
        .custom-card-table tr:last-child td:last-child {
            border-bottom-right-radius: 12px;
        }

        /* Odkazy */
        .custom-card-table a {
            color: #a26769;
            text-decoration: underline;
        }
        
        div.stButton > button:first-child {
                background-color: #5C715E;
                color: white;
                font-weight: bold;
                border-radius: 10px;
            }
                    
        </style>
        """, unsafe_allow_html=True)

        # Vykreslení tabulky v divu se scrollbarem
        st.markdown(
            f'<div class="table-scroll-wrapper">{spojene.to_html(escape=False, index=False, classes="custom-card-table")}</div>',
            unsafe_allow_html=True
        )

        st.caption("Poznámka: Množství každé suroviny je přepočteno na váhu (kg) či objem (l) pro výpočet potřebného množství balení produktů a přesnější výpočet ceny.")

        # Optimalizace
        if optimalizace:
            st.session_state.vybrane_recepty = vybrane_recepty
            st.session_state.pocet_porci = pocet_porci
            st.session_state.nepotrebuju = nepotrebuju

            st.header("Optimalizace nákupu")

            st.markdown("Porovnáme, zda je výhodnější nakoupit **vše v jednom e-shopu**, nebo **nákup rozdělit**.")
            st.markdown("Pro každou surovinu najdeme vždy **levnější variantu** produktu mezi e-shopy a sestavíme **dva rozdělené nákupy**. Nákup rozdělíme jen tehdy, pokud i při zohlednění **ceny dopravy** na obou e-shopech vyjde levněji než jeden společný nákup. Je třeba uvažovat i hodnotu **minimální objednávky**. Při výběru zobrazení _Cena za recept_ optimalizujeme přes **cenu za jednotku** u každého z produktů.")

            real_rohlik_total = 0  # skrytá suma za balení
            real_kosik_total = 0

            if vybrane_recepty:
                dostupne_ingredience = df_recepty[df_recepty["recept_nazev"].isin(vybrane_recepty)]["ingredience_nazev"].unique().tolist()
                
                df_filtered = df_recepty[df_recepty["recept_nazev"].isin(vybrane_recepty) & ~df_recepty["ingredience_nazev"].isin(nepotrebuju)].copy()
                df_filtered["mnozstvi_final"] = (df_filtered["mnozstvi_prepoctene"] / df_filtered["pocet_porci"]) * pocet_porci
                df_agg = df_filtered.groupby(["ingredience_nazev", "unit_katalog"], as_index=False)["mnozstvi_final"].sum()

                total_rohlik = 0
                total_kosik = 0
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
                    best_label = ""
                    best_price_pack = float("inf")
                    best_price_shown = float("inf")

                    for _, r in kosik_opt.iterrows():
                        converted = convert_units(mnozstvi, unit, r["Jednotka balení"])
                        if converted is not None and r["Velikost balení"] > 0:
                            kusu = math.ceil(converted / r["Velikost balení"])
                            cena_pack = r["Cena"] * kusu
                            cena_jedn = r["Jednotková cena"] * mnozstvi

                            cena_porovnani = cena_jedn if zobrazeni == "Cena za recept" else cena_pack

                            if cena_porovnani < best_price:
                                best_price = cena_porovnani
                                best_price_shown = cena_jedn if zobrazeni == "Cena za recept" else cena_pack
                                best_price_pack = cena_pack
                                best_source = "Košík"
                                best_label = f'<a href="{r["URL"]}" target="_blank">{r["Produkt"]}</a> ({kusu}×)'

                    for _, r in rohlik_opt.iterrows():
                        converted = convert_units(mnozstvi, unit, r["Jednotka balení"])
                        if converted is not None and r["Velikost balení"] > 0:
                            kusu = math.ceil(converted / r["Velikost balení"])
                            cena_pack = r["Cena"] * kusu
                            cena_jedn = r["Jednotková cena"] * mnozstvi

                            cena_porovnani = cena_jedn if zobrazeni == "Cena za recept" else cena_pack

                            if cena_porovnani < best_price:
                                best_price = cena_porovnani
                                best_price_shown = cena_jedn if zobrazeni == "Cena za recept" else cena_pack
                                best_price_pack = cena_pack
                                best_source = "Rohlík"
                                best_label = f'<a href="{r["URL"]}" target="_blank">{r["Produkt"]}</a> ({kusu}×)'

                    if best_source == "Košík":
                        total_kosik += best_price_shown
                        real_kosik_total += best_price_pack
                        kosik_items.append((ingred, round(best_price_shown, 2), best_label))
                    elif best_source == "Rohlík":
                        total_rohlik += best_price_shown
                        real_rohlik_total += best_price_pack
                        rohlik_items.append((ingred, round(best_price_shown, 2), best_label))

                
                # Výpočet dopravy pro rozdělený nákup
                doprava_rohlik = 0 if rohlik_xtra else next(v for k, v in ROHLIK_SHIPPING if real_rohlik_total >= k)
                doprava_kosik = 0 if kosik_novy else next(v for k, v in KOSIK_SHIPPING if real_kosik_total >= k)

                # Výpočet dopravy pro nerozdělené nákupy
                doprava_rohlik_cely = 0 if rohlik_xtra else next(v for k, v in ROHLIK_SHIPPING if rohlik_total >= k)
                doprava_kosik_cely = 0 if kosik_novy else next(v for k, v in KOSIK_SHIPPING if kosik_total >= k)
                
                total_rozdeleny = total_kosik + doprava_kosik + total_rohlik + doprava_rohlik
                kosik_cely = kosik_total + doprava_kosik_cely
                rohlik_cely = rohlik_total + doprava_rohlik_cely

                # Varování o minimální hodnotě objednávky
                if total_rozdeleny < kosik_cely and total_rozdeleny < rohlik_cely:
                    if real_kosik_total < MIN_ORDER:
                        st.warning(f"Košík: hodnota nákupu je pod minimem {MIN_ORDER} Kč — nelze objednat samostatně.")
                    if real_rohlik_total < MIN_ORDER and not rohlik_xtra:
                        st.warning(f"Rohlík: hodnota nákupu je pod minimem {MIN_ORDER} Kč — nelze objednat samostatně.")

                    st.subheader(":material/shopping_bag: Rozdělený nákup")

                    # Rozdělené nákupy - součty
                    st.markdown(f"**Košík:** {total_kosik:.2f} Kč + doprava {doprava_kosik:.0f} Kč = {total_kosik + doprava_kosik:.2f} Kč")
                    st.markdown(f"**Rohlík:** {total_rohlik:.2f} Kč + doprava {doprava_rohlik:.0f} Kč = {total_rohlik + doprava_rohlik:.2f} Kč")
                    
                    # Součet rozděleného nákupu a úspora oproti nerozdělení
                    if zobrazeni == "Cena za balení":
                        st.markdown("**Celková cena rozděleného nákupu:**")
                    else:
                        st.markdown("**Celková cena za recept při rozděleném nákupu:**")

                    col1, col2 = st.columns(2)

                    with col1:
                        st.success(f"{total_rozdeleny:.2f} Kč")
                    
                    with col2:
                        st.markdown(f"Úspora oproti nákupu pouze na **Košíku**: :green-badge[{kosik_cely - total_rozdeleny:.2f} Kč]") 
                        st.markdown(f"Úspora oproti nákupu pouze na **Rohlíku**: :green-badge[{rohlik_cely - total_rozdeleny:.2f} Kč]")
                                
                    # Detaily rozdělených nákupních seznamů
                    st.markdown("**Detaily nákupu v jednotlivých e-shopech:**") 

                    # Zobrazení v záložkách
                    tab1, tab2 = st.tabs(["Košík", "Rohlík"]) 
                    with tab1:
                        df_k = pd.DataFrame(kosik_items, columns=["Ingredience", "Cena", "Produkt"])
                        # Tabulka
                        st.markdown(
                            f'<div class="table-scroll-wrapper">{df_k.to_html(escape=False, index=False, classes="custom-card-table")}</div>',
                            unsafe_allow_html=True
                        )

                    with tab2:
                        df_r = pd.DataFrame(rohlik_items, columns=["Ingredience", "Cena", "Produkt"])
                        # Tabulka
                        st.markdown(
                            f'<div class="table-scroll-wrapper">{df_r.to_html(escape=False, index=False, classes="custom-card-table")}</div>',
                            unsafe_allow_html=True
                        )


                # Hláška pokud se optimalizyce nevyplatí    
                elif total_rozdeleny == kosik_cely: 
                    st.info("Rozdělený nákup se nevyplatí: všechny produkty jsou levnější na **Košíku**.")
                elif total_rozdeleny == rohlik_cely:
                    st.info("Rozdělený nákup se nevyplatí: všechny produkty jsou levnější na **Rohlíku**.")
                else:
                    st.info("Rozdělený nákup se nevyplatí: cena dodatečné dopravy převyšuje úsporu na ceně za produkty.")

            else:
                st.info("Vyber alespoň jeden recept pro výpočet optimalizovaného nákupu.")
    
    else:
        st.info("Vyber suroviny, které nemáš doma, abychom ti mohli vytvořit nákupní seznam.")
else:
    st.info("Vyber alespoň jeden recept, aby se zobrazil nákupní seznam.")
