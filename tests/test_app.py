"""
Backend tests for Mergington High School Activities API
Tests follow the AAA (Arrange-Act-Assert) pattern
"""

import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """
        Arrange: No setup needed (activities are predefined in app)
        Act: GET /activities
        Assert: Response contains activities with correct structure
        """
        # Arrange
        # Activities exist in the app; verify we get at least 3 core activities
        core_activities = {"Chess Club", "Programming Class", "Gym Class"}

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        activities = response.json()
        
        # Verify core activities are present
        assert core_activities.issubset(set(activities.keys()))
        
        # Verify each activity has required fields
        for activity_name, activity_details in activities.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)

    def test_get_activities_structure(self, client, sample_activity):
        """
        Arrange: Use Chess Club as sample activity
        Act: GET /activities and extract Chess Club data
        Assert: Verify structure and sample data
        """
        # Arrange
        expected_fields = {"description", "schedule", "max_participants", "participants"}

        # Act
        response = client.get("/activities")

        # Assert
        activities = response.json()
        chess_club = activities[sample_activity]
        assert set(chess_club.keys()) == expected_fields
        assert isinstance(chess_club["max_participants"], int)
        assert isinstance(chess_club["participants"], list)


class TestRootRedirect:
    """Tests for GET / endpoint"""

    def test_root_serves_index_html(self, client):
        """
        Arrange: No setup needed
        Act: GET /
        Assert: Response returns index.html content
        """
        # Arrange & Act
        response = client.get("/")

        # Assert
        assert response.status_code == 200
        # Verify it's HTML content
        assert "text/html" in response.headers.get("content-type", "") or b"<!DOCTYPE" in response.content

    def test_root_redirect_follows_to_index(self, client):
        """
        Arrange: No setup needed
        Act: GET / (follow redirects)
        Assert: Final response is 200 with HTML content
        """
        # Arrange & Act
        response = client.get("/", follow_redirects=True)

        # Assert
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_valid_student(self, client, sample_activity, sample_email):
        """
        Arrange: Prepare valid activity name and email
        Act: POST signup endpoint
        Assert: Response is 200 and student is added to participants
        """
        # Arrange
        # Get initial participants count
        initial_response = client.get("/activities")
        initial_participants = initial_response.json()[sample_activity]["participants"].copy()

        # Act
        response = client.post(
            f"/activities/{sample_activity}/signup",
            params={"email": sample_email}
        )

        # Assert
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        
        # Verify student was added
        updated_response = client.get("/activities")
        updated_participants = updated_response.json()[sample_activity]["participants"]
        assert sample_email in updated_participants
        assert len(updated_participants) == len(initial_participants) + 1

    def test_signup_activity_not_found(self, client, nonexistent_activity, sample_email):
        """
        Arrange: Prepare nonexistent activity name
        Act: POST signup with invalid activity
        Assert: Response is 404 with error message
        """
        # Arrange
        # Act
        response = client.post(
            f"/activities/{nonexistent_activity}/signup",
            params={"email": sample_email}
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_duplicate_student(self, client, sample_activity):
        """
        Arrange: Use a unique email not in pre-populated participants
        Act: POST signup endpoint twice with same email
        Assert: First signup succeeds (200), second fails (400)
        """
        # Arrange
        unique_email = "duplicate_test@mergington.edu"
        
        # Act
        first_response = client.post(
            f"/activities/{sample_activity}/signup",
            params={"email": unique_email}
        )

        second_response = client.post(
            f"/activities/{sample_activity}/signup",
            params={"email": unique_email}
        )

        # Assert
        assert first_response.status_code == 200
        assert second_response.status_code == 400
        assert "already" in second_response.json()["detail"].lower()

    def test_signup_multiple_students_same_activity(self, client, sample_activity):
        """
        Arrange: Prepare two different emails
        Act: Sign up both students for the same activity
        Assert: Both signups succeed and both are in participants
        """
        # Arrange
        email1 = "student1@mergington.edu"
        email2 = "student2@mergington.edu"

        # Act
        response1 = client.post(
            f"/activities/{sample_activity}/signup",
            params={"email": email1}
        )
        response2 = client.post(
            f"/activities/{sample_activity}/signup",
            params={"email": email2}
        )

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify both are in participants
        activities_response = client.get("/activities")
        participants = activities_response.json()[sample_activity]["participants"]
        assert email1 in participants
        assert email2 in participants


class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/participants endpoint"""

    def test_remove_participant_success(self, client, sample_activity, sample_email):
        """
        Arrange: Sign up a student, then remove them
        Act: DELETE participant from activity
        Assert: Response is 200 and student is removed from participants
        """
        # Arrange
        # First, sign up the student
        client.post(
            f"/activities/{sample_activity}/signup",
            params={"email": sample_email}
        )

        # Act
        response = client.delete(
            f"/activities/{sample_activity}/participants",
            params={"email": sample_email}
        )

        # Assert
        assert response.status_code == 200
        assert "Removed" in response.json()["message"]
        
        # Verify student was removed
        updated_response = client.get("/activities")
        participants = updated_response.json()[sample_activity]["participants"]
        assert sample_email not in participants

    def test_remove_participant_activity_not_found(self, client, nonexistent_activity, sample_email):
        """
        Arrange: Prepare nonexistent activity name
        Act: DELETE from nonexistent activity
        Assert: Response is 404
        """
        # Arrange
        # Act
        response = client.delete(
            f"/activities/{nonexistent_activity}/participants",
            params={"email": sample_email}
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_remove_participant_not_found(self, client, sample_activity):
        """
        Arrange: Prepare email that was never signed up
        Act: DELETE nonexistent participant from activity
        Assert: Response is 404
        """
        # Arrange
        email = "never_signed_up@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{sample_activity}/participants",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Participant not found"

    def test_remove_different_participants_independently(self, client, sample_activity):
        """
        Arrange: Sign up two students, remove one
        Act: DELETE one participant from activity
        Assert: First participant removed, second remains
        """
        # Arrange
        email1 = "student1@mergington.edu"
        email2 = "student2@mergington.edu"
        
        client.post(f"/activities/{sample_activity}/signup", params={"email": email1})
        client.post(f"/activities/{sample_activity}/signup", params={"email": email2})

        # Act
        response = client.delete(
            f"/activities/{sample_activity}/participants",
            params={"email": email1}
        )

        # Assert
        assert response.status_code == 200
        
        # Verify only first was removed
        activities_response = client.get("/activities")
        participants = activities_response.json()[sample_activity]["participants"]
        assert email1 not in participants
        assert email2 in participants
