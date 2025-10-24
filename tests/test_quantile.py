from stream_metrics.metrics import quantile
def test_quantile_simple():
    data = [1,2,3,4,5,6,7,8,9,10]
    assert quantile(data, 0.5) == 5.5
    assert round(quantile(data, 0.95),1) == 9.6
