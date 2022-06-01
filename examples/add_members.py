from commonconf.backends import use_configparser_backend, use_django_backend
from commonconf import settings
from uw_gws import GWS
from uw_gws.models import GroupEntity
import argparse
import os


def add_members(group_id, file_path, act_as=None):
    try:
        use_django_backend()
    except ImportError:
        settings = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                'settings.cfg')
        use_configparser_backend(settings, 'GWS')

    members = []
    with open(file_path, 'r') as f:
        for line in f:
            members.append(GroupEntity(name=line.strip(),
                                       type=GroupEntity.UWNETID_TYPE))

    client = GWS(act_as=act_as, log_errors=True)
    errors = client.update_members(group_id, members)

    if len(errors):
        print(errors)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('group_id', help='Add members for group [group_id]')
    parser.add_argument('path', help='Path to file containing members, one per line')
    parser.add_argument('--act_as', default=None, help='User to act as when adding members')
    args = parser.parse_args()
    add_members(args.group_id, args.path, args.act_as)
