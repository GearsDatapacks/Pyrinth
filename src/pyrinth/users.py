"""Used for users."""

from datetime import datetime
import json
from typing import Optional
import requests as r
from pyrinth.exceptions import (
    InvalidParamError, InvalidRequestError,
    NoAuthorizationError, NotFoundError
)
from pyrinth.projects import Project
from pyrinth.models import UserModel


class User:
    """Contains information about users."""

    def __init__(self, user_model: 'UserModel') -> None:
        self.model = user_model
        if isinstance(user_model, dict):
            self.model = UserModel.from_json(user_model)

    def __repr__(self) -> str:
        return f'User: {self.model.username}'

    def get_auth(self) -> Optional[str]:
        """Gets the users authorization token."""
        return self.model.auth

    @staticmethod
    def from_json(json_: dict) -> 'User':
        """Utility Function."""
        result = User(UserModel.from_json(json_))

        return result

    def to_json(self) -> dict:
        """Utility Function."""
        result = {
            'id': self.model.id,
            'github_id': self.model.github_id,
            'username': self.model.username,
            'name': self.model.name,
            'email': self.model.email,
            'avatar_url': self.model.avatar_url,
            'bio': self.model.bio,
            'created': self.model.created,
            'role': self.model.role,
            'badges': self.model.badges,
            'payout_data': self.model.payout_data
        }

        return result

    @staticmethod
    def get(id_: str, auth=None) -> 'User':
        """Alternative method for Modrinth.get_user(id_, auth)."""
        from pyrinth.modrinth import Modrinth
        return Modrinth.get_user(id_, auth)

    def get_date_created(self) -> datetime:
        """
        Gets the date of when the user was created.

        Returns:
            datetime: The time of when the user was created
        """
        from pyrinth.util import format_time
        return format_time(self.model.created)

    def get_followed_projects(self) -> list['Project']:
        """
        Gets a users followed projects.

        Returns:
            list[Project]: The users followed projects
        """
        raw_response = r.get(
            f'https://api.modrinth.com/v2/user/{self.model.username}/follows',
            headers={
                'authorization': self.model.auth
            },
            timeout=60
        )

        if raw_response.status_code == 401:
            raise NoAuthorizationError(
                "No authorization to get this user's followed projects"
            )

        if raw_response.status_code == 404:
            raise NotFoundError("The requested user was not found")

        if not raw_response.ok:
            raise InvalidRequestError()

        followed_projects = []
        projects = json.loads(raw_response.content)
        for project in projects:
            followed_projects.append(Project(project))

        return followed_projects

    def get_notifications(self) -> list['User.Notification']:
        """
        Gets a users notifications.

        Returns:
            list[User.Notification]: The users notifications
        """
        raw_response = r.get(
            f'https://api.modrinth.com/v2/user/{self.model.username}/notifications',
            headers={
                'authorization': self.model.auth
            },
            timeout=60
        )

        if raw_response.status_code == 401:
            raise NoAuthorizationError(
                "No authorization to get this user's notifications"
            )

        if raw_response.status_code == 404:
            raise NotFoundError("The requested user was not found")

        if not raw_response.ok:
            raise InvalidRequestError()

        response = json.loads(raw_response.content)
        return [User.Notification(notification) for notification in response]

    def get_amount_of_projects(self) -> int:
        """
        Gets the amount of projects a user has.

        Returns:
            list[Project]: The users projects
        """
        projs = self.get_projects()

        return len(projs)

    def create_project(self, project_model, icon: Optional[str] = None) -> int:
        """
        Creates a project.

        Args:
            project_model (ProjectModel): The model of the project to create
            icon (str, optional): The path of the icon to use for the newly created project. NOT IMPLEMENTED

        Returns:
            int: If the project creation was successful
        """
        files = {"data": project_model.to_bytes()}
        if icon:
            files.update({"icon": open(icon, "rb")})

        raw_response = r.post(
            'https://api.modrinth.com/v2/project',
            files=files,
            headers={
                'authorization': self.model.auth
            },
            timeout=60
        )

        if raw_response.status_code == 401:
            raise NoAuthorizationError("No authorization to create a project")

        if not raw_response.ok:
            raise InvalidRequestError()

        return True

    def get_projects(self) -> list['Project']:
        """
        Gets a users projects.

        Returns:
            list[Project]: The users projects
        """
        raw_response = r.get(
            f'https://api.modrinth.com/v2/user/{self.model.id}/projects',
            timeout=60
        )

        if raw_response.status_code == 404:
            raise NotFoundError("The requested user was not found")

        if not raw_response.ok:
            raise InvalidRequestError()

        response = json.loads(raw_response.content)
        return [Project(project) for project in response]

    def follow_project(self, id_: str) -> int:
        """
        Follow a project.

        Args:
            id (str): The ID of the project to follow

        Returns:
            int: If the project follow was successful
        """
        raw_response = r.post(
            f'https://api.modrinth.com/v2/project/{id_}/follow',
            headers={
                'authorization': self.model.auth
            },
            timeout=60
        )

        if raw_response.status_code == 400:
            raise NotFoundError(
                "The requested project was not found or you are already following the specified project"
            )

        if raw_response.status_code == 401:
            raise NoAuthorizationError("No authorization to follow a project")

        if not raw_response.ok:
            raise InvalidRequestError()

        return True

    def unfollow_project(self, id_: str) -> int:
        """
        Unfollow a project.

        Args:
            id (str): The ID of the project to unfollow

        Returns:
            int: If the project unfollow was successful
        """
        raw_response = r.delete(
            f'https://api.modrinth.com/v2/project/{id_}/follow',
            headers={
                'authorization': self.model.auth
            },
            timeout=60
        )

        if raw_response.status_code == 400:
            raise NotFoundError(
                "The requested project was not found or you are not following the specified project"
            )

        if raw_response.status_code == 401:
            raise NoAuthorizationError(
                "No authorization to unfollow a project")

        if not raw_response.ok:
            raise InvalidRequestError()

        return True

    @staticmethod
    def from_auth(auth: str) -> 'User':
        """
        Gets a user from authorization token.

        Returns:
            User: The user that was found using the authorization token
        """
        raw_response = r.get(
            'https://api.modrinth.com/v2/user',
            headers={
                'authorization': auth
            },
            timeout=60
        )

        if raw_response.status_code == 401:
            raise InvalidParamError("No authorization token given")

        if not raw_response.ok:
            raise InvalidRequestError()

        response = raw_response.json()
        response.update({"authorization": auth})
        return User.from_json(response)

    @staticmethod
    def from_id(id_: str) -> 'User':
        """
        Gets a user from ID.

        Returns:
            User: The user that was found using the ID
        """
        raw_response = r.get(
            f'https://api.modrinth.com/v2/user/{id_}',
            timeout=60
        )

        if raw_response.status_code == 404:
            raise NotFoundError("The requested user was not found")

        if not raw_response.ok:
            raise InvalidRequestError()

        return User.from_json(raw_response.json())

    @staticmethod
    def from_ids(ids: list[str]) -> list['User']:
        """
        Gets a users from IDs.

        Returns:
            User: The users that were found using the IDs
        """
        raw_response = r.get(
            'https://api.modrinth.com/v2/users',
            params={
                'ids': json.dumps(ids)
            },
            timeout=60
        )

        if not raw_response.ok:
            raise InvalidRequestError()

        response = json.loads(raw_response.content)
        return [User.get(user['username']) for user in response]

    class Notification:
        """Used for the users notifications."""

        def __init__(self, notification_json: dict) -> None:
            self.id = notification_json['id']
            self.user_id = notification_json['user_id']
            self.type = notification_json['type']
            self.title = notification_json['title']
            self.text = notification_json['text']
            self.link = notification_json['link']
            self.read = notification_json['read']
            self.created = notification_json['created']
            self.actions = notification_json['actions']
            self.project_title = self.title.split('**')[1]

        def __repr__(self) -> str:
            return f"Notification: {self.text}"
