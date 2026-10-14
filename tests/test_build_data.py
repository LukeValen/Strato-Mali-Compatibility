import importlib.util
from pathlib import Path
import tempfile
import unittest
import json
from unittest.mock import patch
from io import BytesIO
from urllib.parse import parse_qs, urlparse

spec = importlib.util.spec_from_file_location('build_data', Path(__file__).parents[1] / 'scripts' / 'build_data.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

BODY = '''### Jogo

NieR:Automata The End of YoRHa Edition

### Title ID

0100B8E016F76000

### GPU Mali

Mali-G615 MC6

### Driver Vulkan

Arm 44.1.0

### Versão do Strato Mali

0.0.4-2

### Status

Playable

### Nota

0 estrelas

### Observações

Baixo FPS, mas o jogo continua.
'''

def issue(body=BODY, labels=None):
    return {'body': body, 'labels': labels if labels is not None else [{'name': builder.APPROVAL_LABEL}],
            'html_url': 'https://github.com/LukeValen/Strato-Mali-Compatibility/issues/12',
            'created_at': '2026-10-13T10:00:00Z'}

class ReviewTests(unittest.TestCase):
    def test_english_form_and_legacy_portuguese_reports(self):
        english = (BODY.replace('### Jogo', '### Game').replace('### GPU Mali', '### Mali GPU')
                   .replace('### Driver Vulkan', '### Vulkan driver')
                   .replace('### Versão do Strato Mali', '### Strato Mali version')
                   .replace('### Nota', '### Rating').replace('0 estrelas', '5 stars')
                   .replace('### Observações', '### Notes'))
        self.assertEqual(builder.parse_issue(issue(english))['stars'], 5)
        self.assertEqual(builder.parse_issue(issue(BODY))['stars'], 0)

    def test_closed_approved_reports_are_fetched_and_published(self):
        approved = dict(issue(), state='closed')
        with patch.object(builder, 'urlopen', return_value=BytesIO(json.dumps([approved]).encode())) as fetch:
            reports = builder.fetch_approved('test-token')
        query = parse_qs(urlparse(fetch.call_args.args[0].full_url).query)
        self.assertEqual(query['state'], ['all'])
        self.assertEqual(query['labels'], [builder.APPROVAL_LABEL])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'reviews.json'
            builder.build(reports + [dict(issue(labels=[]), state='closed')], path)
            self.assertEqual(len(json.loads(path.read_text())['reviews']), 1)

    def test_zero_stars_and_context(self):
        result = builder.parse_issue(issue())
        self.assertEqual((result['stars'], result['status'], result['gpu']), (0, 'playable', 'Mali-G615 MC6'))

    def test_approval_and_title_id_required(self):
        self.assertIsNone(builder.parse_issue(issue(labels=[])))
        self.assertIsNone(builder.parse_issue(issue(BODY.replace('0100B8E016F76000','incorrect'))))

    def test_static_json_contains_only_approved(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'reviews.json'
            builder.build([issue(), issue(labels=[])], path)
            self.assertEqual(len(json.loads(path.read_text())['reviews']), 1)

if __name__ == '__main__':
    unittest.main()
