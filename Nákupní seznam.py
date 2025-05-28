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

def format_number(n):
    if n == int(n):
        return str(int(n))  # celé číslo, bez desetinných míst
    else:
        return f"{n:.2f}"  # číslo s dvěma desetinnými místy

# --- UI ---
# st.markdown("""
#     <style>
#         /* Tělo aplikace */
#         .stApp {
#             background-color: #f4f1ee;
#             font-family: 'Segoe UI', sans-serif;
#         }

#         /* Boxy/karty */
#         .stContainer, .stMarkdown, .stDataFrame {
#             background-color: #ffffff;
#             border-radius: 8px;
#             padding: 1rem;
#             box-shadow: 0 2px 8px rgba(0,0,0,0.05);
#         }

#         /* Tlačítka */
#         .stButton>button {
#             background-color: #5c715e;
#             color: white;
#             border: none;
#             padding: 0.6rem 1.2rem;
#             border-radius: 6px;
#             transition: background-color 0.2s ease;
#         }
#         .stButton>button:hover {
#             background-color: #3e5240;
#             cursor: pointer;
#         }

#         /* Nadpisy */
#         h1, h2, h3, h4 {
#             color: #2e2e2e;
#         }

#         /* Scrollbar */
#         ::-webkit-scrollbar {
#             width: 8px;
#         }
#         ::-webkit-scrollbar-thumb {
#             background-color: #c9d5b5;
#             border-radius: 4px;
#         }
#         ::-webkit-scrollbar-thumb:hover {
#             background-color: #aebc98;
#         }

#         /* Inputs */
#         .stTextInput>div>input,
#         .stSelectbox>div>div>div>input {
#             background-color: #ffffff;
#             border-radius: 6px;
#             padding: 0.4rem;
#         }
#     </style>
# """, unsafe_allow_html=True)

st.set_page_config(
    page_title="Co budu vařit?",
    page_icon=":material/grocery:",
    layout="wide"
)

#st.logo("data/logo.png")

st.title("Nákupní seznam podle receptů")
# col1, col2 = st.columns([0.1, 0.9])
# with col1:
#     st.image("data/logo.png")
# with col2:
#     st.title("Nákupní seznam podle receptů")

st.sidebar.header(":material/settings: Nastavení")

recepty_list = df_recepty["recept_nazev"].unique().tolist()
vybrane_recepty = st.multiselect("Vyber recepty", recepty_list)
#st.session_state.vybrane_recepty = vybrane_recepty
pocet_porci = st.sidebar.slider("Vyber počet porcí:", 1, 10, 4)
#zobrazeni = st.radio("Způsob výpočtu cen:", ["Cena za balení", "Cena za recept"])

