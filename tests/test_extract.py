import os
import unittest
from unittest.mock import patch

import yt_dlp

import extract


class NetworkTests(unittest.TestCase):
    def test_bili_bypasses_automatic_proxy_but_respects_explicit_proxy(self):
        with patch.dict(os.environ, {}, clear=True), \
             patch.object(extract, 'detect_proxy', return_value='http://auto:7897'):
            for host in ('www.bilibili.com', 'bilibili.com', 'b23.tv'):
                self.assertEqual(extract._network_options('https://' + host)['proxy'], '')
            self.assertEqual(extract._network_options('https://example.com')['proxy'], 'http://auto:7897')
            self.assertEqual(extract._network_options('https://bilibili.com.evil.test')['proxy'], 'http://auto:7897')
            self.assertEqual(extract._network_options('https://b23.tv', 'http://manual:80')['proxy'], 'http://manual:80')
            self.assertEqual(extract._network_options('https://example.com', '')['proxy'], '')
            with patch.dict(os.environ, BILI_AUDIO_PROXY='http://override:80'):
                self.assertEqual(extract._network_options('https://b23.tv')['proxy'], 'http://override:80')

    def test_timeout_is_retried_for_preview_and_download(self):
        for download in (False, True):
            with self.subTest(download=download), \
                 patch.object(extract.yt_dlp, 'YoutubeDL') as factory, \
                 patch.object(extract.time, 'sleep'):
                ydl = factory.return_value.__enter__.return_value
                ydl.extract_info.side_effect = [
                    yt_dlp.utils.DownloadError('Unable to download webpage: The read operation timed out'),
                    {'id': 'ok'},
                ]
                self.assertEqual(extract._extract_with_retries('https://example.com', {}, download), {'id': 'ok'})
                self.assertEqual(ydl.extract_info.call_count, 2)
                ydl.extract_info.assert_called_with('https://example.com', download=download)

    def test_retries_are_bounded_and_non_network_errors_fail_immediately(self):
        for message, count in [('The read operation timed out', 3), ('Video requires login', 1), ('Permission denied', 1)]:
            with self.subTest(message=message), \
                 patch.object(extract.yt_dlp, 'YoutubeDL') as factory, \
                 patch.object(extract.time, 'sleep'):
                ydl = factory.return_value.__enter__.return_value
                ydl.extract_info.side_effect = yt_dlp.utils.DownloadError(message)
                with self.assertRaises(yt_dlp.utils.DownloadError) as caught:
                    extract._extract_with_retries('https://example.com', {}, False)
                self.assertEqual(ydl.extract_info.call_count, count)
                if count == 3:
                    self.assertIn('重试 2 次后仍失败', str(caught.exception))

    def test_preview_and_download_use_shared_network_options(self):
        with patch.dict(os.environ, {}, clear=True), \
             patch.object(extract, '_extract_with_retries', return_value=None) as run, \
             patch.object(extract, 'resolve_ffmpeg_path', return_value=None):
            for action in (extract.fetch_info, extract.extract_audio):
                with self.assertRaises(yt_dlp.utils.DownloadError):
                    action('https://www.bilibili.com/video/BV1MFss62EcG')
                opts = run.call_args.args[1]
                self.assertEqual(opts['proxy'], '')
                self.assertEqual(opts['socket_timeout'], 30)


if __name__ == '__main__':
    unittest.main()
