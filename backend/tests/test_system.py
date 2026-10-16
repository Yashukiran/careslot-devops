def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "UP"}


def test_ready_checks_database(client):
    res = client.get("/ready")
    assert res.status_code == 200
    assert res.json()["status"] == "READY"


def test_metrics_endpoint_is_prometheus_format(client):
    client.get("/api/doctors")
    res = client.get("/metrics")
    assert res.status_code == 200
    assert "http_requests_total" in res.text
