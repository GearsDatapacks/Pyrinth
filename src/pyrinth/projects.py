import requests as r
import json
from pyrinth.util import remove_null_values, json_to_query_params, to_sentence_case, remove_file_path
from typing import Optional, Union


class Project:
    def __init__(self, project_model) -> None:
        from pyrinth.models import ProjectModel
        if type(project_model) == dict:
            project_model = ProjectModel.from_json(project_model)
        self.project_model = project_model

    def __repr__(self) -> str:
        return f"Project: {self.project_model.title}"

    def get_latest_version(self, loaders: Optional[list[str]] = None, game_versions: Optional[list[str]] = None, featured: Optional[bool] = None) -> Union['Project.Version', None]:
        versions = self.get_versions(loaders, game_versions, featured)
        if versions:
            return versions[0]

        return None

    def get_specific_version(self, schematic_versioning: str) -> Union['Project.Version', None]:
        versions = self.get_versions()
        if versions:
            for version in versions:
                if version.version_model.version_number == schematic_versioning:
                    return version
        return None

    def get_oldest_version(self, loaders=None, game_versions=None, featured=None) -> Union['Project.Version', None]:
        versions = self.get_versions(loaders, game_versions, featured)
        if versions:
            return versions[-1]

        return None

    def get_id(self) -> str:
        return self.project_model.id

    def get_slug(self) -> str:
        return self.project_model.slug

    def get_name(self) -> str:
        return to_sentence_case(self.project_model.slug)

    def get_versions(self, loaders=None, game_versions=None, featured=None, auth: str = '') -> Union[list['Version'], None]:
        filters = {
            'loaders': loaders,
            'game_versions': game_versions,
            'featured': featured
        }

        filters = remove_null_values(filters)
        raw_response = r.get(
            f'https://api.modrinth.com/v2/project/{self.project_model.slug}/version',
            params=json_to_query_params(filters),
            headers={
                'authorization': auth
            }
        )

        if not raw_response.ok:
            print(f"Invalid Request : {raw_response.content!r} (get_versions)")
            return None

        response = json.loads(raw_response.content)
        if response == []:
            print("Project has no versions")
            return None

        return [self.Version(version) for version in response]

    @staticmethod
    def get_version(id: str) -> Union['Project.Version', None]:
        raw_response = r.get(
            f'https://api.modrinth.com/v2/version/{id}'
        )

        if not raw_response.ok:
            print(f"Invalid Request: {raw_response.content!r} (get_version)")
            return None

        response = json.loads(raw_response.content)
        return Project.Version(response)

    def create_version(self, auth: str, version_model) -> Union[int, None]:
        version_model.project_id = self.project_model.id

        files = {
            "data": version_model.to_bytes()
        }

        print(files)

        for file in version_model.files:
            files.update({remove_file_path(file): open(file, "rb").read()})

        raw_response = r.post(
            f'https://api.modrinth.com/v2/version',
            headers={
                "Authorization": auth
            },
            files=files
        )

        if not raw_response.ok:
            print(
                f"Invalid Request: {raw_response.content!r} (create_version)")
            return None

        return 1

    def change_icon(self, file_path: str, auth: str) -> Union[int, None]:
        raw_response = r.patch(
            f'https://api.modrinth.com/v2/project/{self.project_model.slug}/icon',

            params={
                "ext": file_path.split(".")[-1]
            },

            headers={
                "authorization": auth
            },

            data=open(file_path, "rb")
        )

        if not raw_response.ok:
            print(f"Invalid Request: {raw_response.content!r} (change_icon)")
            return None

        return 1

    def delete_icon(self, auth: str) -> Union[int, None]:
        raw_response = r.delete(
            f'https://api.modrinth.com/v2/project/{self.project_model.slug}/icon',
            headers={
                "authorization": auth
            }
        )

        if not raw_response.ok:
            print(f"Invalid Request: {raw_response.content!r} (delete_icon)")
            return None

        return 1

    def add_gallery_image(self, auth: str, image: 'Project.GalleryImage') -> Union[int, None]:
        raw_response = r.post(
            f'https://api.modrinth.com/v2/project/{self.project_model.slug}/gallery',
            headers={
                "authorization": auth
            },
            params=image.to_json(),
            data=open(image.file_path, "rb")
        )

        if not raw_response.ok:
            print(
                f"Invalid Request: {raw_response.content!r} (add_gallery_image)")
            return None

        return 1

    def modify_gallery_image(self, auth: str, url: str, featured: Optional[bool] = None, title: Optional[str] = None, description: Optional[str] = None, ordering: Optional[int] = None) -> Union[int, None]:
        modified_json = {
            'url': url,
            'featured': featured,
            'title': title,
            'description': description,
            'ordering': ordering
        }

        modified_json = remove_null_values(modified_json)
        if not modified_json:
            raise Exception("Please specify at least 1 optional argument.")

        raw_response = r.patch(
            f'https://api.modrinth.com/v2/project/{self.project_model.slug}/gallery',
            params=modified_json,
            headers={
                'authorization': auth
            }
        )

        if not raw_response.ok:
            print(
                f"Invalid Request: {raw_response.content!r} (modify_gallery_image)")
            return None

        return 1

    def delete_gallery_image(self, url: str, auth: str) -> Union[int, None]:
        if '-raw' in url:
            raise Exception(
                "Please use cdn.modrinth.com instead of cdn-raw.modrinth.com"
            )

        raw_response = r.delete(
            f'https://api.modrinth.com/v2/project/{self.project_model.slug}/gallery',
            headers={
                "authorization": auth
            },
            params={
                "url": url
            }
        )

        if not raw_response.ok:
            print(
                f"Invalid Request: {raw_response.content!r} (delete_gallery_image)")
            return None

        return 1

    def exists(self) -> bool:
        raw_response = r.get(
            f'https://api.modrinth.com/v2/project/{self.project_model.slug}/check'
        )

        response = json.loads(raw_response.content)
        return (True if response['id'] else False)

    def modify(self, auth: str, slug: Optional[str] = None, title: Optional[str] = None, description: Optional[str] = None, categories: Optional[list[str]] = None, client_side: Optional[str] = None, server_side: Optional[str] = None, body: Optional[str] = None, additional_categories: Optional[list[str]] = None, issues_url: Optional[str] = None, source_url: Optional[str] = None, wiki_url: Optional[str] = None, discord_url: Optional[str] = None, license_id: Optional[str] = None, license_url: Optional[str] = None, status: Optional[str] = None, requested_status: Optional[str] = None, moderation_message: Optional[str] = None, moderation_message_body: Optional[str] = None) -> Union[int, None]:
        modified_json = {
            'slug': slug,
            'title': title,
            'description': description,
            'categories': categories,
            'client_side': client_side,
            'server_side': server_side,
            'body': body,
            'additional_categories': additional_categories,
            'issues_url': issues_url,
            'source_url': source_url,
            'wiki_url': wiki_url,
            'discord_url': discord_url,
            'license_id': license_id,
            'license_url': license_url,
            'status': status,
            'requested_status': requested_status,
            'moderation_message': moderation_message,
            'moderation_message_body': moderation_message_body
        }

        modified_json = remove_null_values(modified_json)

        if not modified_json:
            raise Exception("Please specify at least 1 optional argument.")

        raw_response = r.patch(
            f'https://api.modrinth.com/v2/project/{self.project_model.slug}',
            data=json.dumps(modified_json),
            headers={
                'Content-Type': 'application/json',
                'authorization': auth
            }
        )

        if not raw_response.ok:
            print(f"Invalid Request: {raw_response.content!r} (modify)")
            return None

        return 1

    def delete(self, auth: str) -> Union[int, None]:
        raw_response = r.delete(
            f'https://api.modrinth.com/v2/project/{self.project_model.slug}',
            headers={
                'authorization': auth
            }
        )

        if not raw_response.ok:
            print(f"Invalid Request: {raw_response.content!r} (delete)")
            return None

        return 1

    def get_dependencies(self) -> Union[list['Project'], None]:
        raw_response = r.get(
            f'https://api.modrinth.com/v2/project/{self.project_model.slug}/dependencies'
        )

        if not raw_response.ok:
            print(
                f"Invalid Request : {raw_response.content!r} (get_dependencies)")
            return None

        response = json.loads(raw_response.content)
        return [Project(dependency) for dependency in response['projects']]

    class Version:
        def __init__(self, version_model) -> None:
            from pyrinth.models import VersionModel
            if type(version_model) == dict:
                version_model = VersionModel.from_json(version_model)
                self.version_model = version_model
            self.version_model = version_model

        def get_dependencies(self) -> list['Project.Dependency']:
            result = []
            for dependency in self.version_model.dependencies:
                result.append(Project.Dependency.from_json(dependency))
            return result

        def get_files(self) -> list['Project.File']:
            result = []
            for file in self.version_model.files:
                result.append(Project.File.from_json(file))
            return result

        def get_project(self) -> 'Project':
            from pyrinth.modrinth import Modrinth
            return Modrinth.get_project(self.version_model.project_id)

        def get_primary_files(self) -> list['Project.File']:
            result = []
            for file in self.get_files():
                if file.primary:
                    result.append(file)
            return result

        def __repr__(self) -> str:
            return f"Version: {self.version_model.name}"

    class GalleryImage:
        def __init__(self, file_path: str, featured: bool, title: str, description, ordering: int = 0) -> None:
            self.file_path = file_path
            self.ext = file_path.split(".")[-1]
            self.featured = str(featured).lower()
            self.title = title
            self.description = description
            self.ordering = ordering

        @staticmethod
        def from_json(json: dict) -> 'Project.GalleryImage':
            result = Project.GalleryImage(
                json['url'], json['featured'], json['title'],
                json['description'], json['ordering']
            )

            return result

        def to_json(self) -> dict:
            result = {
                "ext": self.ext,
                "featured": self.featured,
                "title": self.title,
                "description": self.description,
                "ordering": self.ordering
            }
            result = remove_null_values(result)
            return result

    class File:
        def __init__(self, hashes: dict[str, str], url: str, filename: str, primary: str, size: int, file_type: str) -> None:
            self.hashes = hashes
            self.url = url
            self.filename = filename
            self.primary = primary
            self.size = size
            self.file_type = file_type
            self.extension = filename.split('.')[-1]

        def is_resourcepack(self):
            if self.file_type == None:
                return False
            return True

        @staticmethod
        def from_json(json: dict) -> 'Project.File':
            result = Project.File(
                json['hashes'],
                json['url'],
                json['filename'],
                json['primary'],
                json['size'],
                json['file_type']
            )
            return result

        def __repr__(self) -> str:
            return f"File: {self.filename}"

    class License:
        def __init__(self, id: str, name: str, url: str) -> None:
            self.id = id
            self.name = name
            self.url = url

        @staticmethod
        def from_json(json: dict) -> 'Project.License':
            result = Project.License(
                json['id'],
                json['name'],
                json['url']
            )

            return result

        def __repr__(self) -> str:
            return f"License: {self.name if self.name else self.id}"

    class Donation:
        def __init__(self, id: str, platform: str, url: str) -> None:
            self.id = id
            self.platform = platform
            self.url = url

        @staticmethod
        def from_json(json: dict) -> 'Project.Donation':
            result = Project.Donation(
                json['id'],
                json['platform'],
                json['url']
            )

            return result

        def __repr__(self) -> str:
            return f"Donation: {self.platform}"

    class Dependency:
        def __init__(self, dependency_type, id, dependency_option):
            from pyrinth.modrinth import Modrinth
            self.dependency_type = dependency_type
            self.id = id
            if dependency_type == "project":
                self.id = Modrinth.get_project(self.id).get_id()
            self.dependency_option = dependency_option

        def to_json(self):
            result = {
                "version_id": None,
                "project_id": None,
                "file_name": None,
                "dependency_type": self.dependency_option
            }
            if self.dependency_type == "project":
                result.update({"project_id": self.id})
            elif self.dependency_type == "version":
                result.update({"version_id": self.id})
            return result

        def from_json(json: dict) -> 'Project.Dependency':
            dependency_type = "project"
            id = json['project_id']
            if json['version_id']:
                dependency_type = "version"
                id = json['version_id']

            result = Project.Dependency(
                dependency_type,
                id,
                json['dependency_type']
            )

            return result

        def get_project(self):
            from pyrinth.modrinth import Modrinth
            if self.dependency_type == "version":
                version = Modrinth.get_version(self.id)
                return version.get_project()
            return Modrinth.get_project(self.id)

        def is_required(self) -> bool:
            return (True if self.dependency_option == "required" else False)

        def is_optional(self) -> bool:
            return (True if self.dependency_option == "optional" else False)

        def is_incompatible(self) -> bool:
            return (True if self.dependency_option == "incompatible" else False)
