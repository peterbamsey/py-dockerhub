import requests
import argparse
from pathlib import Path

QUERY_URL = "https://index.docker.io"
AUTH_URL = "https://auth.docker.io"


def get_auth_token(image_name: str, auth_url: str) -> str:
    """
    Get an authentication token for dockerhub
    :param image_name: The name of the image - used in the request for an auth token
    :param auth_url: The URL of the authentication service
    """
    payload = {
        'service': 'registry.docker.io',
        'scope': f'repository:library/{image_name}:pull'
    }

    request = requests.get(f'{auth_url}/token', params=payload)

    if not request.status_code == 200:
        raise Exception(f'Error getting auth token: {request.status_code}')

    return request.json().get('token', None)


def get_image_tags(query_url: str, auth_token: str, image_name: str) -> list:
    """
    Get all the tags for a particular image
    :param image_name: Name of the image to retrieve tags for
    :param auth_token: Authentication token
    :param query_url:  URL to query
    :return dict: All the tags for this image
    """
    headers: dict = {'Authorization': f'Bearer {auth_token}'}
    full_url: str = f'{query_url}/v2/library/{image_name}/tags/list'

    request = requests.get(url=full_url, headers=headers)

    return request.json().get('tags', 'None')


def load_image_build_configs(config_root: str) -> dict:
    """
    Walk a directory structure and build a dictionary that contains all the information needed to trigger the build of
    all the Dockerfiles that are found
    :param config_root: The root directory to look for image configs
    """
    image_build_config: dict = {}
    counter: int = 0
    for path in Path(config_root).rglob('Dockerfile'):
        # Check for a version file, two levels up, otherwise assume latest
        version_file_path = f'{path.resolve().parents[1]}/version'
        if Path(version_file_path).exists():
            with open(version_file_path, 'r') as file:
                image_build_config[str(path.resolve())] = file.read().rstrip()
        else:
            image_build_config[str(path.resolve())] = 'latest'

    return image_build_config


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('image', help='The name of the image to retrieve tags for')
    args = parser.parse_args()

    auth_token = get_auth_token(image_name=args.image, auth_url=AUTH_URL)
    tags = get_image_tags(query_url=QUERY_URL, auth_token=auth_token, image_name=args.image)
    print(tags)
    print(load_image_build_configs('dockerfiles'))