if vybrane_recepty:
    st.subheader(":material/grocery: Suroviny dle vybraných receptů")
    with st.container(height=300, border=True):
        for recept in vybrane_recepty:
            #st.markdown(f"🍽️ **{recept}**")
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
            #st.markdown("")
    ingredience_df = get_ingredients_for_recepty(df_recepty, vybrane_recepty, pocet_porci)
    suroviny = ingredience_df["ingredience_nazev"].tolist()

    nepotrebuju = st.sidebar.multiselect("Vyber suroviny, které UŽ máš doma", suroviny)
    k_nakupu = [s for s in suroviny if s not in nepotrebuju]

    zobrazeni_help =  '''
    Cena za balení - porovnávají se **prodejní ceny** jednotlivých produktů, počet balení se vypočítá podle zvoleného počtu porcí. 
    
    Cena za recept - porovnávají se **ceny za jednotku** (např. za kg nebo l), ceny se vypočítají podle množství potřebného do receptu dle zvoleného počtu porcí.
    '''
    zobrazeni = st.sidebar.radio("Způsob výpočtu cen:", ["Cena za balení", "Cena za recept"], help=zobrazeni_help)

    st.sidebar.caption("Členství na eshopech:")
    rohlik_xtra = st.sidebar.checkbox("**Mám členství Rohlík Xtra** (doprava zdarma, 4x měsíčně bez minima)")
    kosik_novy = st.sidebar.checkbox("**Jsem nový zákazník Košíku** (doprava zdarma po 60 dní)")

    

    if k_nakupu:
        st.subheader(":material/shopping_cart: Nákupní seznam")

        produkty_rohlik = get_products(df_rohlik, k_nakupu)
        produkty_kosik = get_products(df_kosik, k_nakupu)

        mnozstvi_dict = dict(zip(zip(ingredience_df["ingredience_nazev"], ingredience_df["unit_katalog"]), ingredience_df["mnozstvi_final"]))

        kosik_rows = []
        rohlik_rows = []
        kosik_total = 0
        rohlik_total = 0

        # KOŠÍK
        #with st.container(border=True):
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
                    kosik_rows.append({
                        "Ingredience": surovina,
                        "Produkt Košík": f'<a href="{row["URL"]}" target="_blank">{row["Produkt"]}</a> ({kusu}×)',
                        #"Počet": kusu,
                        "Cena (Kč)": round(cena, 2),
                        #"IMG": f'<img src="{row["IMG"]}" class="centered" height="80">' 
                    })
                else:
                    cena = row["Jednotková cena"] * mnozstvi
                    kosik_total += cena      
                    kosik_rows.append({
                        "Ingredience": surovina,
                        "Produkt Košík": f'<a href="{row["URL"]}" target="_blank">{row["Produkt"]}</a>',
                        "Cena (Kč)": round(cena, 2),
                        #"IMG": f'<img src="{row["IMG"]}" class="centered" height="80">' 
                    })
            #st.markdown(f"**Celkem za {'celý nákup' if zobrazeni == 'Cena za balení' else 'množství dle receptu'}: {kosik_total:.2f} Kč**")
    # if zobrazeni == 'Cena za balení':
    #     st.session_state.kosik_total = kosik_total
    #     kosik_total_baleni = kosik_total

        # ROHLÍK
        #with st.container(border=True):
        for surovina in k_nakupu:
            unit_key = ingredience_df[ingredience_df["ingredience_nazev"] == surovina]["unit_katalog"].values[0]
            mnozstvi = mnozstvi_dict.get((surovina, unit_key), 0)
            items = df_rohlik[df_rohlik["Ingredience"] == surovina]
            for _, row in items.iterrows():
                if zobrazeni == "Cena za balení":
                    baleni = row["Velikost balení"]
                    jednotka = row["Jednotka balení"]
                    obrazek = f'<img src="{row["IMG"]}" width="50">' 
                    mnozstvi_prep = convert_units(mnozstvi, unit_key, jednotka)
                    if mnozstvi_prep is None:
                        continue
                    kusu = math.ceil(mnozstvi_prep / baleni) if baleni > 0 else 0
                    cena = row["Cena"] * kusu
                    rohlik_total += cena 
                    rohlik_rows.append({
                        "Ingredience": surovina,
                        "Produkt Rohlík": f'<a href="{row["URL"]}" target="_blank">{row["Produkt"]}</a> ({kusu}×)',
                        #"Počet": kusu,
                        "Cena (Kč) ": round(cena, 2),
                        "IMG": f'<img src="{row["IMG"]}" class="centered" height="50">' 
                    })
                else:
                    cena = row["Jednotková cena"] * mnozstvi
                    rohlik_total += cena
                    rohlik_rows.append({
                        "Ingredience": surovina,
                        "Produkt Rohlík": f'<a href="{row["URL"]}" target="_blank">{row["Produkt"]}</a>',
                        "Cena (Kč) ": round(cena, 2),
                        "IMG": f'<img src="{row["IMG"]}" class="centered" height="50">' 
                    })
            #st.markdown(f"**Celkem za {'celý nákup' if zobrazeni == 'Cena za balení' else 'množství dle receptu'}: {rohlik_total:.2f} Kč**")
            if zobrazeni == 'Cena za balení':
                st.session_state.rohlik_total = rohlik_total
                rohlik_total_baleni = rohlik_total        
                
                
        df_kosik_rows = pd.DataFrame(kosik_rows)
        df_rohlik_rows = pd.DataFrame(rohlik_rows)

        spojene = pd.merge(df_kosik_rows, df_rohlik_rows, on="Ingredience", how="outer")

        #with st.container( border=True):
                #df_spojene = pd.DataFrame(spojene)

        st.markdown(f"**Celkem za {'celý nákup' if zobrazeni == 'Cena za balení' else 'množství dle receptu'}:**")

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
            
        st.markdown('<style>th { text-align: left !important; }</style>', unsafe_allow_html=True)
        st.markdown('<style>table { width: 100% !important; } th { text-align: left !important; }</style>', unsafe_allow_html=True)
        st.markdown(spojene.to_html(escape=False, index=False), unsafe_allow_html=True)


        if st.button("Chci optimalizovat nákup"):
            st.session_state.vybrane_recepty = vybrane_recepty
            st.session_state.pocet_porci = pocet_porci
            st.session_state.nepotrebuju = nepotrebuju
            #st.switch_page("pages/Optimalizace nákupu.py")

            st.subheader(":material/shopping_bag: Optimalizace nákupu")

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

                # Doprava se řídí podle reálné ceny (za balení)
                if real_kosik_total < MIN_ORDER:
                    st.warning(f"Košík: hodnota nákupu {real_kosik_total:.2f} Kč je pod minimem {MIN_ORDER} Kč — nelze objednat samostatně.")
                if real_rohlik_total < MIN_ORDER and not rohlik_xtra:
                    st.warning(f"Rohlík: hodnota nákupu {real_rohlik_total:.2f} Kč je pod minimem {MIN_ORDER} Kč — nelze objednat samostatně.")

                if real_kosik_total >= MIN_ORDER and (real_rohlik_total >= MIN_ORDER or rohlik_xtra):
                    doprava_rohlik = 0 if rohlik_xtra else next(v for k, v in ROHLIK_SHIPPING if real_rohlik_total >= k)
                    doprava_kosik = 0 if kosik_novy else next(v for k, v in KOSIK_SHIPPING if real_kosik_total >= k)

                    st.subheader("Rozdělený nákup")

                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Košík:** {total_kosik:.2f} Kč + doprava {doprava_kosik:.0f} Kč = {total_kosik + doprava_kosik:.2f} Kč")
                        with st.expander("Detaily nákupu v Košíku"):
                            df_k = pd.DataFrame(kosik_items, columns=["Ingredience", "Cena", "Produkt"])
                            st.markdown('<style>th { text-align: left !important; }</style>', unsafe_allow_html=True)
                            st.markdown('<style>table { width: 100% !important; } th { text-align: left !important; }</style>', unsafe_allow_html=True)
                            st.markdown(df_k.to_html(escape=False, index=False), unsafe_allow_html=True)

                    with col2:    
                        st.markdown(f"**Rohlík:** {total_rohlik:.2f} Kč + doprava {doprava_rohlik:.0f} Kč = {total_rohlik + doprava_rohlik:.2f} Kč")
                        with st.expander("Detaily nákupu v Rohlíku"):
                            df_r = pd.DataFrame(rohlik_items, columns=["Ingredience", "Cena", "Produkt"])
                            st.markdown('<style>th { text-align: left !important; }</style>', unsafe_allow_html=True)
                            st.markdown('<style>table { width: 100% !important; } th { text-align: left !important; }</style>', unsafe_allow_html=True)
                            st.markdown(df_r.to_html(escape=False, index=False), unsafe_allow_html=True)

                    total_rozdeleny = total_kosik + doprava_kosik + total_rohlik + doprava_rohlik
                    if zobrazeni == "Cena za balení":
                        st.markdown("**Celková cena rozděleného nákupu:**")
                    else:
                        st.markdown("**Celková cena za recept při rozděleném nákupu:**")
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
