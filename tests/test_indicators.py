from main import ema, rsi, analyse

def test_ema_length():
    assert len(ema([1,2,3,4], 2)) == 4

def test_rsi_range():
    value = rsi([float(x) for x in range(1,40)])
    assert 0 <= value <= 100

def test_analysis_schema():
    bars = [{"open":i,"high":i+1,"low":i-1,"close":i+0.5,"openTime":str(i)} for i in range(1,100)]
    result = analyse(bars)
    assert result["signal"] in {"CALL","PUT","WAIT"}
    assert 0 <= result["strength"] <= 95
