from types import SimpleNamespace

import pytest

from app import create_app
from app.navigation_models import NavigationNode
from app.navigation_state import NavigationStateMachine


@pytest.fixture(scope='module')
def app_context():
    app = create_app({'TESTING': True})
    app.config['SECRET_KEY'] = 'test-navigation-secret'
    with app.test_request_context():
        yield app


@pytest.fixture
def override_navigation_tree(monkeypatch):
    tree = [
        NavigationNode(key='company_info', name='会社情報', endpoint='company.info'),
        NavigationNode(
            key='filings_group',
            name='申告',
            children=[{'key': 'corporate_tax_calc', 'name': '法人税計算', 'endpoint': 'company.info'}],
        ),
    ]
    monkeypatch.setattr('app.navigation_state.navigation_tree', tree)
    monkeypatch.setattr('app.navigation_models.NavigationNode.get_url', lambda self: f"/{self.key}")
    return tree


def test_state_machine_marks_completed_from_session(app_context, override_navigation_tree, monkeypatch):
    monkeypatch.setattr('app.navigation_state.current_user', SimpleNamespace(company=None, is_admin=False))
    from flask import session

    session['wizard_completed_steps'] = ['company_info']

    monkeypatch.setattr('app.navigation_state.NavigationStateMachine._compute_skipped', lambda self, company_id: set())
    monkeypatch.setattr('app.navigation_state.NavigationStateMachine._augment_completed', lambda self, company_id, user_id: set())

    machine = NavigationStateMachine('company_info')
    state = machine.compute()
    assert 'company_info' in state.completed_keys
    assert state.items[0]['is_active'] is True
    # filing group should have corporate tax pruned for non-admin
    assert state.items[1]['children'] == []


def test_mark_and_unmark_completed_step(app_context, override_navigation_tree, monkeypatch):
    monkeypatch.setattr('app.navigation_state.current_user', SimpleNamespace(company=None, is_admin=False))
    from flask import session

    session['wizard_completed_steps'] = []
    machine = NavigationStateMachine('company_info')
    machine.mark_completed('company_info')
    assert session['wizard_completed_steps'] == ['company_info']

    machine.unmark_completed('company_info')
    assert session['wizard_completed_steps'] == []