from fastapi.testclient import TestClient

from tests.conftest import MockLLMProvider


def test_generate_itineraries_with_insights_success(client: TestClient):
    """Test successful insight generation for itineraries"""
    # Mock the LLM provider to return a test response
    mock_provider = MockLLMProvider(response="Test AI insight for this route")

    # Override the dependency to use our mock
    from app.agents.insight import InsightAgent
    from app.dependencies import get_insight_agent

    client.app.dependency_overrides[get_insight_agent] = lambda: InsightAgent(mock_provider)

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

    assert "itineraries" in data
    assert len(data["itineraries"]) == 1

    itinerary = data["itineraries"][0]
    assert "ai_insight" in itinerary
    assert "Test AI insight" in itinerary["ai_insight"]
    assert itinerary["duration"] == 3600
    assert itinerary["walk_distance"] == 500.0

    # Clean up dependency override
    client.app.dependency_overrides.clear()


def test_generate_itineraries_with_insights_empty_list(client: TestClient):
    """Test with empty itineraries list - should return error"""
    mock_provider = MockLLMProvider()

    # Override the dependency to use our mock
    from app.agents.insight import InsightAgent
    from app.dependencies import get_insight_agent

    client.app.dependency_overrides[get_insight_agent] = lambda: InsightAgent(mock_provider)

    payload = {"itineraries": [], "user_preferences": []}

    response = client.post("/api/v1/insight/itineraries", json=payload)

    # Should return 500 because agent validates at least one itinerary is required
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert "At least one itinerary is required" in data["detail"]

    # Clean up dependency override
    client.app.dependency_overrides.clear()


def test_generate_itineraries_with_insights_no_preferences(client: TestClient):
    """Test without user preferences"""
    mock_provider = MockLLMProvider(
        response="Route Option 1:\nSimple route analysis without preferences"
    )

    from app.agents.insight import InsightAgent
    from app.dependencies import get_insight_agent

    client.app.dependency_overrides[get_insight_agent] = lambda: InsightAgent(mock_provider)

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

    assert "itineraries" in data
    assert len(data["itineraries"]) == 1
    assert "ai_insight" in data["itineraries"][0]
    assert "Simple route analysis" in data["itineraries"][0]["ai_insight"]

    # Clean up dependency override
    client.app.dependency_overrides.clear()


def test_generate_itineraries_with_insights_multiple_itineraries(client: TestClient):
    """Test with multiple itineraries"""
    mock_provider = MockLLMProvider(
        response="""Route Option 1:
First route analysis with shorter walking distance.

Route Option 2:
Second route analysis with longer walking but similar time."""
    )

    from app.agents.insight import InsightAgent
    from app.dependencies import get_insight_agent

    client.app.dependency_overrides[get_insight_agent] = lambda: InsightAgent(mock_provider)

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

    assert "itineraries" in data
    assert len(data["itineraries"]) == 2

    # Check that each itinerary has an AI insight
    for itinerary in data["itineraries"]:
        assert "ai_insight" in itinerary
        assert len(itinerary["ai_insight"]) > 0

    # Clean up dependency override
    client.app.dependency_overrides.clear()


def test_generate_itineraries_with_insights_invalid_payload(client: TestClient):
    """Test with invalid payload structure"""
    payload = {"invalid": "payload"}

    response = client.post("/api/v1/insight/itineraries", json=payload)

    assert response.status_code == 422
