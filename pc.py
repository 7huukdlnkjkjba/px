import subprocess, os
os.makedirs('videos', exist_ok=True)
vid = input("ID: ").strip()
subprocess.run([
    'yt-dlp',
    '-P', 'videos',
    '--cookies-from-browser', 'chrome',
    '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    '--add-header', 'Referer: https://hanime1.com/',
    '--no-check-certificate',
    f'https://hanime1.com/watch?v={vid}'
])