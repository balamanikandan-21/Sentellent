from app.recommendation.types import FactorScore, ScoreCard


def _factor(name: str, score: float, weight: float, available: bool = True) -> FactorScore:
    return FactorScore(
        name=name,
        score=score,
        weight=weight,
        data_available=available,
        reasoning="test",
    )


class TestFactorScore:
    def test_weighted_score(self):
        f = _factor("fundamentals", 0.8, 0.20)
        assert f.weighted == 0.8 * 0.20

    def test_unavailable_factor_contributes_zero(self):
        f = _factor("momentum", 0.9, 0.10, available=False)
        assert f.weighted == 0.0

    def test_to_dict_rounds(self):
        f = _factor("value", 0.666666, 0.12)
        d = f.to_dict()
        assert d["score"] == 0.67
        assert d["weight"] == 0.12


class TestScoreCard:
    def test_empty_scorecard(self):
        card = ScoreCard(ticker="TCS")
        assert card.composite_score == 0.0
        assert card.data_coverage == 0.0
        assert card.action == "SELL"  # score 0.0 <= 0.35
        assert card.confidence == "low"

    def test_composite_is_weighted_average_of_available(self):
        card = ScoreCard(
            ticker="RELIANCE",
            factors=[
                _factor("a", 1.0, 0.5),
                _factor("b", 0.0, 0.5),
            ],
        )
        assert card.composite_score == 0.5

    def test_unavailable_factors_excluded_from_weights(self):
        # Only factor "a" has data; composite should equal its raw score,
        # not be dragged down by the unavailable factor's weight.
        card = ScoreCard(
            ticker="INFY",
            factors=[
                _factor("a", 0.8, 0.2),
                _factor("b", 0.9, 0.8, available=False),
            ],
        )
        assert abs(card.composite_score - 0.8) < 1e-9

    def test_action_thresholds(self):
        buy = ScoreCard(ticker="X", factors=[_factor("a", 0.65, 1.0)])
        hold = ScoreCard(ticker="X", factors=[_factor("a", 0.5, 1.0)])
        sell = ScoreCard(ticker="X", factors=[_factor("a", 0.35, 1.0)])
        assert buy.action == "BUY"
        assert hold.action == "HOLD"
        assert sell.action == "SELL"

    def test_data_coverage_and_confidence_tiers(self):
        factors = [_factor(str(i), 0.5, 0.25) for i in range(4)]
        full = ScoreCard(ticker="X", factors=factors)
        assert full.data_coverage == 1.0
        assert full.confidence == "high"

        factors_half = factors[:2] + [
            _factor("c", 0.5, 0.25, available=False),
            _factor("d", 0.5, 0.25, available=False),
        ]
        half = ScoreCard(ticker="X", factors=factors_half)
        assert half.data_coverage == 0.5
        assert half.confidence == "medium"

        factors_low = factors[:1] + [_factor(str(i), 0.5, 0.25, available=False) for i in range(3)]
        low = ScoreCard(ticker="X", factors=factors_low)
        assert low.data_coverage == 0.25
        assert low.confidence == "low"

    def test_to_dict_shape(self):
        card = ScoreCard(ticker="TCS", factors=[_factor("a", 0.7, 1.0)])
        d = card.to_dict()
        assert d["ticker"] == "TCS"
        assert d["action"] == "BUY"
        assert len(d["factors"]) == 1
        assert set(d["factors"][0]) == {
            "name",
            "score",
            "weight",
            "weighted_score",
            "data_available",
            "reasoning",
            "sources",
        }
