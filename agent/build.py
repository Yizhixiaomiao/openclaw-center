import PyInstaller.__main__
import os

script_dir = os.path.dirname(os.path.abspath(__file__))

PyInstaller.__main__.run([
    os.path.join(script_dir, "agent", "__main__.py"),
    "--name=OpenClawCenterAgent",
    "--onefile",
    "--console",
    "--uac-admin",
    "--hidden-import=agent",
    "--hidden-import=agent.config",
    "--hidden-import=agent.register",
    "--hidden-import=agent.heartbeat",
    "--hidden-import=agent.collector",
    "--hidden-import=agent.task_runner",
    "--hidden-import=agent.prompt_sync",
    "--hidden-import=agent.logger",
    "--hidden-import=agent.service",
    "--hidden-import=agent.updater",
    "--hidden-import=yaml",
    "--hidden-import=psutil",
    f"--distpath={os.path.join(script_dir, 'dist')}",
    f"--workpath={os.path.join(script_dir, 'build')}",
    f"--specpath={script_dir}",
])

# Copy version.txt next to the built exe
dist_dir = os.path.join(script_dir, "dist")
version_src = os.path.join(script_dir, "version.txt")
version_dst = os.path.join(dist_dir, "version.txt")
if os.path.isfile(version_src):
    import shutil
    shutil.copy2(version_src, version_dst)
    print(f"Copied version.txt to {version_dst}")
