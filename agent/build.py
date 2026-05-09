import PyInstaller.__main__
import os

script_dir = os.path.dirname(os.path.abspath(__file__))

PyInstaller.__main__.run([
    os.path.join(script_dir, "agent", "__main__.py"),
    "--name=OpenClawCenterAgent",
    "--onefile",
    "--console",
    "--hidden-import=agent",
    "--hidden-import=agent.config",
    "--hidden-import=agent.register",
    "--hidden-import=agent.heartbeat",
    "--hidden-import=agent.collector",
    "--hidden-import=agent.task_runner",
    "--hidden-import=agent.prompt_sync",
    "--hidden-import=agent.logger",
    "--hidden-import=yaml",
    "--hidden-import=psutil",
    f"--distpath={os.path.join(script_dir, 'dist')}",
    f"--workpath={os.path.join(script_dir, 'build')}",
    f"--specpath={script_dir}",
])
