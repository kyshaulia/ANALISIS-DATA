from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st
from matplotlib.ticker import FuncFormatter

# ---------------------------------------------------------------- konfigurasi
st.set_page_config(page_title="Dashboard Bike Sharing", page_icon="🚲", layout="wide")

C_HIGHLIGHT, C_PRIMARY, C_NEUTRAL, C_TEXT = "#D1495B", "#00798C", "#B8BFC9", "#2B2D42"
plt.rcParams.update({
    "font.size": 10, "axes.titlesize": 12, "axes.titleweight": "bold",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.titlelocation": "left", "text.color": C_TEXT, "axes.labelcolor": C_TEXT,
    "xtick.color": C_TEXT, "ytick.color": C_TEXT,
})
thousand = FuncFormatter(lambda x, _: f"{x:,.0f}".replace(",", "."))

SEASON_ORDER = ["Dingin", "Semi", "Panas", "Gugur"]
WEATHER_ORDER = ["Cerah", "Berkabut/Berawan", "Hujan/Salju Ringan"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
DAY_ORDER = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]


# ---------------------------------------------------------------- data
@st.cache_data
def load_data():
    base = Path(__file__).parent
    day = pd.read_csv(base / "main_data.csv", parse_dates=["dteday"])
    hour = pd.read_csv(base / "hour_data.csv", parse_dates=["dteday"])
    return day, hour


day_df, hour_df = load_data()

# ---------------------------------------------------------------- sidebar
st.sidebar.header("Filter")
min_d, max_d = day_df["dteday"].min().date(), day_df["dteday"].max().date()
date_range = st.sidebar.date_input("Rentang tanggal", (min_d, max_d), min_value=min_d, max_value=max_d)
seasons = st.sidebar.multiselect("Musim", SEASON_ORDER, default=SEASON_ORDER)
st.sidebar.caption("Filter berlaku untuk seluruh grafik. Perbandingan hari kerja vs akhir pekan pada tab 1 selalu menampilkan keduanya.")

if isinstance(date_range, tuple) and len(date_range) == 2:
    start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
else:
    start, end = pd.Timestamp(min_d), pd.Timestamp(max_d)


def apply_filter(df):
    return df[(df["dteday"] >= start) & (df["dteday"] <= end) & (df["season_name"].isin(seasons))]


day_f, hour_f = apply_filter(day_df), apply_filter(hour_df)

# ---------------------------------------------------------------- header + KPI
st.title("🚲 Dashboard Bike Sharing — Capital Bikeshare, Washington D.C.")
st.caption("Data 2011–2012. Sumber: Bike Sharing Dataset (Fanaee-T & Gama, 2013).")

if day_f.empty:
    st.warning("Tidak ada data untuk filter yang dipilih. Ubah rentang tanggal atau musim.")
    st.stop()

total = int(day_f["cnt"].sum())
avg_day = day_f["cnt"].mean()
casual_share = day_f["casual"].sum() / total * 100
peak_hour = hour_f.groupby("hr")["cnt"].mean().idxmax()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total penyewaan", f"{total:,.0f}".replace(",", "."))
k2.metric("Rata-rata per hari", f"{avg_day:,.0f}".replace(",", "."))
k3.metric("Porsi pengguna kasual", f"{casual_share:.1f}%")
k4.metric("Jam puncak rata-rata", f"{peak_hour:02d}:00")

tab1, tab2, tab3, tab4 = st.tabs([
    "1. Pola Jam", "2. Cuaca & Suhu", "3. Pertumbuhan & Pengguna", "4. Segmen Waktu (Analisis Lanjutan)"
])

