# block = {
#     'index': 1,
#     'timestamp': 1506057125.900785,
#     'transactions': [
#         {
#             'sender': "8527147fe1f5426f9dd545de4b27ee00",
#             'recipient': "a77f5cdfa2934df3954a5c7c7da5df1f",
#             'amount': 5,
#         }
#     ],
#     'proof': 324984774000,
#     'previous_hash': "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
# }


class Block(object):
    def __init__(self, index=0, timestamp=0, transactions="", proof=0, previous_hash=""):
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions
        self.proof = proof
        self.previous_hash = previous_hash
        pass


# :param sender: <str> Address of the Sender
# :param recipient: <str> Address of the Recipient
# :param amount: <int> Amount
class Transaction(object):
    def __init__(self, sender, recipient, amount):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        pass
