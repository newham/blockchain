import json


def to_json(object):
    return json.dumps(object, default=lambda obj: obj.__dict__, sort_keys=True)


def test_json():
    j = {'hi': 'hi'}
    hi = Hi()
    hi.__dict__.update(j)
    print(hi.hi, j['hi'])

class Hi:
    def __init__(self,hi='null'):
        self.hi = hi