# ---------------------------------------------------------------- tab 1
with tab1:
    st.subheader("Pada jam berapa permintaan memuncak?")
    hourly = hour_f.groupby(["day_type", "hr"])["cnt"].mean().unstack("day_type")

    fig, ax = plt.subplots(figsize=(10, 4.6))
    for tipe, warna in [("Akhir Pekan/Libur", C_HIGHLIGHT), ("Hari Kerja", C_PRIMARY)]:
        if tipe in hourly.columns and hourly[tipe].notna().any():
            ax.plot(hourly.index, hourly[tipe], color=warna, lw=2.5, label=tipe)
            hp, vp = hourly[tipe].idxmax(), hourly[tipe].max()
            ax.scatter(hp, vp, color=warna, zorder=5)
            ax.annotate(f"{hp:02d}:00 ({vp:.0f})", (hp, vp), xytext=(0, 10), textcoords="offset points",
                        ha="center", color=warna, fontweight="bold")
    ax.set_xticks(range(0, 24, 2))
    ax.set_xlabel("Jam dalam sehari"); ax.set_ylabel("Rata-rata penyewaan per jam")
    ax.set_ylim(0, max(hourly.max().max() * 1.2, 10)); ax.yaxis.set_major_formatter(thousand)
    ax.legend(frameon=False, loc="upper left")
    ax.set_title("Hari kerja: dua puncak komuter. Akhir pekan: satu puncak landai di siang hari")
    st.pyplot(fig)

    if {"Hari Kerja", "Akhir Pekan/Libur"} <= set(hourly.columns):
        pw, pe = hourly["Hari Kerja"].max(), hourly["Akhir Pekan/Libur"].max()
        st.info(
            f"**Insight:** puncak hari kerja pukul **{hourly['Hari Kerja'].idxmax():02d}:00** ({pw:.0f} sewa/jam), "
            f"puncak akhir pekan pukul **{hourly['Akhir Pekan/Libur'].idxmax():02d}:00** ({pe:.0f} sewa/jam). "
            f"Selisih puncak {pw - pe:.0f} sepeda/jam ({(pw / pe - 1) * 100:.0f}% lebih tinggi di hari kerja). "
            "Rekomendasi: redistribusi sepeda ke permukiman sebelum 08:00 dan ke area perkantoran sebelum 17:00."
        )

# ---------------------------------------------------------------- tab 2
with tab2:
    st.subheader("Seberapa besar pengaruh cuaca dan suhu?")
    c1, c2 = st.columns(2)

    w = day_f.groupby("weather")["cnt"].agg(["mean", "count"]).reindex(WEATHER_ORDER).dropna()
    with c1:
        fig, ax = plt.subplots(figsize=(5.5, 4.4))
        base = w["mean"].iloc[0]
        colors = [C_NEUTRAL] * len(w)
        if len(w) > 1:
            colors[-1] = C_HIGHLIGHT
        bars = ax.bar(w.index, w["mean"], color=colors, width=0.6)
        for b, v, n in zip(bars, w["mean"], w["count"]):
            pct = "" if v == base else f"\n({(v / base - 1) * 100:+.0f}%)"
            ax.text(b.get_x() + b.get_width() / 2, v + base * 0.02, f"{v:,.0f}".replace(",", ".") + pct,
                    ha="center", fontweight="bold", fontsize=9)
        ax.set_ylim(0, base * 1.25); ax.yaxis.set_major_formatter(thousand)
        ax.set_ylabel("Rata-rata penyewaan harian"); ax.tick_params(axis="x", labelsize=8)
        ax.set_title("Penyewaan menurun saat cuaca memburuk")
        st.pyplot(fig)
        st.caption("Persentase dibanding hari cerah. Kategori hujan/salju lebat tidak ada pada data harian.")

    tb = pd.cut(day_f["temp_c"], bins=[0, 10, 20, 30, 45], labels=["< 10 °C", "10–20 °C", "20–30 °C", "> 30 °C"], right=False)
    t = day_f.groupby(tb, observed=True)["cnt"].agg(["mean", "count"])
    with c2:
        fig, ax = plt.subplots(figsize=(5.5, 4.4))
        best = t["mean"].values.argmax()
        colors = [C_HIGHLIGHT if i == best else C_NEUTRAL for i in range(len(t))]
        bars = ax.bar(t.index.astype(str), t["mean"], color=colors, width=0.6)
        for b, v, n in zip(bars, t["mean"], t["count"]):
            ax.text(b.get_x() + b.get_width() / 2, v + t["mean"].max() * 0.02,
                    f"{v:,.0f}".replace(",", ".") + f"\n(n={n})", ha="center", fontweight="bold", fontsize=9)
        ax.set_ylim(0, t["mean"].max() * 1.25); ax.yaxis.set_major_formatter(thousand)
        ax.set_ylabel("Rata-rata penyewaan harian"); ax.set_xlabel("Suhu aktual")
        ax.set_title("Penyewaan tertinggi pada suhu hangat")
        st.pyplot(fig)
        st.caption("n = jumlah hari pada rentang suhu tersebut.")

    st.info("**Rekomendasi:** jadwalkan servis massal saat hujan atau suhu < 10 °C, dan perkuat promosi serta ketersediaan armada pada suhu 20–30 °C.")

