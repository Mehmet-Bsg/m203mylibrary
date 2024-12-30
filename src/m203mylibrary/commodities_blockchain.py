import yfinance as yf
import pandas as pd
import numpy as np
import logging
import hashlib
import time
import pickle
import os
import random
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from scipy.optimize import minimize

# --------------------------------------------------------------------------------
# Utilities for random naming (kept from original for demonstration)
# --------------------------------------------------------------------------------
animals = [
    "Eagle", "Tiger", "Lion", "Wolf", "Bear", "Falcon", "Shark", "Panther", "Leopard", "Cheetah",
    "Hawk", "Fox", "Owl", "Cobra", "Jaguar", "Horse", "Elephant", "Dolphin", "Gorilla", "Lynx"
]
professions = [
    "Carpenter", "Engineer", "Doctor", "Pilot", "Farmer", "Artist", "Blacksmith", "Chef", "Teacher", "Mechanic",
    "Architect", "Scientist", "Soldier", "Nurse", "Firefighter", "Plumber", "Astronaut", "Tailor", "Photographer", "Lawyer"
]
colors = [
    "Red", "Blue", "Green", "Yellow", "Black", "White", "Purple", "Orange", "Brown", "Grey",
    "Pink", "Violet", "Crimson", "Turquoise", "Gold", "Silver", "Amber", "Magenta", "Teal", "Indigo"
]

def generate_random_name():
    animal = random.choice(animals)
    profession = random.choice(professions)
    color = random.choice(colors)
    return f"{color}{animal}{profession}"

# --------------------------------------------------------------------------------
# Blockchain data structure (same as original script)
# --------------------------------------------------------------------------------

@dataclass
class Block:
    name_backtest: str
    data: str
    previous_hash: str = ''
    timestamp: float = field(default_factory=time.time)
    hash: str = field(init=False)

    def __post_init__(self):
        self.hash = self.calculate_hash

    @property
    def calculate_hash(self):
        return hashlib.sha256(
            (str(self.timestamp)
             + self.name_backtest
             + self.data
             + self.previous_hash).encode()
        ).hexdigest()

@dataclass
class Blockchain:
    name: str
    chain: list = field(default_factory=list)

    def store(self):
        if not os.path.exists('blockchain'):
            os.makedirs('blockchain')
        with open(f'blockchain/{self.name}.pkl', 'wb') as f:
            pickle.dump(self, f)

    def __post_init__(self):
        # Initialize the chain with the genesis block
        self.chain.append(self.create_genesis_block())
        self.store()

    def create_genesis_block(self):
        return Block('Genesis Block', '', '0')

    def add_block(self, name: str, data: str):
        previous_block = self.chain[-1]
        new_block = Block(name, data, previous_block.hash)
        self.chain.append(new_block)
        self.store()

    def is_valid(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            if current_block.hash != current_block.calculate_hash:
                return False

            if current_block.previous_hash != previous_block.hash:
                return False

        return True

    def __str__(self):
        to_return = ''
        for i, block in enumerate(self.chain):
            to_return += "-" * 80 + '\n'
            to_return += f"Block {i}\n"
            to_return += "-" * 80 + '\n'
            to_return += f"Backtest: {block.name_backtest}\n"
            to_return += f"Timestamp: {block.timestamp}\n"
            to_return += f"Hash: {block.hash}\n"
            to_return += f"Previous Hash: {block.previous_hash}\n"
            to_return += "-" * 80 + '\n'
        return to_return

    def remove_blockchain(self):
        # remove the blockchain from disk
        os.remove(f'blockchain/{self.name}.pkl')

def load_blockchain(name: str):
    with open(f'blockchain/{name}.pkl', 'rb') as f:
        return pickle.load(f)

def remove_blockchain(name: str):
    os.remove(f'blockchain/{name}.pkl')