import os
import tempfile
import unittest
from unittest.mock import patch

import app as backend
from platform_utils import open_in_file_manager, pick_directory, save_zip_dialog


class AppTests(unittest.TestCase):
    def test_batch_completion_and_download_from_fallback(self):
        with tempfile.TemporaryDirectory() as root:
            primary = os.path.join(root, 'primary')
            fallback = os.path.join(root, 'fallback')
            os.makedirs(primary)
            os.makedirs(fallback)
            calls = []

            def fake_extract(url, output_dir, progress_hook, **kwargs):
                progress_hook({'status': 'converting'})
                self.assertNotEqual(backend.TASKS['test']['status'], 'done')
                path = os.path.join(output_dir, str(len(calls)) + '.mp4')
                with open(path, 'wb') as f:
                    f.write(b'video')
                calls.append(url)
                return [path]

            with patch.dict(os.environ, BILI_AUDIO_DOWNLOAD_DIR=primary), \
                 patch.object(backend, 'is_writable', return_value=False), \
                 patch.object(backend, '_fallback_dir', return_value=fallback), \
                 patch.object(backend, 'extract_audio', side_effect=fake_extract):
                backend._run_task('test', ['https://example.com/1', 'https://example.com/2'], 'mp3', 'video', '', None)
                client = backend.app.test_client()
                task = client.get('/api/task/test').get_json()
                self.assertEqual(task['status'], 'done')
                self.assertEqual(task['count'], 2)
                self.assertNotIn('paths', task)
                response = client.get(task['download_url'])
                self.assertEqual(response.data, b'video')
                response.close()
                self.assertEqual(client.get('/api/task/missing/download').status_code, 404)

    def test_macos_finder_and_dialog_arguments(self):
        with patch('platform_utils.sys.platform', 'darwin'), \
             patch('platform_utils.subprocess.Popen') as popen:
            open_in_file_manager('/tmp/中文 file.mp4', select=True)
            popen.assert_called_once_with(['open', '-R', '/tmp/中文 file.mp4'])
        with patch('platform_utils.sys.platform', 'darwin'), \
             patch('platform_utils.subprocess.run') as run:
            run.return_value.returncode = 0
            run.return_value.stdout = '/tmp/chosen/\n'
            self.assertEqual(pick_directory('/tmp/a"b'), '/tmp/chosen/')
            self.assertEqual(run.call_args.args[0][-1], '/tmp/a"b')
            save_zip_dialog('中文.zip', '/tmp')
            self.assertEqual(run.call_args.args[0][-2:], ['中文.zip', '/tmp'])
            run.return_value.stdout = '\n'
            self.assertIsNone(pick_directory('/tmp'))


if __name__ == '__main__':
    unittest.main()
