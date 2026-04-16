"""
Decentralized P2P Energy Trading Simulation

This project is made by Quantum Coders, a team from VSSUT Burla.
Team Members:
- Arsalan Ali
- Brahamananda Sahoo
- Kritika Tekriwal

A comprehensive simulation of decentralized peer-to-peer energy trading with blockchain integration.
"""

import hashlib
import json
import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


@dataclass
class Agent:
    id: int
    name: str
    agent_type: str  # 'prosumer' or 'consumer'
    wallet: float
    price_preference: float
    generation_capacity: float
    demand_base: float
    generation_variability: float
    demand_variability: float
    balance_history: List[float] = field(default_factory=list)
    generation_history: List[float] = field(default_factory=list)
    demand_history: List[float] = field(default_factory=list)
    trade_history: List[Dict] = field(default_factory=list)

    def step(self, hour: int) -> Tuple[float, float, float]:
        generation = 0.0
        demand = max(0.0, self.demand_base + np.random.normal(0, self.demand_variability))
        if self.agent_type == "prosumer":
            solar_factor = max(0.0, np.sin((hour % 24) / 24 * np.pi) + 0.1)
            generation = max(0.0, self.generation_capacity * solar_factor + np.random.normal(0, self.generation_variability))
        net = generation - demand
        self.generation_history.append(generation)
        self.demand_history.append(demand)
        self.balance_history.append(self.wallet)
        return generation, demand, net

    def propose_order(self, net_energy: float, grid_price: float) -> Optional[Dict]:
        if net_energy > 0.05:
            ask_price = max(0.01, min(self.price_preference, grid_price * 0.95))
            return {
                "agent_id": self.id,
                "agent_name": self.name,
                "order_type": "ask",
                "quantity": net_energy,
                "price": ask_price,
            }
        elif net_energy < -0.05:
            bid_price = max(0.01, min(self.price_preference, grid_price * 1.05))
            return {
                "agent_id": self.id,
                "agent_name": self.name,
                "order_type": "bid",
                "quantity": abs(net_energy),
                "price": bid_price,
            }
        return None

    def record_trade(self, trade: Dict):
        self.trade_history.append(trade)


@dataclass
class Transaction:
    buyer_id: int
    seller_id: int
    quantity: float
    price: float
    timestamp: float
    energy_type: str = "renewable"

    def to_dict(self) -> Dict:
        return {
            "buyer_id": self.buyer_id,
            "seller_id": self.seller_id,
            "quantity": round(self.quantity, 4),
            "price": round(self.price, 4),
            "total": round(self.price * self.quantity, 4),
            "timestamp": self.timestamp,
            "energy_type": self.energy_type,
        }


@dataclass
class Block:
    index: int
    timestamp: float
    transactions: List[Dict]
    previous_hash: str
    nonce: int = 0
    hash: Optional[str] = None

    def compute_hash(self) -> str:
        block_string = json.dumps(
            {
                "index": self.index,
                "timestamp": self.timestamp,
                "transactions": self.transactions,
                "previous_hash": self.previous_hash,
                "nonce": self.nonce,
            },
            sort_keys=True,
        )
        return hashlib.sha256(block_string.encode()).hexdigest()

    def seal(self) -> None:
        self.hash = self.compute_hash()


class Blockchain:
    def __init__(self):
        self.chain: List[Block] = []
        self.pending_transactions: List[Dict] = []
        self.create_genesis_block()

    def create_genesis_block(self) -> None:
        genesis_block = Block(index=0, timestamp=time.time(), transactions=[], previous_hash="0")
        genesis_block.seal()
        self.chain.append(genesis_block)

    def add_transaction(self, transaction: Transaction) -> None:
        self.pending_transactions.append(transaction.to_dict())

    def mine_block(self) -> Block:
        assert self.chain[-1].hash is not None
        block = Block(
            index=len(self.chain),
            timestamp=time.time(),
            transactions=self.pending_transactions.copy(),
            previous_hash=self.chain[-1].hash,
        )
        block.seal()
        self.chain.append(block)
        self.pending_transactions.clear()
        return block

    def is_valid(self) -> bool:
        for idx in range(1, len(self.chain)):
            current = self.chain[idx]
            previous = self.chain[idx - 1]
            if current.previous_hash != previous.hash:
                return False
            if current.compute_hash() != current.hash:
                return False
        return True


