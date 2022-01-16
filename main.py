import json

import requests
import argparse
import docker
from pathlib import Path
from docker.errors import DockerException

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


def load_image_build_configs(config_root: str) -> str:
    """
    Walk a directory structure and build a dictionary that contains all the
    information needed to trigger the build of the Dockerfiles that are found
    :param config_root: The root directory to look for image configs
    """
    image_build_config: list = []
    for path in Path(config_root).rglob('Dockerfile'):
        # Check for a version file, two levels up, otherwise assume latest
        version_file_path = f'{path.resolve().parents[1]}/version'
        docker_file_path = str(path.resolve())
        version = 'latest'
        if Path(version_file_path).exists():
            with open(version_file_path, 'r') as file:
                version = file.read().rstrip()
        image_build_config.append(dict({'Dockerfile': docker_file_path, 'version': version}))

    return json.dumps(image_build_config)


def build_image(docker_file: str, build_args: str) -> bool:
    """
    Use a docker client to trigger an image build based on the inputs
    :param build_args: Key value pairs key=value,key=value... to be passed to the build process
    :param docker_file: Path to the Dockerfile
    :return: bool representing a successful or failed build
    """
    docker_client = docker.from_env()

    print(f'Building Image from {docker_file} with build args {build_args}.')

    dockerfile_directory = str(Path(docker_file).parent)
    build_args_dict = dict(x.split("=") for x in build_args.split(","))

    try:
        build_result = docker_client.images.build(path=dockerfile_directory,
                                                  buildargs=build_args_dict,
                                                  tag=build_args_dict.get('version'))
    except DockerException as error:
        print('Error building Dockerfile:\n'
              f'{error}')
        return False

    for log in build_result[1]:
        print(log, flush=True)
    docker_client.close()

    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Docker Image Build Management')
    parser.add_argument('--get-build-configs', action='store_true', required=False,
                        help='Find all the Dockerfiles to build and return them as a list of dicts')
    parser.add_argument('--build-image', action='store_true',
                        help='Build an image based on the values of required arguments '
                             '--docker-file and --build-args.')
    parser.add_argument('--docker-file',
                        help='Path to the Dockerfile to build, requires --build-image and --build-args')
    parser.add_argument('--build-args',
                        help='Key value pairs representing build arguments to docker build.\n'
                             'Expected format: key=value,key=value,...\n'
                             'Requires --build-image and --docker-file.')

    args = parser.parse_args()

    if args.get_build_configs:
        print(load_image_build_configs('dockerfiles'))
    elif args.build_image and (args.docker_file is None or args.build_args is None):
        parser.error("--build-image requires --docker-file and --build-args.")
    elif args.build_image and args.docker_file and args.build_args:
        print(args.build_image)
        build_image(docker_file=args.docker_file, build_args=args.build_args)
