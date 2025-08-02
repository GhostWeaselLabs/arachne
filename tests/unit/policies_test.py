from meridian.core.policies import Block, Coalesce, Drop, Latest, PutResult


def test_block_policy() -> None:
    p = Block()
    assert p.on_enqueue(1, 0, 1) == PutResult.OK
    assert p.on_enqueue(1, 1, 2) == PutResult.BLOCKED


def test_drop_policy() -> None:
    p = Drop()
    assert p.on_enqueue(1, 1, 2) == PutResult.DROPPED


def test_latest_policy() -> None:
    p = Latest()
    assert p.on_enqueue(1, 0, 1) == PutResult.OK
    assert p.on_enqueue(1, 1, 2) == PutResult.REPLACED


def test_coalesce_policy_and_exceptions() -> None:
    p = Coalesce(lambda a, b: (a or 0) + (b or 0))
    assert p.on_enqueue(1, 1, 2) == PutResult.COALESCED
    bad = Coalesce(lambda a, b: (_ for _ in ()).throw(RuntimeError("boom")))
    assert bad.on_enqueue(1, 1, 2) == PutResult.COALESCED
