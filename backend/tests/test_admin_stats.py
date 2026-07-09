from app.application.services.admin_stats_service import (
    TEST_TELEGRAM_IDS,
    _is_production_user,
)


def test_qa_telegram_ids_include_integration_user():
    assert 999999001 in TEST_TELEGRAM_IDS
    assert 555000111 in TEST_TELEGRAM_IDS
    assert 900000001 in TEST_TELEGRAM_IDS


def test_production_user_filter_excludes_admins_and_tests():
    clause = str(_is_production_user().compile(compile_kwargs={"literal_binds": True}))
    assert "is_admin" in clause.lower() or "false" in clause.lower()
    assert "999999001" in clause
