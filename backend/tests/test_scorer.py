from app.recommendation.scorer import (
    NIFTY_PE_MEDIAN,
    _safe_float,
    score_dividend,
    score_fundamentals,
    score_momentum,
)


class TestSafeFloat:
    def test_valid_values(self):
        assert _safe_float({"x": 5}, "x") == 5.0
        assert _safe_float({"x": "3.14"}, "x") == 3.14

    def test_invalid_values(self):
        assert _safe_float({}, "x") is None
        assert _safe_float({"x": None}, "x") is None
        assert _safe_float({"x": "N/A"}, "x") is None
        assert _safe_float({"x": [1]}, "x") is None


class TestScoreFundamentals:
    def test_no_data_marks_unavailable(self):
        f = score_fundamentals({})
        assert f.data_available is False
        assert f.score == 0.5  # neutral fallback, excluded from composite anyway

    def test_cheap_profitable_low_debt_scores_high(self):
        f = score_fundamentals({
            "pe_ratio": 12.0,
            "pb_ratio": 1.5,
            "return_on_equity": 0.22,
            "profit_margin": 0.18,
            "debt_to_equity": 0.2,
        })
        assert f.data_available is True
        assert f.score > 0.6
        assert "Fundamentals" in f.sources

    def test_expensive_leveraged_scores_low(self):
        f = score_fundamentals({
            "pe_ratio": NIFTY_PE_MEDIAN * 3,
            "pb_ratio": 12.0,
            "return_on_equity": 0.02,
            "profit_margin": 0.01,
            "debt_to_equity": 2.5,
        })
        assert f.score < 0.4

    def test_debt_to_equity_percentage_normalization(self):
        # yfinance reports D/E as a percentage (e.g. 45.0 == 0.45x)
        as_pct = score_fundamentals({"debt_to_equity": 45.0})
        as_ratio = score_fundamentals({"debt_to_equity": 0.45})
        assert abs(as_pct.score - as_ratio.score) < 1e-9


class TestScoreMomentum:
    def test_missing_data(self):
        f = score_momentum({"current_price": 100.0})
        assert f.data_available is False

    def test_price_position_tiers(self):
        base = {"52_week_high": 200.0, "52_week_low": 100.0}
        near_high = score_momentum({**base, "current_price": 195.0})
        upper = score_momentum({**base, "current_price": 170.0})
        near_low = score_momentum({**base, "current_price": 105.0})
        assert near_high.score == 0.7  # capped: limited upside room
        assert upper.score == 0.8
        assert near_low.score == 0.3

    def test_degenerate_range(self):
        f = score_momentum({
            "current_price": 100.0, "52_week_high": 100.0, "52_week_low": 100.0,
        })
        assert f.data_available is True  # neutral, but no crash


class TestScoreDividend:
    def test_no_yield_data(self):
        f = score_dividend({})
        assert f.data_available is False

    def test_yield_ordering(self):
        high = score_dividend({"dividend_yield": 0.07})
        moderate = score_dividend({"dividend_yield": 0.02})
        none_paid = score_dividend({"dividend_yield": 0.0})
        assert high.score > moderate.score > none_paid.score
