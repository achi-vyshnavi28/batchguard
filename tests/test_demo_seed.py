"""Hosted demo seed (not a validation requirement, so it is kept out of the OQ protocol)."""

from batchguard.alcoa import alcoa_report


def test_demo_batches_follow_the_same_rules(tmp_path):
    """Hosted-demo seed: built through the real services, so the rules, signatures and audit trail all hold."""
    from batchguard import services as svc
    from batchguard.models import make_session_factory
    Session = make_session_factory(f"sqlite:///{(tmp_path / 'demo.sqlite3').as_posix()}")
    with Session() as db:
        svc.seed(db)
        released, blocked, running = svc.seed_demo_batches(db)
        db.commit()
        assert (released.status, blocked.status, running.status) == ("released", "in_progress", "in_progress")
        assert any("Deviation" in b and "open" in b for b in svc.release_blockers(db, blocked.id))
        assert any("not verified" in b for b in svc.release_blockers(db, running.id))
        assert [c["status"] for c in alcoa_report(db, released.id)] == ["pass"] * 9
        assert svc.verify_audit_chain(db)[0]
    Session.kw["bind"].dispose()
