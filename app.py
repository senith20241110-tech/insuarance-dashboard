import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


st.set_page_config(
    page_title="Insurance Website Analytics Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

#data loading
import os

@st.cache_data
def load_data():
    file_path = os.path.join(os.path.dirname(__file__), "insurance_data_aggregated.csv")

    df = pd.read_csv(file_path)

    df.columns = [c.strip() for c in df.columns]

    df = df.rename(columns={
        "TotalNumberOfInsurancePoliciesPurchaed": "Policies",
        "TotalNumberOfInsuranceQuotes": "Quotes",
        "Pages / Session": "PagesPerSession",
        "Avg. Session Duration": "AvgSessionDuration",
    })

    return df

df = load_data()

#sidebar
st.sidebar.title("Filters")
st.sidebar.markdown("Use the controls below to explore the data.")

all_channels = sorted(df["Marketing Channel"].unique().tolist())
all_devices = sorted(df["Device Category"].unique().tolist())

selected_channels = st.sidebar.multiselect(
    "Marketing Channel",
    options=all_channels,
    default=all_channels,
)

selected_devices = st.sidebar.multiselect(
    "Device Category",
    options=all_devices,
    default=all_devices,
)

min_users, max_users = int(df["Users"].min()), int(df["Users"].max())
users_range = st.sidebar.slider(
    "Users per record (filter noisy rows)",
    min_value=min_users,
    max_value=max_users,
    value=(min_users, max_users),
)

st.sidebar.markdown("---")
metric_choice = st.sidebar.radio(
    "Primary metric for channel comparisons",
    options=["Users", "Revenue", "Quotes", "Policies"],
    index=0,
)

st.sidebar.markdown("---")
st.sidebar.caption(
    "Dashboard built for 5DATA004C Data Science Project Lifecycle. "
    "Data-aggregated insurance website analytics."
)

#filters
filtered = df[
    df["Marketing Channel"].isin(selected_channels)
    & df["Device Category"].isin(selected_devices)
    & df["Users"].between(users_range[0], users_range[1])
].copy()

#header
st.title("Insurance Website Analytics Dashboard")
st.markdown(
    "Explore how visitors from different **marketing channels** and **devices** "
    "behave on the insurance company's website from browsing to quotes to purchases."
)

if filtered.empty:
    st.warning("No data matches the current filter selection.")
    st.stop()

#kpi's
total_users = int(filtered["Users"].sum())
total_quotes = int(filtered["Quotes"].sum())
total_policies = int(filtered["Policies"].sum())
total_revenue = float(filtered["Revenue"].sum())
conv_rate = (total_policies / total_users * 100) if total_users else 0
quote_to_policy = (total_policies / total_quotes * 100) if total_quotes else 0
revenue_per_user = (total_revenue / total_users) if total_users else 0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Users", f"{total_users:,}")
k2.metric("Total Quotes", f"{total_quotes:,}")
k3.metric("Policies Purchased", f"{total_policies:,}")
k4.metric("Total Revenue", f"£{total_revenue:,.2f}")
k5.metric("Revenue / User", f"£{revenue_per_user:,.2f}")

st.caption(
    f"Overall conversion (Users → Policies): **{conv_rate:.2f}%**  |  "
    f"Quote → Policy rate: **{quote_to_policy:.2f}%**"
)

st.markdown("---")
#row1
col1, col2 = st.columns(2)

with col1:
    st.subheader(f"{metric_choice} by Marketing Channel & Device")
    channel_device = (
        filtered.groupby(["Marketing Channel", "Device Category"])[metric_choice]
        .sum()
        .reset_index()
    )
    fig1 = px.bar(
        channel_device,
        x="Marketing Channel",
        y=metric_choice,
        color="Device Category",
        barmode="stack",
        text_auto=".2s",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig1.update_layout(xaxis_tickangle=-30, legend_title="Device")
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("Device Mix (share of Users)")
    device_share = filtered.groupby("Device Category")["Users"].sum().reset_index()
    fig2 = px.pie(
        device_share,
        names="Device Category",
        values="Users",
        hole=0.45,
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig2.update_traces(textinfo="percent+label")
    st.plotly_chart(fig2, use_container_width=True)

#row2
col3, col4 = st.columns(2)

with col3:
    st.subheader("Conversion Funnel: Users → Quotes → Policies")
    funnel_vals = [total_users, total_quotes, total_policies]
    fig3 = go.Figure(
        go.Funnel(
            y=["Users", "Quotes Obtained", "Policies Purchased"],
            x=funnel_vals,
            textinfo="value+percent initial",
            marker={"color": ["#E71453", "#2EEA34", "#1B42C1"]},
        )
    )
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.subheader("Conversion Rate (%) by Channel")
    conv_by_channel = (
        filtered.groupby("Marketing Channel")
        .apply(lambda g: pd.Series({
            "Users": g["Users"].sum(),
            "Policies": g["Policies"].sum(),
        }))
        .reset_index()
    )
    conv_by_channel["ConversionRate"] = (
        conv_by_channel["Policies"] / conv_by_channel["Users"] * 100
    ).round(2)
    conv_by_channel = conv_by_channel.sort_values("ConversionRate", ascending=False)
    fig4 = px.bar(
        conv_by_channel,
        x="Marketing Channel",
        y="ConversionRate",
        color="ConversionRate",
        color_continuous_scale="Teal",
        text="ConversionRate",
    )
    fig4.update_traces(texttemplate="%{text}%", textposition="outside")
    fig4.update_layout(xaxis_tickangle=-30, yaxis_title="Conversion Rate (%)")
    st.plotly_chart(fig4, use_container_width=True)

#row3
st.subheader("Engagement vs. Revenue: Pages/Session, Session Duration & Revenue")
fig5 = px.scatter(
    filtered,
    x="PagesPerSession",
    y="AvgSessionDuration",
    size="Revenue",
    color="Marketing Channel",
    hover_data=["Device Category", "Users", "Quotes", "Policies"],
    size_max=45,
    labels={
        "PagesPerSession": "Pages per Session",
        "AvgSessionDuration": "Avg. Session Duration (s)",
    },
)
st.plotly_chart(fig5, use_container_width=True)
st.caption(
    "Bubble size = Revenue. This chart highlights which channels combine strong "
    "engagement (pages/session, session duration) with high revenue value."
)

#row4
st.subheader("Revenue Heatmap: Channel × Device")
heat_data = (
    filtered.groupby(["Marketing Channel", "Device Category"])["Revenue"]
    .sum()
    .reset_index()
    .pivot(index="Marketing Channel", columns="Device Category", values="Revenue")
    .fillna(0)
)
fig6 = px.imshow(
    heat_data,
    text_auto=".0f",
    color_continuous_scale="Blues",
    aspect="auto",
    labels=dict(color="Revenue (£)"),
)
st.plotly_chart(fig6, use_container_width=True)

#raw data 
with st.expander("View filtered raw data"):
    st.dataframe(filtered, use_container_width=True)
    csv = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download filtered data as CSV",
        data=csv,
        file_name="filtered_insurance_data.csv",
        mime="text/csv",
    )

#insights
st.markdown("---")
st.subheader("💡 Key Insights")
st.markdown(
    """
- **Aggregators** drive disproportionately high revenue and conversion relative to their traffic volume,
  suggesting users referred via aggregator sites arrive with strong purchase intent.
- **Organic Search** and **Paid Search** bring in the largest volumes of users, but Paid Search converts
  users to quotes far more effectively — reflecting the value of targeted keyword intent.
- **Mobile** is the dominant device across almost every channel, reinforcing the need for a mobile-first
  website experience.
- Channels such as **Social** and **Display** generate traffic but negligible revenue, indicating they may
  serve an awareness/branding role rather than direct conversion.
"""
)
