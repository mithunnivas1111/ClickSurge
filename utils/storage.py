"""
Storage Utility — CRUD for Action Items and Audit History

Uses JSON files for persistence (no database needed).
Files stored in /reports/ folder alongside CSV exports.
"""
import json
import os
from datetime import datetime


ACTIONS_FILE  = 'reports/action_items.json'
HISTORY_FILE  = 'reports/audit_history.json'


def _load(filepath):
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception:
        return []


def _save(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)


# ─────────────────────────────────────────────
# ACTION ITEMS — CRUD
# ─────────────────────────────────────────────

def get_all_actions():
    return _load(ACTIONS_FILE)


def add_action(page, issue_type, priority, description, assigned_to='', due_date=''):
    actions = _load(ACTIONS_FILE)
    action = {
        'id':          f"ACT-{len(actions)+1:04d}",
        'page':        page,
        'issue_type':  issue_type,
        'priority':    priority,
        'description': description,
        'assigned_to': assigned_to,
        'due_date':    due_date,
        'status':      'To Do',
        'notes':       '',
        'created_at':  datetime.now().isoformat(),
        'updated_at':  datetime.now().isoformat(),
    }
    actions.append(action)
    _save(ACTIONS_FILE, actions)
    return action


def update_action(action_id, **kwargs):
    actions = _load(ACTIONS_FILE)
    for action in actions:
        if action['id'] == action_id:
            for k, v in kwargs.items():
                action[k] = v
            action['updated_at'] = datetime.now().isoformat()
            break
    _save(ACTIONS_FILE, actions)


def delete_action(action_id):
    actions = _load(ACTIONS_FILE)
    actions = [a for a in actions if a['id'] != action_id]
    _save(ACTIONS_FILE, actions)


def get_actions_by_status(status):
    return [a for a in get_all_actions() if a['status'] == status]


def get_actions_by_page(page_url):
    return [a for a in get_all_actions() if a['page'] == page_url]


def get_action_stats():
    actions = get_all_actions()
    if not actions:
        return {'total': 0, 'todo': 0, 'in_progress': 0, 'done': 0, 'ignored': 0}
    return {
        'total':       len(actions),
        'todo':        len([a for a in actions if a['status'] == 'To Do']),
        'in_progress': len([a for a in actions if a['status'] == 'In Progress']),
        'done':        len([a for a in actions if a['status'] == 'Done']),
        'ignored':     len([a for a in actions if a['status'] == 'Ignored']),
    }


# ─────────────────────────────────────────────
# AUDIT HISTORY — CRUD
# ─────────────────────────────────────────────

def save_audit_snapshot(stats, label=''):
    history = _load(HISTORY_FILE)
    snapshot = {
        'id':         f"AUD-{len(history)+1:04d}",
        'label':      label or f"Audit {datetime.now().strftime('%b %d %Y %H:%M')}",
        'timestamp':  datetime.now().isoformat(),
        'stats':      stats,
    }
    history.append(snapshot)
    _save(HISTORY_FILE, history)
    return snapshot


def get_audit_history():
    return _load(HISTORY_FILE)


def delete_audit(audit_id):
    history = _load(HISTORY_FILE)
    history = [h for h in history if h['id'] != audit_id]
    _save(HISTORY_FILE, history)


def get_latest_audit():
    history = _load(HISTORY_FILE)
    return history[-1] if history else None


def get_trend_data():
    """Return list of (timestamp, total_issues, estimated_gain) for trend chart."""
    history = _load(HISTORY_FILE)
    return [
        {
            'label':           h['label'],
            'timestamp':       h['timestamp'],
            'total_issues':    h['stats'].get('total_opportunities', 0),
            'high_priority':   h['stats'].get('high_priority', 0),
            'estimated_gain':  h['stats'].get('total_estimated_gain', 0),
        }
        for h in history
    ]