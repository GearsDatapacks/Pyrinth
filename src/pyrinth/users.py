from typing import Sequence, Union
import requests as r
import json
from pyrinth.projects import Project


class User:
    def __init__(self, username: str, authorization: str = '', ignore_warning: bool = False) -> None:
        self.auth = authorization
        if self.auth != '':
            self.raw_response = r.get(
                f'https://api.modrinth.com/v2/user',
                headers={
                    'authorization': self.auth
                }
            )
            if not self.raw_response.ok:
                raise Exception("Invalid auth token")

        if self.auth == '':
            self.raw_response = r.get(
                f'https://api.modrinth.com/v2/user/{username}'
            )
            if not ignore_warning:
                print('[WARNING] Some functions won\'t work without an auth key')

        self.response = json.loads(self.raw_response.content)
        self.username = self.response['username']
        self.id = self.response['id']
        self.github_id = self.response['github_id']
        self.name = self.response['name']
        self.email = self.response['email']
        self.avatar_url = self.response['avatar_url']
        self.bio = self.response['bio']
        self.created = self.response['created']
        self.role = self.response['role']
        self.badges = self.response['badges']
        self.payout_data = self.response['payout_data']

    def get_followed_projects(self) -> Union[list['Project'], None]:
        if self.auth == '':
            raise Exception("get_followed_projects needs an auth token.")
        raw_response = r.get(
            f'https://api.modrinth.com/v2/user/{self.username}/follows',
            headers={
                'authorization': self.auth
            }
        )

        if not raw_response.ok:
            print(
                f"Invalid Request: {json.loads(raw_response.content)['description']}")
            return None

        followed_projects = []
        projects = json.loads(raw_response.content)
        for project in projects:
            followed_projects.append(Project(project))

        return followed_projects

    def get_notifications(self) -> Union[list['User.Notification'], None]:
        raw_response = r.get(
            f'https://api.modrinth.com/v2/user/{self.username}/notifications',
            headers={
                'authorization': self.auth
            }
        )

        if not raw_response.ok:
            print(
                f"Invalid Request: {json.loads(raw_response.content)['description']}")
            return None

        response = json.loads(raw_response.content)
        return [User.Notification(notification) for notification in response]

    def get_amount_of_projects(self) -> Union[int, list['Project']]:
        projs = self.get_projects()

        if not projs:
            return 0

        return projs

    def create_project(self, project_model, icon: str = '') -> Union[int, None]:
        raw_response = r.post(
            'https://api.modrinth.com/v2/project',
            files={
                "data": project_model.to_bytes()
            },
            headers={
                'Authorization': self.auth
            }
        )

        if not raw_response.ok:
            print(
                f"Invalid Request: {json.loads(raw_response.content)['description']}"
            )
            return None

        return 1

    def get_projects(self) -> Union[list['Project'], None]:
        raw_response = r.get(
            f'https://api.modrinth.com/v2/user/{self.id}/projects'
        )

        if not raw_response.ok:
            print(
                f"Invalid Request: {json.loads(raw_response.content)['description']}"
            )
            return None

        response = json.loads(raw_response.content)
        return [Project(project) for project in response]

    def follow_project(self, id: str) -> Union[int, None]:
        raw_response = r.post(
            f'https://api.modrinth.com/v2/project/{id}/follow',
            headers={
                'authorization': self.auth
            }
        )

        if not raw_response.ok:
            print(
                f"Invalid Request: {json.loads(raw_response.content)['description']}")
            return None

        return 1

    def unfollow_project(self, id: str) -> Union[int, None]:
        raw_response = r.delete(
            f'https://api.modrinth.com/v2/project/{id}/follow',
            headers={
                'authorization': self.auth
            }
        )

        if not raw_response.ok:
            print(
                f"Invalid Request: {json.loads(raw_response.content)['description']}")
            return None

        return 1

    @staticmethod
    def from_auth(auth: str) -> Union['User', None]:
        raw_response = r.get(
            f'https://api.modrinth.com/v2/user',
            headers={
                'authorization': auth
            }
        )

        if not raw_response.ok:
            print(
                f"Invalid Request: {json.loads(raw_response.content)['description']}")
            return None

        response = json.loads(raw_response.content)
        return User(response['username'], auth, ignore_warning=True)

    @staticmethod
    def from_id(id: str) -> Union['User', None]:
        raw_response = r.get(
            f'https://api.modrinth.com/v2/user/{id}'
        )

        if not raw_response.ok:
            print(
                f"Invalid Request: {json.loads(raw_response.content)['description']}")
            return None

        response = json.loads(raw_response.content)
        return User(response['username'], ignore_warning=True)

    @staticmethod
    def from_ids(ids: list[str]) -> list['User']:
        raw_response = r.get(
            'https://api.modrinth.com/v2/users',
            params={
                'ids': json.dumps(ids)
            }
        )

        response = json.loads(raw_response.content)
        return [User(user['username']) for user in response]

    class Notification:

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

    class TeamMember:
        def __init__(self, team_member_json: dict) -> None:
            self.team_id = team_member_json['team_id']
            self.user = User(
                team_member_json['user']['username'],
                ignore_warning=True
            )

            self.role = team_member_json['role']
            self.permissions = team_member_json['permissions']
            self.accepted = team_member_json['accepted']
            self.payouts_split = team_member_json['payouts_split']
            self.ordering = team_member_json['ordering']

        def __repr__(self) -> str:
            return f"TeamMember: {self.user.username}"
