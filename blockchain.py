import hashlib
from time import time
from urllib.parse import urlparse

import requests

import util
from block import Block, Transaction


class BlockChain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()

    def register_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.path)

    def new_block(self, proof, previous_hash=None):
        # 生成新的区块
        block = Block(len(self.chain) + 1, time(), self.current_transactions, proof,
                      previous_hash or self.hash(self.chain[-1]))
        # 重置当前交易记录
        self.current_transactions = []
        # 追加
        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        self.current_transactions.append(Transaction(sender, recipient, amount))
        block_index = 1 if self.last_block is None else self.last_block.index + 1
        return block_index

    @staticmethod
    def hash(block):
        # block_string = json.dumps(block, sort_keys=True).encode()
        if not block:
            block_str = "root"
        else:
            block_str = util.to_json(block)
        return hashlib.sha256(block_str.encode()).hexdigest()

    @property
    def last_block(self):
        if len(self.chain) == 0:
            return None
        return self.chain[-1]

    def proof_of_work(self):
        proof = 0
        while self.valid_proof(proof) is False:
            proof += 1
        return proof

    @staticmethod
    def valid_proof(proof):
        # guess = f'{last_proof}{proof}'.encode()
        guess = f'{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    def user_account(self, id):
        return 0

    def valid_chain(self, chain):
        # last_block = block_chain.last_block
        index = len(chain) - 1

        # compare root block's hash
        if not chain or chain[0].previous_hash != self.chain[0].previous_hash:
            return False

        # check other block : last -> root
        while index > 1:
            current_block = chain[index]
            last_block = chain[index - 1]
            # check hash
            if current_block.previous_hash != self.hash(last_block):
                print(current_block.previous_hash, self.hash(last_block))
                return False
            # check proof
            if not self.valid_proof(current_block.proof):
                print(current_block.proof)
                return False
            index -= 1

        return True

    def resolve_conflicts(self):
        neighbours = self.nodes
        new_chain = None

        max_length = len(self.chain)

        for node in neighbours:
            try:
                resp = requests.get(f'http://{node}/chain')
            except BaseException:
                continue
            else:
                if resp.status_code == 200:
                    print("start to resolve")
                    resp_json = resp.json()
                    length = resp_json['length']
                    node_chain = []
                    for block_json in resp_json['chain']:
                        block = Block()
                        block.__dict__.update(block_json)
                        node_chain.append(block)
                    print("build chain done")
                    print("other:", length, "local:", max_length)
                    if length > max_length and self.valid_chain(node_chain):
                        max_length = length
                        new_chain = node_chain

        if new_chain:
            self.chain = new_chain
            return True

        return False
