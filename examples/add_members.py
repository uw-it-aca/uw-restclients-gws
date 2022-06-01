from commonconf.backends import use_configparser_backend, use_django_backend
from commonconf import settings
import argparse
import os


def add_members(group_id, file_path, act_as=None):
    try:
        use_django_backend()
    except ImportError:
        settings = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                'settings.cfg')
        use_configparser_backend(settings, 'GWS')

    from uw_gws import GWS

    members = []
    with open(file_path, 'r') as f:
        for line in f:
            members.append(line.strip())

    client = GWS(act_as=act_as, log_errors=True)
    client.add_members(group_id, members)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('group_id', help='Add members for group [group_id]')
    parser.add_argument('path', help='Path to file containing members, one per line')
    parser.add_argument('--act_as', default=None, help='User to act as when adding members')
    args = parser.parse_args()
    add_members(args.group_id, args.path, args.act_as)
