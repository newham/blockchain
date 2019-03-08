import json
import sys
import time
from uuid import uuid4

from flask import Flask, jsonify, request

import paho.mqtt.client as mqtt

import util

import _thread

from blockchain import BlockChain

app = Flask(__name__)

node_identifier = str(uuid4()).replace('-', '')

block_chain = BlockChain()

client = mqtt.Client()


@app.route('/transaction/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    index = add_transaction(values)
    if index < 0:
        return msg_resp('Missing values', 400)
    # pub transaction to other nodes
    pub_msg(TOPIC_NEW_TRANSACTION, util.to_json(values))
    # do response
    return msg_resp(f'Transaction will be added to Block {index}', 201)


def add_transaction(values):
    if not all(k in values for k in ['sender', 'recipient', 'amount']):
        return -1
    index = block_chain.new_transaction(values['sender'], values['recipient'], values['amount'])
    # print('add transaction', values['sender'], values['recipient'], values['amount'])
    return index


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

    # do work

    proof = block_chain.proof_of_work(block_chain.last_proof())

    # get a reword
    block_chain.new_transaction("0", node_identifier, 1)

    # build a block
    previous_hash = block_chain.hash(block_chain.last_block)

    # add to chain
    block = block_chain.new_block(proof, previous_hash)

    # add start
    block_chain_json = {
        'chain': block_chain.chain,
        'length': len(block_chain.chain),
    }
    # pub msg to other nodes
    pub_msg(TOPIC_RESOLVE, util.to_json(block_chain_json))
    # add end

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


TOPIC_RESOLVE = "node/resolve/"
TOPIC_NEW_TRANSACTION = "transaction/new/"


def on_connect(client, userdata, flags, rc):
    app.logger.info("Connected to mqtt broker")


def register_node_mptt():
    client.on_message = on_resolve_msg
    client.on_connect = on_connect
    client.connect("212.64.27.116", 1883, 60)
    client.subscribe(TOPIC_RESOLVE + '+')
    client.subscribe(TOPIC_NEW_TRANSACTION + '+')
    client.loop_start()


def on_resolve_msg(client, userdata, msg):
    msg_topic = msg.topic.rsplit('/', 1)[0] + '/'
    id = msg.topic.rsplit('/', 1)[1]
    msg_payload = msg.payload.decode()
    msg_json = json.loads(msg_payload)
    # print("on_resolve_msg", id, msg_topic)
    if not id or id == node_identifier:
        return
    if msg_topic == TOPIC_RESOLVE:
        if block_chain.resolve_conflicts(msg_json):
            message = 'Local chain has been replaced'
        else:
            message = 'Local chain is authoritative'
        app.logger.info(message)
    elif msg_topic == TOPIC_NEW_TRANSACTION:
        add_transaction(msg_json)


def pub_msg(topic, msg):
    client.publish(topic + node_identifier, msg)


def msg_resp(message, code=200):
    return jsonify({'message': message}), code


if __name__ == '__main__':
    # _thread.start_new_thread(register_node_mptt,())
    register_node_mptt()
    # _thread.start_new_thread(sent_msg,())
    app.run(host='localhost', port=5000)
