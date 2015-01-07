from pyethereum import tester
from pyethereum import utils

class TestCommitRevealEntropyContract(object):

    CONTRACT = 'contracts/commit_reveal_entropy.se'

    def setup_class(cls):
        cls.s = tester.state()
        cls.c = cls.s.contract(cls.CONTRACT)
        cls.snapshot = cls.s.snapshot()

    def setup_method(self, method):
        self.s.revert(self.snapshot)

    def _request_entropy(self, cost=10**15):
        return self.s.send(tester.k0, self.c, cost, funid=0, abi=[])

    def _get_entropy(self, ticket_id):
        return self.s.send(tester.k0, self.c, 0, funid=1, abi=[ticket_id])

    def _get_entropy_ticket(self, ticket_id):
        return self.s.send(tester.k0, self.c, 0, funid=2, abi=[ticket_id])

    def _commit(self, target, hash, cost=10**18):
        return self.s.send(tester.k0, self.c, cost, funid=3, abi=[target, hash])

    def _reveal(self, target, value):
        return self.s.send(tester.k0, self.c, 0, funid=4, abi=[target, value])

    def _get_block(self, target):
        return self.s.send(tester.k0, self.c, 0, funid=5, abi=[target])

    def _call_hash(self, value):
        return self.s.send(tester.k0, self.c, 0, funid=6, abi=[utils.big_endian_to_int(value)])

    def _hash_value(self, value):
        return utils.big_endian_to_int(utils.sha3(utils.zpad(value, 32)))

    def test_request_entropy(self):
        assert self._request_entropy() == [0, 4]
        assert self._get_entropy_ticket(0) == [int(tester.a0, 16), 0, self.s.block.number + 1, 0]
        assert self._get_entropy(0) == [0, 0]  # pending

    def test_request_entropy_insufficient_fee(self):
        assert self._request_entropy(cost=0) == [0]
        assert self._get_entropy_ticket(0) == [0, 0, 0, 0]
        assert self._get_entropy(0) == [3, 0]  # not found

    def test_request_multiple_entropy_tickets(self):
        assert self._request_entropy() == [0, 4]
        assert self._request_entropy() == [1, 4]
        assert self._request_entropy() == [2, 4]

        assert self._get_entropy_ticket(0) == [int(tester.a0, 16), 0, self.s.block.number + 1, 0]
        assert self._get_entropy_ticket(1) == [int(tester.a0, 16), 0, self.s.block.number + 1, 0]
        assert self._get_entropy_ticket(2) == [int(tester.a0, 16), 0, self.s.block.number + 1, 0]

    def test_request_entropy_target_depends_on_block_number(self):
        self.s.mine()
        assert self._request_entropy() == [0, 5]
        assert self._get_entropy_ticket(0) == [int(tester.a0, 16), 0, self.s.block.number + 1, 0]

        self.s.mine(10)
        assert self._request_entropy() == [1, 15]
        assert self._get_entropy_ticket(1) == [int(tester.a0, 16), 0, self.s.block.number + 1, 0]

    def test_request_entropy_get_expired(self):
        assert self._request_entropy() == [0, 4]

        # XXX off by one?
        self.s.mine(4)
        assert self.s.block.number == 4
        assert self._get_entropy(0) == [2, 0]  # expired

    def test_hash_sha3(self):
        value = 'cow'
        assert self._call_hash(value) == [self._hash_value(value)]
