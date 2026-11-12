"""Extracted candidate timing proposals; every outcome still needs evaluation.

Only the module description differs from the local planning implementation.
The event-constraint field native_conditions is retained as an opaque input.
"""
from copy import deepcopy


def _late_retreat(plan, result):
    d = result.get('diagnostic') or {}
    if not d.get('tactical_evidence') or result.get('feasible') or result.get('error'):
        return None
    if plan.get('interaction_policies') or plan.get('entities') or any(
            s['kind'] == 'MoveCamera' for s in plan['steps']):
        return None
    pending = d.get('pending_deployment') or {}
    leak = d.get('first_leak') or {}; before = leak.get('before') or {}
    start = leak.get('from_frame')
    if pending.get('wait_kind') != 'deployment_unavailable' or type(start) is not int:
        return None
    steps = plan['steps']
    target = next((s for s in steps if s['id'] == pending.get('step_id')), None)
    if not target or target['kind'] != 'Deploy':
        return None
    role = target['task']; cid = plan['bindings'][role]
    if pending.get('source_id', cid) != cid:
        return None
    cards = [c for c in before.get('cards', []) if c.get('id') == cid]
    if len(cards) != 1 or before.get('dp', -1) < cards[0].get('cost', float('inf')):
        return None
    if any(a.get('source_id') == cid and a.get('alive') for a in before.get('characters', [])):
        return None
    prior = [s for s in steps[:steps.index(target)] if s.get('task') == role and s['kind'] in ('Deploy', 'Retreat')]
    if not prior or prior[-1]['kind'] != 'Retreat':
        return None
    retreat = prior[-1]
    if retreat.get('native_conditions') or retreat.get('cost_changes'):
        return None
    events = [a for a in result.get('trace', []) if a.get('source_id') == cid and a['kind'] in ('spawn', 'withdraw')]
    previous = [a for a in events if a.get('frame', start + 1) <= start]
    arrival = next((a for a in events if a.get('step_id') == target['id'] and a['kind'] == 'spawn'), None)
    if not previous or previous[-1]['kind'] != 'withdraw' or previous[-1].get('step_id') != retreat['id']:
        return None
    if not arrival or arrival['frame'] <= start:
        return None
    observation = dict(waiting_step=target['id'], first_leak_frame=start,
                       recorded_arrival=arrival['frame'], source_id=cid)
    return retreat, observation


def retreat_wait_proposals(plan, result):
    late = _late_retreat(plan, result)
    if late is None:
        return []
    retreat, observation = late; wait = retreat.get('pre_frames', 0)
    if type(wait) is not int or wait <= 0:
        return []
    proposals = []
    for value in dict.fromkeys((wait // 2, 0)):
        candidate = deepcopy(plan)
        next(s for s in candidate['steps'] if s['id'] == retreat['id'])['pre_frames'] = value
        candidate.setdefault('adapted_source_gates', []).append(dict(
            step_id=retreat['id'], field='pre_frames', original=wait, candidate=value,
            observation=observation,
            scope='Earlier strategic retreat hypothesis; all actions, other gates and 0.1-second input delay retained; cooldown causality unproven'))
        proposals.append(candidate)
    return proposals


def retreat_order_proposals(plan, result):
    late = _late_retreat(plan, result)
    if late is None:
        return []
    retreat, observation = late; steps = plan['steps']; index = steps.index(retreat)
    positions = []
    for i in range(index-1, -1, -1):
        step = steps[i]
        if (step['kind'] not in ('Deploy','Output') or step.get('task') == retreat['task']
                or any(step.get(k) for k in ('kills','costs','cost_changes','pre_frames','post_frames','native_conditions'))
                or step.get('cooling_required',-1) not in (-1,None)):
            break
        positions.append(i)
    proposals = []
    for position in dict.fromkeys(reversed(positions)):
        candidate = deepcopy(plan)
        candidate['steps'].insert(position, candidate['steps'].pop(index))
        candidate.setdefault('adapted_source_order', []).append(dict(step_id=retreat['id'],
            before_step=steps[position]['id'], observation=observation,
            scope='Earlier retreat before independent deployment; preserve all actions and gates; outcome unproven'))
        proposals.append(candidate)
        if len(proposals) == 2:
            break
    return proposals


def timing_plans(plan, diagnostic):
    execution = diagnostic.get('source_execution') or {}
    result = dict(diagnostic=diagnostic, trace=execution.get('trace', []))
    yield from ((p, 'test earlier retreat across independent deployment after observed late arrival')
                for p in retreat_order_proposals(plan, result))
    yield from ((p, 'test shorter strategic retreat wait after observed late arrival')
                for p in retreat_wait_proposals(plan, result))