class EnergyMarket:
    def __init__(self, grid_price: float, grid_supply_price: float):
        self.grid_price = grid_price
        self.grid_supply_price = grid_supply_price
        self.bid_book: List[Dict] = []
        self.ask_book: List[Dict] = []
        self.last_price: float = grid_price

    def reset_books(self) -> None:
        self.bid_book = []
        self.ask_book = []

    def add_order(self, order: Dict) -> None:
        if order["order_type"] == "bid":
            self.bid_book.append(order)
        else:
            self.ask_book.append(order)

    def match_orders(self) -> Tuple[List[Transaction], float, float]:
        self.bid_book.sort(key=lambda x: x["price"], reverse=True)
        self.ask_book.sort(key=lambda x: x["price"])
        transactions: List[Transaction] = []
        bid_idx = 0
        ask_idx = 0
        clearing_prices: List[float] = []

        while bid_idx < len(self.bid_book) and ask_idx < len(self.ask_book):
            bid = self.bid_book[bid_idx]
            ask = self.ask_book[ask_idx]
            if bid["price"] >= ask["price"]:
                quantity = min(bid["quantity"], ask["quantity"])
                price = (bid["price"] + ask["price"]) / 2
                clearing_prices.append(price)
                transactions.append(
                    Transaction(
                        buyer_id=bid["agent_id"],
                        seller_id=ask["agent_id"],
                        quantity=quantity,
                        price=price,
                        timestamp=time.time(),
                    )
                )
                bid["quantity"] -= quantity
                ask["quantity"] -= quantity
                if bid["quantity"] <= 0:
                    bid_idx += 1
                if ask["quantity"] <= 0:
                    ask_idx += 1
            else:
                break

        if clearing_prices:
            self.last_price = float(np.mean(clearing_prices))
        else:
            self.last_price = self.grid_price

        traded_volume = sum(t.quantity for t in transactions)
        return transactions, self.last_price, traded_volume

    def settle_with_grid(self, orders: List[Dict]) -> List[Transaction]:
        transactions: List[Transaction] = []
        for order in orders:
            if order["order_type"] == "bid":
                transactions.append(
                    Transaction(
                        buyer_id=order["agent_id"],
                        seller_id=-1,
                        quantity=order["quantity"],
                        price=self.grid_price,
                        timestamp=time.time(),
                        energy_type="grid",
                    )
                )
            else:
                transactions.append(
                    Transaction(
                        buyer_id=-1,
                        seller_id=order["agent_id"],
                        quantity=order["quantity"],
                        price=self.grid_supply_price,
                        timestamp=time.time(),
                        energy_type="grid",
                    )
                )
        return transactions


