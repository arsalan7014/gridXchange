"""
Interactive Dashboard for Decentralized P2P Energy Trading Simulation

This project is made by Quantum Coders, a team from VSSUT Burla.
Team Members:
- Arsalan Ali
- Brahamananda Sahoo
- Kritika Tekriwal

Built with Streamlit for real-time visualization of energy flows, trading networks, and blockchain transactions.
"""
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx

from energy_trading_sim import EnergyTradingSimulator


def draw_trade_network(simulator):
    edges = simulator.get_trade_network()
    if not edges:
        st.info("No peer-to-peer trades available yet. Increase participants or run the simulation.")
        return

    graph = nx.DiGraph()
    for agent_id, agent in simulator.agents.items():
        graph.add_node(agent_id, label=agent.name, type=agent.agent_type)
    for edge in edges:
        graph.add_edge(edge["source"], edge["target"], weight=edge["weight"], price=edge["price"])

    pos = nx.spring_layout(graph, seed=42)
    edge_x = []
    edge_y = []
    for source, target in graph.edges():
        x0, y0 = pos[source]
        x1, y1 = pos[target]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]
    node_x = [pos[node][0] for node in graph.nodes()]
    node_y = [pos[node][1] for node in graph.nodes()]
    node_text = [f"{graph.nodes[n]['label']} ({graph.nodes[n]['type']})" for n in graph.nodes()]

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=1, color="#888"),
        hoverinfo="none",
        mode="lines",
    )
    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        marker=dict(size=24, color=["#2ca02c" if graph.nodes[n]["type"] == "prosumer" else "#1f77b4" for n in graph.nodes()]),
        text=node_text,
        textposition="top center",
        hoverinfo="text",
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        title="Peer-to-peer trading network",
        showlegend=False,
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    )
    st.plotly_chart(fig, use_container_width=True)


def main():
    st.set_page_config(page_title="Decentralized P2P Energy Trading Simulation", layout="wide")

    # Set background color to blue
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #1e3a8a;  /* Blue background */
            color: white;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.title("Decentralized P2P Energy Trading Simulation")
    st.markdown("*Made by Quantum Coders, VSSUT Burla*")
    st.markdown(
        "This interactive simulator demonstrates how a local energy community can use decentralized bidding, smart contracts, and blockchain immutability to trade renewable power in real time."
    )

    with st.sidebar:
        st.header("Simulation controls")
        num_prosumers = st.slider("Number of prosumers", min_value=1, max_value=12, value=5)
        num_consumers = st.slider("Number of consumers", min_value=1, max_value=12, value=5)
        hours = st.slider("Simulation hours", min_value=4, max_value=48, value=24)
        generation_variability = st.slider("Generation variability", min_value=0.1, max_value=5.0, value=1.8, step=0.1)
        demand_variability = st.slider("Demand variability", min_value=0.1, max_value=4.0, value=1.5, step=0.1)
        grid_price = st.slider("Grid purchase price ($/kWh)", min_value=0.05, max_value=0.5, value=0.22, step=0.01)
        smart_price_factor = st.slider("Smart contract price factor", min_value=0.80, max_value=1.20, value=1.0, step=0.01)
        run_sim = st.button("Run simulation")

    simulator = EnergyTradingSimulator(
        num_prosumers=num_prosumers,
        num_consumers=num_consumers,
        generation_variability=generation_variability,
        demand_variability=demand_variability,
        grid_price=grid_price,
        grid_supply_price=round(grid_price * 0.48, 3),
        price_volatility=smart_price_factor,
    )

    if run_sim:
        summary = simulator.run(hours=hours)

        st.subheader("Market performance summary")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total traded volume", f"{summary['traded_volume'].sum():.2f} kWh")
        col2.metric("Average price", f"${summary['price'].mean():.3f}")
        col3.metric("Average efficiency", f"{summary['efficiency'].mean():.2%}")
        col4.metric("Average grid load", f"{summary['grid_load'].mean():.2f} kWh")

        st.markdown("---")
        st.subheader("Price and trading volume")
        chart_data = summary[ ["hour", "price", "traded_volume"]].melt(id_vars=["hour"], value_vars=["price", "traded_volume"], var_name="metric", value_name="value")
        fig = px.line(chart_data, x="hour", y="value", color="metric", markers=True)
        fig.update_layout(yaxis_title="Value", xaxis_title="Hour")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Participant balances and last-hour activity")
        agent_summary = simulator.get_agent_summary()
        st.dataframe(agent_summary.sort_values(by=["wallet"], ascending=False).reset_index(drop=True))

        st.subheader("Blockchain ledger and transaction history")
        blockchain_df = simulator.get_blockchain_history()
        st.dataframe(blockchain_df)

        st.subheader("Last transactions")
        transaction_ledger = simulator.get_transaction_ledger()
        st.dataframe(transaction_ledger.sort_values(by=["block_index"], ascending=False).head(20))

        st.subheader("P2P trading network")
        draw_trade_network(simulator)

        st.subheader("Simulation diagnostics")
        diag_data = summary[ ["hour", "efficiency", "grid_load", "cost_savings"] ]
        fig2 = px.area(diag_data, x="hour", y=["efficiency", "grid_load", "cost_savings"], labels={"value":"Metric", "variable":"Metric Type"})
        st.plotly_chart(fig2, use_container_width=True)

        st.success("Simulation run complete. The blockchain is valid: {}".format(simulator.blockchain.is_valid()))
        st.markdown("_Use the sidebar to adjust community size, volatility, and pricing preferences, then rerun the simulation._")
        st.markdown("**Project by Quantum Coders, VSSUT Burla**")
    else:
        st.info("Configure the community and press Run simulation to see P2P energy trading in action.")