# ---------------------------------------------------------------- tab 3
with tab3:
    st.subheader("Bagaimana pertumbuhan dan komposisi pengguna?")
    c1, c2 = st.columns([1.5, 1])

    full = day_df[day_df["season_name"].isin(seasons)]
    m = full.groupby(["year", "mnth"])["cnt"].sum().unstack("year")
    m["yoy"] = (m[2012] / m[2011] - 1) * 100
    with c1:
        fig, ax = plt.subplots(figsize=(7.5, 4.4))
        colors = [C_HIGHLIGHT if v == m["yoy"].max() else C_PRIMARY for v in m["yoy"]]
        bars = ax.bar([MONTHS[i - 1] for i in m.index], m["yoy"], color=colors, width=0.7)
        for b, v in zip(bars, m["yoy"]):
            ax.text(b.get_x() + b.get_width() / 2, v + 3, f"{v:.0f}%", ha="center", fontsize=8, fontweight="bold")
        ax.set_ylabel("Pertumbuhan YoY (%)"); ax.set_ylim(0, m["yoy"].max() * 1.15)
        ax.set_title("Pertumbuhan penyewaan 2012 vs 2011 per bulan")
        st.pyplot(fig)
        st.caption("Pertumbuhan dihitung dari seluruh 2011 vs 2012 (hanya dipengaruhi filter musim, bukan rentang tanggal).")

    s = day_f.groupby("season_name")[["casual", "cnt"]].sum().reindex(SEASON_ORDER).dropna()
    s["share"] = s["casual"] / s["cnt"] * 100
    with c2:
        fig, ax = plt.subplots(figsize=(4.8, 4.4))
        best = s["share"].values.argmax()
        colors = [C_HIGHLIGHT if i == best else C_NEUTRAL for i in range(len(s))]
        bars = ax.bar(s.index, s["share"], color=colors, width=0.6)
        for b, v in zip(bars, s["share"]):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.4, f"{v:.1f}%", ha="center", fontweight="bold")
        ax.set_ylim(0, s["share"].max() * 1.25); ax.set_ylabel("Pengguna kasual dari total (%)")
        ax.set_title("Porsi pengguna kasual per musim")
        st.pyplot(fig)

    st.info("**Rekomendasi:** jalankan kampanye konversi pengguna kasual menjadi anggota terdaftar pada musim semi dan panas, saat porsi pengguna kasual paling tinggi.")

# ---------------------------------------------------------------- tab 4
with tab4:
    st.subheader("Peta panas permintaan per jam dan hari")
    heat = hour_f.pivot_table(index="weekday_name", columns="hr", values="cnt", aggfunc="mean").reindex(DAY_ORDER)
    fig, ax = plt.subplots(figsize=(11, 3.8))
    sns.heatmap(heat, cmap="YlGnBu", ax=ax, cbar_kws={"label": "Rata-rata sewa/jam"}, linewidths=0.3, linecolor="white")
    ax.set_xlabel("Jam dalam sehari"); ax.set_ylabel(""); ax.tick_params(axis="y", rotation=0)
    ax.set_title("Hari kerja: puncak 08:00 dan 17:00–18:00. Akhir pekan: 11:00–16:00")
    st.pyplot(fig)

    def segment(h):
        if h <= 5: return "1. Dini hari (00–05)"
        if h <= 9: return "2. Jam sibuk pagi (06–09)"
        if h <= 15: return "3. Siang (10–15)"
        if h <= 19: return "4. Jam sibuk sore (16–19)"
        return "5. Malam (20–23)"

    seg = hour_f.assign(segmen=hour_f["hr"].apply(segment))
    tbl = seg.groupby(["segmen", "day_type"])["cnt"].mean().unstack("day_type").round(0)
    st.markdown("**Rata-rata penyewaan per jam menurut segmen waktu (manual grouping)**")
    st.dataframe(tbl)
    st.caption("Segmen waktu ditentukan berdasarkan aturan domain (jam komuter pagi/sore).")

st.caption("Proyek Analisis Data — Bike Sharing Dataset")
