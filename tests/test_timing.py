"""Timing hypotheses use observed readiness/lifetimes, not actor or map identities."""
from copy import deepcopy
import unittest
from strategy_workflow.timing import retreat_wait_proposals, retreat_order_proposals


class TimingTests(unittest.TestCase):
    def retreat_fixture(self):
        p=dict(bindings={'role':'unit'},steps=[dict(id='initial',kind='Deploy',task='role'),
            dict(id='retreat',kind='Retreat',task='role',kills=5,pre_frames=60,post_frames=3),
            dict(id='return',kind='Deploy',task='role')])
        r=dict(feasible=False,error=None,trace=[dict(kind='spawn',source_id='unit',step_id='initial',frame=10),
            dict(kind='withdraw',source_id='unit',step_id='retreat',frame=80),
            dict(kind='spawn',source_id='unit',step_id='return',frame=140)],diagnostic=dict(
                tactical_evidence=True,pending_deployment=dict(step_id='return',wait_kind='deployment_unavailable'),
                first_leak=dict(from_frame=100,before=dict(dp=30,cards=[dict(id='unit',cost=20)],characters=[]))))
        return p,r

    def test_late_redeployment_can_shorten_strategic_wait_preserving_actions(self):
        p,r=self.retreat_fixture();original=deepcopy(p);before=deepcopy(r)
        proposals=retreat_wait_proposals(p,r)
        self.assertEqual([c['steps'][1]['pre_frames'] for c in proposals],[30,0])
        for c in proposals:
            self.assertEqual(c['steps'],[p['steps'][0],dict(p['steps'][1],pre_frames=c['steps'][1]['pre_frames']),p['steps'][2]])
        self.assertEqual(p,original);self.assertEqual(r,before)

    def test_retreat_change_rejects_missing_or_contradictory_evidence(self):
        for case in ('partial','won','error','cost','present','wrong_lifetime','no_arrival','interaction','no_wait'):
            p,r=self.retreat_fixture()
            if case=='partial':r['diagnostic']['tactical_evidence']=False
            elif case=='won':r['feasible']=True
            elif case=='error':r['error']={'kind':'transport'}
            elif case=='cost':r['diagnostic']['first_leak']['before']['dp']=19
            elif case=='present':r['diagnostic']['first_leak']['before']['characters']=[dict(source_id='unit',alive=True)]
            elif case=='wrong_lifetime':r['trace'][1]['step_id']='other'
            elif case=='no_arrival':r['trace'].pop()
            elif case=='interaction':p['interaction_policies']=[{}]
            elif case=='no_wait':p['steps'][1]['pre_frames']=0
            self.assertEqual(retreat_wait_proposals(p,r),[],case)

    def test_reorder_preserves_every_action_and_gate_even_without_explicit_wait(self):
        p,r=self.retreat_fixture();p['steps'].insert(1,dict(id='other',kind='Deploy',task='other'))
        p['steps'][2]['pre_frames']=0;before=deepcopy(p)
        proposals=retreat_order_proposals(p,r);self.assertEqual(len(proposals),1)
        self.assertEqual([s['id'] for s in proposals[0]['steps']],['initial','retreat','other','return'])
        self.assertEqual({s['id']:s for s in proposals[0]['steps']},{s['id']:s for s in p['steps']})
        self.assertEqual(p,before)

    def test_reorder_does_not_cross_dependency_or_event_barriers(self):
        for change in ({'kills':2},{'cost_changes':3},{'pre_frames':1},{'cooling_required':0},
                       {'kind':'Skill'},{'task':'role'},{'native_conditions':[{}]}):
            p,r=self.retreat_fixture();p['steps'].insert(1,dict(id='other',kind='Deploy',task='other'))
            p['steps'][1].update(change)
            self.assertEqual(retreat_order_proposals(p,r),[],change)


if __name__=='__main__':unittest.main()
