from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import json
import asyncio
from uuid import uuid4

@dataclass
class Block:
    index: int
    timestamp: float
    transactions: List[Dict[str, Any]]
    previous_hash: str
    nonce: int = 0
    hash: str = field(init=False)

    def __post_init__(self):
        self.hash = self.calculate_hash()

    def calculate_hash(self) -> str:
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

class BlockchainManager:
    def __init__(self, difficulty: int = 4):
        self.chain: List[Block] = []
        self.pending_transactions: List[Dict[str, Any]] = []
        self.difficulty = difficulty
        self.mining_reward = 1.0
        self.create_genesis_block()
        asyncio.create_task(self._mine_pending_transactions())

    def create_genesis_block(self) -> None:
        genesis_block = Block(
            index=0,
            timestamp=datetime.now().timestamp(),
            transactions=[],
            previous_hash="0"
        )
        self.chain.append(genesis_block)

    async def record_transaction(self, transaction: Any) -> str:
        tx_data = {
            "id": str(uuid4()),
            "timestamp": datetime.now().timestamp(),
            "data": transaction.__dict__
        }
        self.pending_transactions.append(tx_data)
        return tx_data["id"]

    async def update_transaction(self, transaction: Any) -> None:
        tx_data = {
            "id": str(uuid4()),
            "timestamp": datetime.now().timestamp(),
            "type": "update",
            "data": transaction.__dict__
        }
        self.pending_transactions.append(tx_data)

    def get_latest_block(self) -> Block:
        return self.chain[-1]

    async def mine_block(self, miner_address: str) -> Block:
        if not self.pending_transactions:
            return None

        block = Block(
            index=len(self.chain),
            timestamp=datetime.now().timestamp(),
            transactions=self.pending_transactions[:],
            previous_hash=self.get_latest_block().hash
        )

        while not block.hash.startswith("0" * self.difficulty):
            block.nonce += 1
            block.hash = block.calculate_hash()

        self.chain.append(block)
        self.pending_transactions = [
            {
                "from": "network",
                "to": miner_address,
                "amount": self.mining_reward
            }
        ]
        return block

    def is_chain_valid(self) -> bool:
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            if current_block.hash != current_block.calculate_hash():
                return False

            if current_block.previous_hash != previous_block.hash:
                return False

        return True

    def get_transaction_history(self, transaction_id: Optional[str] = None) -> List[Dict[str, Any]]:
        history = []
        for block in self.chain:
            for tx in block.transactions:
                if not transaction_id or tx.get("id") == transaction_id:
                    history.append({
                        "block_index": block.index,
                        "timestamp": block.timestamp,
                        "transaction": tx
                    })
        return history

    async def _mine_pending_transactions(self) -> None:
        while True:
            if len(self.pending_transactions) >= 5:
                await self.mine_block("system")
            await asyncio.sleep(10)