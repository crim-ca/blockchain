from datetime import datetime

from blockchain.impl import Base, WithDatetimeCreated, WithDatetimeExpire


class BaseTest(Base):
    @property
    def x(self):
        x = self.get("x")
        return {"prop": 1, "dict": x}

    @x.setter
    def x(self, x):
        dict.__setitem__(self, "x", {"set-x": x, "x": None})


class WithTimeProperties(WithDatetimeCreated, WithDatetimeExpire):
    pass


def test_property_resolved():
    # when property getter/setter are defined, they are enforced to apply any required data conversion/validation
    b = BaseTest()
    b["x"] = 2
    assert b["x"] == {"prop": 1, "dict": {"set-x": 2, "x": None}}  # would be '2' if get&set property not employed
    assert b.x == {"prop": 1, "dict": {"set-x": 2, "x": None}}
    x = b.json().get("x")  # ignore 'id'
    assert x == {"prop": 1, "dict": {"set-x": 2, "x": None}}

    b.x = 3
    assert b["x"] == {"prop": 1, "dict": {"set-x": 3, "x": None}}
    assert b.x == {"prop": 1, "dict": {"set-x": 3, "x": None}}
    x = b.json().get("x")  # ignore 'id'
    assert x == {"prop": 1, "dict": {"set-x": 3, "x": None}}

    # otherwise, default behaviour occurs
    b["y"] = 1
    assert b["y"] == 1
    assert b.y == 1
    y = b.json().get("y")  # ignore 'id'
    assert y == 1

    b.y = 2
    assert b["y"] == 2
    assert b.y == 2
    y = b.json().get("y")  # ignore 'id'
    assert y == 2

    # getter/setter also applied when initialized using any supported dict-like variation
    for b in [BaseTest(x=1, y=2), BaseTest({"x": 1, "y": 2}), BaseTest([("x", 1), ("y", 2)])]:
        j = b.json()
        x = j.get("x")  # ignore 'id'
        y = j.get("y")
        assert b["x"] == {"prop": 1, "dict": {"set-x": 1, "x": None}}
        assert b.x == {"prop": 1, "dict": {"set-x": 1, "x": None}}
        assert x == {"prop": 1, "dict": {"set-x": 1, "x": None}}
        assert b["y"] == 2
        assert b.y == 2
        assert y == 2


def test_with_times_properties():
    p = WithTimeProperties(created=datetime(2000, 12, 1))
    c = p.json().get("created")
    assert p.created == datetime(2000, 12, 1)
    assert p.expire is None
    assert c == "2000-12-01T00:00:00"
    p = WithTimeProperties(created="2000-12-01")
    c = p.json().get("created")
    assert p.created == datetime(2000, 12, 1)
    assert p.expire is None
    assert c == "2000-12-01T00:00:00"
    p = WithTimeProperties(created="2000-12-01T08:09:10")
    c = p.json().get("created")
    assert p.created == datetime(2000, 12, 1, 8, 9, 10)
    assert p.expire is None
    assert c == "2000-12-01T08:09:10"
    p = WithTimeProperties(created="2000-12-01 08:09:10")
    c = p.json().get("created")
    assert p.created == datetime(2000, 12, 1, 8, 9, 10)
    assert p.expire is None
    assert c == "2000-12-01T08:09:10"

    p = WithTimeProperties(expire=datetime(2000, 12, 1))
    e = p.json().get("expire")
    assert p.created is not None
    assert p.expire == datetime(2000, 12, 1)
    assert e == "2000-12-01T00:00:00"
    p = WithTimeProperties(expire="2000-12-01")
    c = p.json().get("expire")
    assert p.created is not None
    assert p.expire == datetime(2000, 12, 1)
    assert c == "2000-12-01T00:00:00"
    p = WithTimeProperties(expire="2000-12-01T08:09:10")
    c = p.json().get("expire")
    assert p.created is not None
    assert p.expire == datetime(2000, 12, 1, 8, 9, 10)
    assert c == "2000-12-01T08:09:10"
    p = WithTimeProperties(expire="2000-12-01 08:09:10")
    c = p.json().get("expire")
    assert p.created is not None
    assert p.expire == datetime(2000, 12, 1, 8, 9, 10)
    assert c == "2000-12-01T08:09:10"

    n = datetime.now()
    p = WithTimeProperties()  # autogen created, but not expire
    c = p.created
    e = p.expire
    assert c is not None
    assert c == p.created  # not regen, stored on first create during init
    assert n < c
    assert e is None