if __name__ == "__main__":
    main()
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx

from energy_trading_sim import EnergyTradingSimulator


def draw_trade_network(simulator):
    edges = simulator.get_trade_network()
    if not edges:
        st.info("No peer-to-peer trades available yet.")
        return

    graph = nx.DiGraph()
    for agent_id, agent in simulator.agents.items():
        graph.add_node(agent_id, label=agent.name, type=agent.agent_type)

    for edge in edges:
        graph.add_edge(edge["source"], edge["target"], weight=edge["weight"], price=edge["price"])

    pos = nx.spring_layout(graph, seed=42)

    edge_x, edge_y = [], []
    for source, target in graph.edges():
        x0, y0 = pos[source]
        x1, y1 = pos[target]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    node_x = [pos[node][0] for node in graph.nodes()]
    node_y = [pos[node][1] for node in graph.nodes()]
    node_text = [f"{graph.nodes[n]['label']} ({graph.nodes[n]['type']})" for n in graph.nodes()]

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=1, color="#888"),
        hoverinfo="none",
        mode="lines",
    )

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        marker=dict(
            size=24,
            color=[
                "#00ff9c" if graph.nodes[n]["type"] == "prosumer" else "#00c3ff"
                for n in graph.nodes()
            ],
        ),
        text=node_text,
        textposition="top center",
        hoverinfo="text",
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        title="P2P Trading Network",
        showlegend=False,
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor="#0e1117",
        paper_bgcolor="#0e1117",
        font=dict(color="white"),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    )

    st.plotly_chart(fig, use_container_width=True)


def main():
    st.set_page_config(
        page_title="P2P Energy Trading",
        layout="wide"
    )

    # 🔥 ADVANCED UI STYLING
    st.markdown(
        """
        <style>
        .stApp {
            background: linear-gradient(135deg, #141e30, #243b55);
            color: white;
        }

        .stDataFrame, .stTable {
            background-color: rgba(255,255,255,0.05);
        }

        .stMetric {
            background-color: rgba(255,255,255,0.05);
            padding: 10px;
            border-radius: 10px;
        }

        div[data-testid="stSidebar"] {
            background-color: #0e1117;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.title("⚡ Decentralized P2P Energy Trading Simulation")
    st.markdown("*Quantum Coders | VSSUT Burla*")

    with st.sidebar:
        st.header("Controls")

        num_prosumers = st.slider("Prosumers", 1, 12, 5)
        num_consumers = st.slider("Consumers", 1, 12, 5)
        hours = st.slider("Hours", 4, 48, 24)

        generation_variability = st.slider("Generation Variability", 0.1, 5.0, 1.8)
        demand_variability = st.slider("Demand Variability", 0.1, 4.0, 1.5)

        grid_price = st.slider("Grid Price ($/kWh)", 0.05, 0.5, 0.22)
        smart_price_factor = st.slider("Smart Pricing Factor", 0.8, 1.2, 1.0)

        run_sim = st.button("Run Simulation")

    simulator = EnergyTradingSimulator(
        num_prosumers=num_prosumers,
        num_consumers=num_consumers,
        generation_variability=generation_variability,
        demand_variability=demand_variability,
        grid_price=grid_price,
        grid_supply_price=round(grid_price * 0.48, 3),
        price_volatility=smart_price_factor,
    )

    if run_sim:
        summary = simulator.run(hours=hours)

        st.subheader("Market Summary")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Volume", f"{summary['traded_volume'].sum():.2f}")
        col2.metric("Avg Price", f"${summary['price'].mean():.3f}")
        col3.metric("Efficiency", f"{summary['efficiency'].mean():.2%}")
        col4.metric("Grid Load", f"{summary['grid_load'].mean():.2f}")

        st.markdown("---")

        # 📈 PRICE + VOLUME
        st.subheader("Price & Volume")

        chart_data = summary[["hour", "price", "traded_volume"]].melt(
            id_vars=["hour"], var_name="metric", value_name="value"
        )

        fig = px.line(chart_data, x="hour", y="value", color="metric", markers=True)
        fig.update_layout(
            plot_bgcolor="#0e1117",
            paper_bgcolor="#0e1117",
            font=dict(color="white"),
        )

        st.plotly_chart(fig, use_container_width=True)

        # 👥 AGENTS
        st.subheader("Agent Status")
        st.dataframe(simulator.get_agent_summary())

        # 🔗 BLOCKCHAIN
        st.subheader("Blockchain")
        st.dataframe(simulator.get_blockchain_history())

        st.subheader("Transactions")
        st.dataframe(
            simulator.get_transaction_ledger()
            .sort_values(by="block_index", ascending=False)
            .head(20)
        )

        # 🌐 NETWORK
        st.subheader("Trading Network")
        draw_trade_network(simulator)

        # 📊 DIAGNOSTICS
        st.subheader("Diagnostics")

        fig2 = px.area(
            summary,
            x="hour",
            y=["efficiency", "grid_load", "cost_savings"],
        )

        fig2.update_layout(
            plot_bgcolor="#0e1117",
            paper_bgcolor="#0e1117",
            font=dict(color="white"),
        )

        st.plotly_chart(fig2, use_container_width=True)

        st.success(f"Blockchain valid: {simulator.blockchain.is_valid()}")

    else:
        st.info("Set parameters and run simulation.")


if __name__ == "__main__":
    main()
