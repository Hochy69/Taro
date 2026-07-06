from app.application.services.admin_stats_service import TEST_TELEGRAM_IDS


def test_qa_telegram_ids_include_integration_user():
    assert 999999001 in TEST_TELEGRAM_IDS
    assert 555000111 in TEST_TELEGRAM_IDS
