

import pandas as pd
import streamlit as st


st.set_page_config(page_title="NFT Rarity & Fraud Scorer", page_icon="🔎", layout="wide")


# sample data
def load_sample_data():
    """Returns a DataFrame mimicking the output of your real pipeline."""
    rows = [
       
        ("#7495", "Laser eyes · Gold fur · Crown", 99.4, "Clean", 420),
        ("#3749", "Solid gold · Cyborg", 97.1, "Clean", 311),
        ("#9178", "Rainbow fur · 3D glasses", 94.3, "Med", 188),
        ("#2222", "Zombie · BAYC shirt", 88.2, "Clean", 142),
        ("#0141", "Trippy fur · Cross earring", 91.7, "Clean", 96),
        ("#4821", "Trippy fur · Cross earring", 76.2, "High", 94),
        ("#0992", "Cheetah · Earring · Hat", 61.4, "High", 280),
        ("#6103", "Bored · Sailor hat", 54.8, "Med", 41),
        ("#1450", "Halftone · Beanie", 47.3, "Med", 33),
        ("#7731", "Bored · Striped tee", 38.9, "Low", 22),
    ]
    return pd.DataFrame(
        rows, columns=["token", "traits", "rarity", "fraud_risk", "last_sale_eth"]
    )


def analyze_collection(contract_address: str) -> pd.DataFrame:
    """
    Orchestrates the full analysis for a collection.
    For the live version this calls your real modules.
    """

    return load_sample_data()


# ui

RISK_COLORS = {"Clean": "🟢", "Low": "🟢", "Med": "🟡", "High": "🔴"}


def risk_badge(risk: str) -> str:
    return f"{RISK_COLORS.get(risk, '⚪')} {risk}"


st.title("🔎 NFT Rarity & Fraud Scorer")
st.caption("Enter a collection contract address to rank rarity and flag wash trading.")

col_input, col_btn = st.columns([5, 1])
with col_input:
    contract = st.text_input(
        "Contract address",
        value="0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D",
        label_visibility="collapsed",
    )
with col_btn:
    run = st.button("Analyze", use_container_width=True, type="primary")


if run or "data" not in st.session_state:
    with st.spinner("Fetching on-chain data and scoring..."):
        st.session_state["data"] = analyze_collection(contract)

df = st.session_state["data"]



# metric cards

m1, m2, m3, m4 = st.columns(4)
flagged = df[df["fraud_risk"].isin(["High", "Med"])]
rarest = df.loc[df["rarity"].idxmax()]

m1.metric("Collection size", "10,000", help="Total tokens in the collection")
m2.metric("Flagged tokens", len(flagged), delta=f"{len(flagged)/len(df)*100:.1f}%",
          delta_color="inverse")
m3.metric("Rarest token", rarest["token"], delta=f"score {rarest['rarity']}")
m4.metric("Floor price", "14.2 ETH", delta="~$47,800")

st.divider()


#rarity leaderboard + fraud flags
left, right = st.columns(2)

with left:
    st.subheader("⭐ Top rarest tokens")
    top5 = df.sort_values("rarity", ascending=False).head(5)
    for _, row in top5.iterrows():
        st.markdown(f"**{row['token']}** — {row['traits']}")
        st.progress(row["rarity"] / 100, text=f"Rarity {row['rarity']}")

with right:
    st.subheader("⚠️ Fraud flags")
    flags = df[df["fraud_risk"].isin(["High", "Med"])].sort_values(
        "fraud_risk", ascending=False
    )
    for _, row in flags.iterrows():
        msg = f"**{row['token']}** — {row['traits']}"
        if row["fraud_risk"] == "High":
            st.error(f"{msg}  \nHigh risk: same-wallet trades / price spike")
        else:
            st.warning(f"{msg}  \nMedium risk: timing anomaly")

st.divider()


# distribution chart 
st.subheader("📊 Rarity score distribution")

bins = list(range(0, 101, 10))
labels = [f"{b}-{b+10}" for b in bins[:-1]]
df["bucket"] = pd.cut(df["rarity"], bins=bins, labels=labels, include_lowest=True)
dist = df["bucket"].value_counts().reindex(labels, fill_value=0)
st.bar_chart(dist)

st.divider()


#main table
st.subheader("All tokens")

fcol1, fcol2 = st.columns([2, 3])
with fcol1:
    view = st.radio(
        "Filter",
        ["All", "Flagged only", "Top 100 rare", "Common"],
        horizontal=True,
        label_visibility="collapsed",
    )
with fcol2:
    search = st.text_input("Search token #", placeholder="Search token #...",
                           label_visibility="collapsed")

table = df.copy()
if view == "Flagged only":
    table = table[table["fraud_risk"].isin(["High", "Med"])]
elif view == "Top 100 rare":
    table = table.sort_values("rarity", ascending=False).head(100)
elif view == "Common":
    table = table[table["rarity"] < 50]
if search:
    table = table[table["token"].str.contains(search, case=False)]

table = table.sort_values("rarity", ascending=False).reset_index(drop=True)
table.insert(0, "rank", range(1, len(table) + 1))

st.dataframe(
    table[["rank", "token", "traits", "rarity", "fraud_risk", "last_sale_eth"]],
    use_container_width=True,
    hide_index=True,
    column_config={
        "rank": st.column_config.NumberColumn("Rank", width="small"),
        "token": "Token",
        "traits": "Key traits",
        "rarity": st.column_config.ProgressColumn(
            "Rarity", min_value=0, max_value=100, format="%.1f"
        ),
        "fraud_risk": "Fraud risk",
        "last_sale_eth": st.column_config.NumberColumn("Last sale", format="%d ETH"),
    },
)


#export
st.download_button(
    "⬇️ Export CSV",
    data=table.to_csv(index=False).encode("utf-8"),
    file_name="nft_scores.csv",
    mime="text/csv",
)