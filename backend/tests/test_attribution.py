from app.application.services.attribution_service import normalize_acquisition_source


def test_normalize_partner_and_ads_sources():
    assert normalize_acquisition_source("p_psyloveys") == "p_psyloveys"
    assert normalize_acquisition_source("ADS_Love") == "ads_love"
    assert normalize_acquisition_source(" ads_tarot ") == "ads_tarot"


def test_normalize_rejects_referrals_and_junk():
    assert normalize_acquisition_source("ref_ABCDEF12") is None
    assert normalize_acquisition_source("") is None
    assert normalize_acquisition_source(None) is None
    assert normalize_acquisition_source("bad source!") is None
