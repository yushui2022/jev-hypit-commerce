import json,tempfile,unittest
from pathlib import Path
from render import prepare
from analyze import extract_json
class IntegrationBoundaryTest(unittest.TestCase):
    def test_missing_asset_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'story.json';source.write_text(json.dumps({'pairs':[{'product':{'image':'missing.png'},'avatar':{'image':'also-missing.png'}}]}))
            with self.assertRaisesRegex(ValueError,'Missing product'):prepare(source,Path(d)/'out','example.com')
    def test_portable_demo_prepares_pair_references(self):
        source=Path(__file__).resolve().parents[1]/'examples/storyboard.json'
        with tempfile.TemporaryDirectory() as d:
            run=prepare(source,d,'example.com/?a=1&b=2');xml=(run.parent/'main.svml').read_text()
            self.assertIn('product-image={product0}',xml);self.assertIn('a=1&amp;b=2',xml)
            self.assertEqual(len(list((run.parent/'images').iterdir())),6)
    def test_fenced_vision_response(self):
        response={'candidates':[{'content':{'parts':[{'text':'```json\n{"visual_features":"green bottle"}\n```'}]}}]}
        self.assertEqual(extract_json(response),'green bottle')
    def test_malformed_vision_response_rejected(self):
        with self.assertRaises(ValueError):extract_json({'candidates':[{'content':{'parts':[{'text':'{"visual_features": null}'}]}}]})
