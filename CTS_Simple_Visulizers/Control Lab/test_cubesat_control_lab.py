import math
import unittest
import threading
import json
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from http.server import ThreadingHTTPServer
import cubesat_control_lab as lab


class GraphTests(unittest.TestCase):
    def test_autostop_waits_for_motion(self):
        graph = lab.lesson_graph(4)
        for n in graph['nodes']:
            if n['id'] == 'attitude': n['value'] = [1,0,0,0]
        _, _, samples = lab.simulate_batch(graph, {}, .05, 20, auto_stop=True)
        self.assertEqual(len(samples), 20)
        self.assertFalse(samples[-1]['settled'])
        self.assertFalse(samples[-1]['settle_armed'])

    def test_autostop_checks_all_axes_inside_batch(self):
        graph = {'nodes':[
            {'id':'decay','type':'Gain','value':-10},
            {'id':'rate','type':'Integrator','value':[.00002, -.00003, .00004]}],
            'edges':[{'source':'rate','target':'decay','port':0},
                     {'source':'decay','target':'rate','port':0}]}
        state, _, samples = lab.simulate_batch(graph, {}, .05, 20, auto_stop=True)
        self.assertLess(len(samples), 20)
        self.assertTrue(samples[-1]['settled'])
        self.assertTrue(all(abs(x)<1e-5 for x in state['rate']))
        self.assertTrue(any(abs(x)>=1e-5 for x in samples[-2]['values']['rate']))

    def test_speed_batch_matches_individual_steps(self):
        graph = lab.lesson_graph(2)
        expected = {}
        for _ in range(20):
            expected, _ = lab.simulate(graph, expected, .05)
        result, _, samples = lab.simulate_batch(graph, {}, .05, 20)
        self.assertEqual(result, expected)
        self.assertEqual(len(samples), 20)
        self.assertAlmostEqual(samples[-1]['offset'], 1)

    def test_speed_batch_rejects_unbounded_work(self):
        with self.assertRaises(ValueError):
            lab.simulate_batch(lab.lesson_graph(0), {}, .05, 10000)

    def run_model(self, lesson, seconds, mutate=None):
        graph = lab.lesson_graph(lesson)
        if mutate:
            mutate(graph)
        state = {}
        for _ in range(round(seconds / .05)):
            state, values = lab.simulate(graph, state, .05)
        return graph, state, values

    def test_constant_torque_double_integral(self):
        _, state, _ = self.run_model(0, 1)
        self.assertAlmostEqual(state['rate'], .06, places=8)
        self.assertAlmostEqual(state['angle'], .03, places=8)

    def test_proportional_oscillates_and_pd_settles(self):
        _, p, _ = self.run_model(1, 40)
        _, pd, _ = self.run_model(2, 40)
        self.assertLess(abs(pd['angle']), .02)
        self.assertLess(abs(pd['rate']), .003)
        self.assertGreater(abs(p['angle']), abs(pd['angle']) * 3)

    def test_wheel_momentum_conserved(self):
        _, state, _ = self.run_model(3, 8)
        self.assertAlmostEqual(state['momentum'] + lab.J * state['rate'], 0, places=10)

    def test_vector_sun_pointing(self):
        _, state, values = self.run_model(4, 50)
        self.assertAlmostEqual(math.hypot(*state['attitude']), 1, places=10)
        self.assertGreater(values['sun_body'][2], .99)
        self.assertLess(math.hypot(*state['rate']), .01)

    def test_missing_input_rejected(self):
        graph = lab.lesson_graph(0)
        graph['edges'].pop()
        with self.assertRaisesRegex(ValueError, 'input'):
            lab.simulate(graph, {}, .05)

    def test_algebraic_loop_rejected(self):
        graph = {'nodes': [{'id': 'a', 'type': 'Gain', 'value': 1}],
                 'edges': [{'source': 'a', 'target': 'a', 'port': 0}]}
        with self.assertRaisesRegex(ValueError, 'loop'):
            lab.simulate(graph, {}, .05)

    def test_shape_mismatch_rejected(self):
        graph = lab.lesson_graph(0)
        graph['nodes'][0]['value'] = [1, 2, 3]
        with self.assertRaisesRegex(ValueError, 'shape'):
            lab.simulate(graph, {}, .05)

    def test_nan_rejected(self):
        graph = lab.lesson_graph(0)
        graph['nodes'][0]['value'] = float('nan')
        with self.assertRaises(ValueError):
            lab.simulate(graph, {}, .05)

    def test_free_spin_has_no_artificial_braking(self):
        def change(graph):
            for n in graph['nodes']:
                if n['id'] == 'torque': n['value'] = 0
                if n['id'] == 'rate': n['value'] = .1
        _, state, _ = self.run_model(0, 3, change)
        self.assertAlmostEqual(state['rate'], .1)
        self.assertAlmostEqual(state['angle'], .3)

    def test_wire_changes_change_the_physics(self):
        graph = lab.lesson_graph(0)
        # Bypass 1/J. Rate now integrates torque's numerical value directly.
        for e in graph['edges']:
            if e['target'] == 'rate': e['source'] = 'torque'
        state, _ = lab.simulate(graph, {}, .1)
        self.assertAlmostEqual(state['rate'], .00001)

    def test_three_axis_momentum_conservation(self):
        graph = lab.lesson_graph(4)
        state = {'rate': [.08, -.06, .03], 'momentum': [.00002, -.00001, .00003]}
        state, _ = lab.simulate(graph, state, 0)
        def momentum(s):
            body = lab.add(lab.scale(s['rate'], lab.J), s['momentum'])
            return [sum(x*y for x,y in zip(row,body)) for row in lab.rotation(s['attitude'])]
        initial = momentum(state)
        for _ in range(200):
            state, values = lab.simulate(graph, state, .05)
            self.assertLessEqual(max(map(abs, values['limit'])), .0001)
        for a,b in zip(initial,momentum(state)):
            self.assertAlmostEqual(a,b,places=11)

    def test_zero_sun_is_rejected(self):
        graph = lab.lesson_graph(4)
        graph['nodes'][0]['value'] = [0,0,0]
        with self.assertRaisesRegex(ValueError, 'zero vector'):
            lab.simulate(graph, {}, .05)

    def test_duplicate_input_rejected(self):
        graph = lab.lesson_graph(0)
        graph['edges'].append(dict(graph['edges'][0]))
        with self.assertRaisesRegex(ValueError, 'one wire'):
            lab.simulate(graph, {}, .05)


class HTTPTests(unittest.TestCase):
    def test_page_and_simulation_endpoint(self):
        server = ThreadingHTTPServer(('127.0.0.1', 0), lab.Handler)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        base = f'http://127.0.0.1:{server.server_port}'
        try:
            with urlopen(base) as response:
                page = response.read().decode('utf-8')
                self.assertIn('CubeSat Control Lab', page)
                self.assertNotIn('__DATA__', page)
            payload = dict(graph=lab.lesson_graph(0), state={}, dt=.1)
            request = Request(base+'/api/step', data=json.dumps(payload).encode(), headers={'Content-Type':'application/json'})
            with urlopen(request) as response:
                result = json.load(response)
                self.assertAlmostEqual(result['state']['rate'], .006)
            payload['graph']['edges'] = []
            request.data = json.dumps(payload).encode()
            with self.assertRaises(HTTPError) as caught:
                urlopen(request)
            self.assertEqual(caught.exception.code,400)
            caught.exception.close()
        finally:
            server.shutdown()
            server.server_close()
            worker.join()


if __name__ == '__main__':
    unittest.main()
