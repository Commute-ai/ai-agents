from fastapi.testclient import TestClient


def test_generate_itineraries_with_insights_success(client: TestClient):
    """Test successful insight generation for itineraries"""
    # The client fixture already mocks the insight service

    payload = {
        "itineraries": [
            {
                "start": "2024-01-01T08:00:00",
                "end": "2024-01-01T09:00:00",
                "duration": 3600,
                "walk_distance": 500.0,
                "walk_time": 600,
                "legs": [
                    {
                        "mode": "BUS",
                        "start": "2024-01-01T08:00:00",
                        "end": "2024-01-01T08:30:00",
                        "duration": 1800,
                        "distance": 5000.0,
                        "from_place": {
                            "coordinates": {"latitude": 40.7128, "longitude": -74.0060},
                            "name": "Start Location",
                        },
                        "to_place": {
                            "coordinates": {"latitude": 40.7589, "longitude": -73.9851},
                            "name": "End Location",
                        },
                        "route": {
                            "short_name": "M15",
                            "long_name": "M15 Select Bus Service",
                            "description": "Manhattan bus route",
                        },
                    }
                ],
            }
        ],
        "user_preferences": [{"prompt": "I prefer faster routes"}],
    }

    response = client.post("/api/v1/insight/itineraries", json=payload)

    assert response.status_code == 200
    data = response.json()

    assert "itinerary_insights" in data
    assert len(data["itinerary_insights"]) == 1
    # Test uses mock insight service which returns standardized mock insights
    assert data["itinerary_insights"][0]["ai_insight"] == "Mock overall itinerary insight"
    assert "leg_insights" in data["itinerary_insights"][0]
    assert len(data["itinerary_insights"][0]["leg_insights"]) == 1  # One leg in test data
    assert (
        data["itinerary_insights"][0]["leg_insights"][0]["ai_insight"] == "Mock insight for leg 1"
    )


def test_generate_itineraries_with_insights_empty_list(client: TestClient):
    """Test with empty itineraries list - should return error"""
    payload = {"itineraries": [], "user_preferences": []}

    response = client.post("/api/v1/insight/itineraries", json=payload)

    # Should return 400 because service validates at least one itinerary is required
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "At least one itinerary is required" in data["detail"]


def test_generate_itineraries_with_insights_no_preferences(client: TestClient):
    """Test without user preferences"""
    payload = {
        "itineraries": [
            {
                "start": "2024-01-01T08:00:00",
                "end": "2024-01-01T09:00:00",
                "duration": 3600,
                "walk_distance": 500.0,
                "walk_time": 600,
                "legs": [],
            }
        ]
    }

    response = client.post("/api/v1/insight/itineraries", json=payload)

    assert response.status_code == 200
    data = response.json()

    assert "itinerary_insights" in data
    assert len(data["itinerary_insights"]) == 1
    # Uses standard mock response
    assert data["itinerary_insights"][0]["ai_insight"] == "Mock overall itinerary insight"


def test_generate_itineraries_with_insights_multiple_itineraries(client: TestClient):
    """Test with multiple itineraries"""
    payload = {
        "itineraries": [
            {
                "start": "2024-01-01T08:00:00",
                "end": "2024-01-01T09:00:00",
                "duration": 3600,
                "walk_distance": 500.0,
                "walk_time": 600,
                "legs": [],
            },
            {
                "start": "2024-01-01T08:15:00",
                "end": "2024-01-01T09:15:00",
                "duration": 3600,
                "walk_distance": 800.0,
                "walk_time": 900,
                "legs": [],
            },
        ]
    }

    response = client.post("/api/v1/insight/itineraries", json=payload)

    assert response.status_code == 200
    data = response.json()

    assert "itinerary_insights" in data
    assert len(data["itinerary_insights"]) == 2

    # Check that each insight is properly structured (uses mock service)
    for itinerary_insight in data["itinerary_insights"]:
        assert "ai_insight" in itinerary_insight
        assert "leg_insights" in itinerary_insight
        assert itinerary_insight["ai_insight"] == "Mock overall itinerary insight"
        assert isinstance(itinerary_insight["leg_insights"], list)


def test_generate_itineraries_with_insights_invalid_payload(client: TestClient):
    """Test with invalid payload structure"""
    payload = {"invalid": "payload"}

    response = client.post("/api/v1/insight/itineraries", json=payload)

    assert response.status_code == 422
