import sys
import time
from uuid import uuid4

from flask import Flask, jsonify, request

import util
from blockchain import BlockChain

app = Flask(__name__)

node_identifier = str(uuid4()).replace('-', '')

block_chain = BlockChain()


@app.route('/transaction/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    if not all(k in values for k in ['sender', 'recipient', 'amount']):
        return msg_resp('Missing values', 400)
    index = block_chain.new_transaction(values['sender'], values['recipient'], values['amount'])
    return msg_resp(f'Transaction will be added to Block {index}', 201)


@app.route('/chain', methods=['GET'])
def full_chain():
    resp = {
        'chain': block_chain.chain,
        'length': len(block_chain.chain),
    }
    return json_resp(util.to_json(resp))


@app.route('/mine', methods=['GET'])
def mine():
    # check the transactions if exist
    if not block_chain.current_transactions:
        return msg_resp('No transactions', 400)
    last_block = block_chain.last_block
    # # chan is empty, init a root block
    # if not last_block:
    #     # root block
    #     block = block_chain.new_block(0, "root")
    # create a new block
    # else:

    # do work
    proof = block_chain.proof_of_work()

    # get a reword
    block_chain.new_transaction("0", node_identifier, 1)

    # build a block
    previous_hash = block_chain.hash(last_block)

    # add to chain
    block = block_chain.new_block(proof, previous_hash)

    resp = util.to_json(block)
    return json_resp(resp)


@app.route('/user', methods=['GET'])
def user():
    return json_resp({'id': node_identifier})


@app.route('/node/register', methods=['POST'])
def register_node():
    values = request.get_json()
    print(values)
    nodes = values.get('nodes')
    print(nodes)

    if not nodes:
        return msg_resp('Error nodes', 400)

    for node in nodes:
        block_chain.register_node(node)

    return json_resp({'message': 'nodes have been added', 'total_nodes': list(block_chain.nodes), })


@app.route('/node/resolve', methods=['GET'])
def consensus_node():
    if block_chain.resolve_conflicts():
        message = 'Local chain has been replaced'
    else:
        message = 'Local chain is authoritative'
    return msg_resp(message)


def json_resp(resp, code=200):
    if isinstance(resp, dict):
        return jsonify(resp), code
    elif isinstance(resp, str):
        return resp, code, {'Content-Type': 'application/json'}
    return resp, code


def msg_resp(message, code=200):
    return jsonify({'message': message}), code


if __name__ == '__main__':
    app.run(host='localhost', port=5001)