class EnergyTradingSimulator:
    def __init__(
        self,
        num_prosumers: int = 6,
        num_consumers: int = 6,
        generation_capacity: float = 8.0,
        demand_base: float = 5.0,
        generation_variability: float = 2.0,
        demand_variability: float = 1.5,
        grid_price: float = 0.20,
        grid_supply_price: float = 0.10,
        price_volatility: float = 0.05,
    ):
        self.grid_price = grid_price
        self.grid_supply_price = grid_supply_price
        self.price_volatility = price_volatility
        self.agents: Dict[int, Agent] = {}
        self.market = EnergyMarket(grid_price=grid_price, grid_supply_price=grid_supply_price)
        self.blockchain = Blockchain()
        self.history: List[Dict] = []
        self.metrics: List[Dict] = []
        self._create_agents(
            num_prosumers,
            num_consumers,
            generation_capacity,
            demand_base,
            generation_variability,
            demand_variability,
        )

    def _create_agents(
        self,
        num_prosumers: int,
        num_consumers: int,
        generation_capacity: float,
        demand_base: float,
        generation_variability: float,
        demand_variability: float,
    ) -> None:
        agent_id = 0
        for i in range(num_prosumers):
            self.agents[agent_id] = Agent(
                id=agent_id,
                name=f"Prosumer-{i+1}",
                agent_type="prosumer",
                wallet=round(random.uniform(80, 140), 2),
                price_preference=round(random.uniform(0.12, 0.25), 3),
                generation_capacity=generation_capacity,
                demand_base=max(1.5, demand_base * random.uniform(0.6, 1.2)),
                generation_variability=generation_variability,
                demand_variability=demand_variability,
            )
            agent_id += 1
        for i in range(num_consumers):
            self.agents[agent_id] = Agent(
                id=agent_id,
                name=f"Consumer-{i+1}",
                agent_type="consumer",
                wallet=round(random.uniform(60, 120), 2),
                price_preference=round(random.uniform(0.18, 0.32), 3),
                generation_capacity=0.0,
                demand_base=demand_base * random.uniform(0.8, 1.4),
                generation_variability=0.0,
                demand_variability=demand_variability,
            )
            agent_id += 1

    def reset(self) -> None:
        self.market.reset_books()
        self.history.clear()
        self.metrics.clear()
        self.blockchain = Blockchain()
        for agent in self.agents.values():
            agent.balance_history.clear()
            agent.generation_history.clear()
            agent.demand_history.clear()
            agent.trade_history.clear()

    def step(self, hour: int) -> Dict:
        self.market.reset_books()
        orders: List[Dict] = []
        total_surplus = 0.0
        total_deficit = 0.0
        for agent in self.agents.values():
            generation, demand, net = agent.step(hour)
            order = agent.propose_order(net, self.grid_price)
            if order:
                self.market.add_order(order)
                orders.append(order)
            if net > 0:
                total_surplus += net
            else:
                total_deficit += abs(net)

        matched_transactions, market_price, traded_volume = self.market.match_orders()
        unmatched_orders = [order for order in orders if order["quantity"] > 0]
        grid_transactions = self.market.settle_with_grid(unmatched_orders)
        all_transactions = matched_transactions + grid_transactions

        for tx in all_transactions:
            self._execute_transaction(tx)
            self.blockchain.add_transaction(tx)

        block = self.blockchain.mine_block()
        self.history.append(
            {
                "hour": hour,
                "market_price": round(market_price, 4),
                "traded_volume": round(traded_volume, 4),
                "surplus": round(total_surplus, 4),
                "deficit": round(total_deficit, 4),
                "block_hash": block.hash,
                "transactions": [tx.to_dict() for tx in all_transactions],
            }
        )
        self._record_metrics(hour, traded_volume, total_surplus, total_deficit, market_price)
        return self.history[-1]

    def _execute_transaction(self, tx: Transaction) -> None:
        buyer = self.agents.get(tx.buyer_id)
        seller = self.agents.get(tx.seller_id)
        total_cost = tx.price * tx.quantity
        if buyer:
            buyer.wallet -= total_cost
            buyer.record_trade({**tx.to_dict(), "role": "buyer"})
        if seller:
            seller.wallet += total_cost
            seller.record_trade({**tx.to_dict(), "role": "seller"})

    def _record_metrics(self, hour: int, traded_volume: float, surplus: float, deficit: float, market_price: float) -> None:
        efficiency = traded_volume / max(1.0, surplus + deficit)
        grid_load = max(0.0, deficit - traded_volume)
        savings = traded_volume * (self.grid_price - market_price)
        self.metrics.append(
            {
                "hour": hour,
                "price": round(market_price, 4),
                "traded_volume": round(traded_volume, 4),
                "efficiency": round(efficiency, 4),
                "grid_load": round(grid_load, 4),
                "cost_savings": round(max(0.0, savings), 4),
            }
        )

    def run(self, hours: int = 24) -> pd.DataFrame:
        self.reset()
        for hour in range(hours):
            self.step(hour)
        return self.get_summary()

    def get_summary(self) -> pd.DataFrame:
        return pd.DataFrame(self.metrics)

    def get_agent_summary(self) -> pd.DataFrame:
        rows = []
        for agent in self.agents.values():
            rows.append(
                {
                    "agent_id": agent.id,
                    "name": agent.name,
                    "type": agent.agent_type,
                    "wallet": round(agent.wallet, 2),
                    "generation_last": round(agent.generation_history[-1] if agent.generation_history else 0.0, 4),
                    "demand_last": round(agent.demand_history[-1] if agent.demand_history else 0.0, 4),
                    "trades": len(agent.trade_history),
                }
            )
        return pd.DataFrame(rows)

    def get_blockchain_history(self) -> pd.DataFrame:
        rows = []
        for block in self.blockchain.chain:
            rows.append(
                {
                    "index": block.index,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(block.timestamp)),
                    "hash": block.hash,
                    "previous_hash": block.previous_hash,
                    "transactions": len(block.transactions),
                }
            )
        return pd.DataFrame(rows)

    def get_transaction_ledger(self) -> pd.DataFrame:
        ledger = []
        for block in self.blockchain.chain:
            for tx in block.transactions:
                ledger.append({**tx, "block_index": block.index})
        return pd.DataFrame(ledger)

    def get_price_trend(self) -> pd.Series:
        return pd.Series([metric["price"] for metric in self.metrics], name="market_price")

    def get_trade_network(self) -> List[Dict]:
        edges = []
        for block in self.blockchain.chain:
            for tx in block.transactions:
                if tx["buyer_id"] >= 0 and tx["seller_id"] >= 0:
                    edges.append(
                        {
                            "source": tx["seller_id"],
                            "target": tx["buyer_id"],
                            "weight": tx["quantity"],
                            "price": tx["price"],
                        }
                    )
        return edges


def sample_simulation(num_prosumers: int = 3, num_consumers: int = 3, hours: int = 12) -> EnergyTradingSimulator:
    simulator = EnergyTradingSimulator(
        num_prosumers=num_prosumers,
        num_consumers=num_consumers,
        generation_capacity=8.0,
        demand_base=4.5,
        generation_variability=2.0,
        demand_variability=1.4,
        grid_price=0.22,
        grid_supply_price=0.10,
    )
    simulator.run(hours=hours)
    return simulator
