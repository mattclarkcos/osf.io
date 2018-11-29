import pytest

from api.base.settings.defaults import API_BASE
from osf.models import OSFGroup
from osf_tests.factories import (
    AuthUserFactory,
    OSFGroupFactory,
)

@pytest.fixture()
def user():
    return AuthUserFactory()

@pytest.fixture()
def manager():
    return AuthUserFactory()

@pytest.fixture()
def member():
    return AuthUserFactory()

@pytest.fixture()
def osf_group(manager, member):
    group = OSFGroupFactory(name='Platform Team', creator=manager)
    group.make_member(member)
    return group

@pytest.mark.django_db
class TestOSFGroupList:

    @pytest.fixture()
    def url(self):
        return '/{}osf_groups/'.format(API_BASE)

    def test_return(self, app, member, manager, user, osf_group, url):
        # test nonauthenticated
        res = app.get(url)
        assert res.status_code == 200
        data = res.json['data']
        assert len(data) == 1
        assert data[0]['id'] == osf_group._id
        assert data[0]['type'] == 'osf_groups'
        assert data[0]['attributes']['name'] == osf_group.name

        # test authenticated user
        res = app.get(url, auth=user)
        assert res.status_code == 200
        data = res.json['data']
        assert len(data) == 1
        assert data[0]['id'] == osf_group._id

        # test authenticated member
        res = app.get(url, auth=member)
        assert res.status_code == 200
        data = res.json['data']
        assert len(data) == 1
        assert data[0]['id'] == osf_group._id

        # test authenticated manager
        res = app.get(url, auth=manager)
        assert res.status_code == 200
        data = res.json['data']
        assert len(data) == 1
        assert data[0]['id'] == osf_group._id

    def test_groups_filter(self, app, member, manager, user, osf_group, url):
        second_group = OSFGroupFactory(name='Apples')
        res = app.get(url + '?filter[name]=Platform')
        assert res.status_code == 200
        data = res.json['data']
        assert len(data) == 1
        assert data[0]['id'] == osf_group._id

        res = app.get(url + '?filter[name]=Apple')
        assert res.status_code == 200
        data = res.json['data']
        assert len(data) == 1
        assert data[0]['id'] == second_group._id

        res = app.get(url + '?filter[bad_field]=Apple', expect_errors=True)
        assert res.status_code == 400


@pytest.mark.django_db
class TestOSFGroupCreate:
    @pytest.fixture()
    def url(self):
        return '/{}osf_groups/'.format(API_BASE)

    @pytest.fixture()
    def simple_payload(self):
        return {
            'data': {
                'type': 'osf_groups',
                'attributes': {
                    'name': 'My New Lab'
                },
            }
        }

    def test_create_osf_group(self, app, url, manager, simple_payload):
        # Nonauthenticated
        res = app.post_json_api(url, simple_payload, expect_errors=True)
        assert res.status_code == 401

        # Authenticated
        res = app.post_json_api(url, simple_payload, auth=manager.auth)
        assert res.status_code == 201
        assert res.json['data']['type'] == 'osf_groups'
        assert res.json['data']['attributes']['name'] == 'My New Lab'
        group = OSFGroup.objects.get(_id=res.json['data']['id'])
        assert group.creator_id == manager.id
        assert group.has_permission(manager, 'manage') is True
        assert group.has_permission(manager, 'member') is True

    def test_create_osf_group_validation_errors(self, app, url, manager, simple_payload):
        # Need data key
        res = app.post_json_api(url, simple_payload['data'], auth=manager.auth, expect_errors=True)
        assert res.status_code == 400
        assert res.json['errors'][0]['detail'] == 'Request must include /data.'

        # Incorrect type
        simple_payload['data']['type'] = 'incorrect_type'
        res = app.post_json_api(url, simple_payload, auth=manager.auth, expect_errors=True)
        assert res.status_code == 409

        # Required name field
        payload = {
            'data': {
                'type': 'osf_groups'
            }
        }
        res = app.post_json_api(url, payload, auth=manager.auth, expect_errors=True)
        assert res.status_code == 400
        assert res.json['errors'][0]['detail'] == 'This field is required.'
